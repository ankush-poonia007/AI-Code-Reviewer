import time
import traceback
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger

from backend.config import settings
from backend.constants import SupportedLanguage, validate_language
from backend.models.review import Review
from backend.models.issue import Issue
from backend.models.review_execution import ReviewExecution
from backend.models.enums import ReviewStatusEnum

from backend.database.repositories import ReviewRepository, IssueRepository, ExecutionRepository
from backend.providers.base_provider import LLMProvider
from backend.providers.response_models import LLMResponse
from backend.providers.response_parser import ResponseParser
from backend.prompts.review_prompt import ReviewPromptBuilder
from backend.schemas.review_result import ParsedReviewResult, ParsedIssue
from backend.schemas.review_response import (
    ReviewSummaryResponse,
    ExecutionResponse,
    ReviewDetailResponse,
    DashboardResponse,
    ModelInfoResponse,
)
from backend.services.exceptions import ReviewNotFoundError, ExecutionNotFoundError


class ReviewService:
    """
    Core workflow orchestrator brain of the application enforcing ADR-028, ADR-029, ADR-033, and ADR-038.
    Coordinates stateless prompt templates, AI provider networks, and persistent transaction loops.
    """

    def __init__(
        self,
        db: Session,
        review_repo: ReviewRepository,
        issue_repo: IssueRepository,
        execution_repo: ExecutionRepository,
        llm_provider: LLMProvider,
        response_parser: type[ResponseParser] = ResponseParser,
        prompt_builder: type[ReviewPromptBuilder] = ReviewPromptBuilder
    ) -> None:
        """Initializes the service with completely injected dependencies adhering to ADR-029."""
        self.db = db
        self.review_repo = review_repo
        self.issue_repo = issue_repo
        self.execution_repo = execution_repo
        self.llm_provider = llm_provider
        self.response_parser = response_parser
        self.prompt_builder = prompt_builder
        self._logger = logger.bind(component="review_service")

    async def review_code(self, filename: str, language: str, source_code: str) -> tuple[str, ParsedReviewResult]:
        """
        Primary public method orchestrating the end-to-end AI code review pipeline.
        Maintains an atomic transaction checkpoint, ensuring full rollback or audited status tracking.

        Returns:
            A tuple of (review_id, parsed_result) for the completed review transaction.
        """
        self._logger.info(f"Initiating code review transaction block for file: {filename}")
        
        # Start performance clock benchmarks
        start_time = time.perf_counter()
        
        # Step 1: Establish an early database footprint before entering network loops
        review_record = self._create_review(filename=filename, language=language)
        review_uuid = UUID(review_record.id)
        
        try:
            # Step 2: Build the decoupled static/dynamic instruction block prompt (ADR-030)
            final_prompt = self._build_prompt(filename=filename, language=language, source_code=source_code)

            # Step 3: Dispatch non-blocking prompt data down to the abstracted provider adapter layer
            llm_transport_payload = await self._invoke_provider(final_prompt)
            
            # Step 4: Route unstructured responses through the trust boundary validation parser (ADR-027)
            parsed_result = self._parse_response(llm_transport_payload.content)

            # Stop performance clock benchmarks
            end_time = time.perf_counter()
            duration_ms = int((end_time - start_time) * 1000)

            # Step 5: Map schemas to domain ORM models (ADR-038: Caller persists mapping output)
            self._finalize_successful_review(review_record, parsed_result, duration_ms)
            
            db_issues = self._map_issue_entities(review_uuid, parsed_result)
            self.issue_repo.create_many(db_issues)
            
            db_execution = self._map_execution_telemetry(review_uuid, llm_transport_payload, duration_ms)
            self.execution_repo.create(db_execution)

            # Step 6: Atomic Commit Step across all relational tables
            self.db.commit()
            
            self._logger.success(f"Code review transaction block completed and saved to disk for {filename}.")

            return str(review_record.id), parsed_result

        except Exception as e:
            # Boundary Interceptor: Rollback any partially flushed transaction steps cleanly
            self._logger.error(f"Pipeline failure encountered. Initiating rollback and updating audit trail: {str(e)}")
            self.db.rollback()
            
            # Audited Failure Recovery Layer: Persist a FAILED state via isolated audit transaction
            self._finalize_failed_review(review_record, e)
                
            # Pure raise statement preserves original traceback history cleanly for debugging
            raise

    # =====================================================================
    # Private Layer Helper Methods (Steps 1-4 Workflow Implementation)
    # =====================================================================
    def _create_review(self, filename: str, language: str) -> Review:
        """Instantiates an early tracking record row inside database memory with PENDING status."""
        normalized_language = validate_language(language)
        review_entity = Review(
            filename=filename,
            language=SupportedLanguage(normalized_language),
            executive_summary="Initializing code analysis workflow...",
            status=ReviewStatusEnum.PENDING,
            review_duration_ms=0
        )
        return self.review_repo.create(review_entity)

    def _build_prompt(self, filename: str, language: str, source_code: str) -> str:
        """Delegates prompt creation entirely to the ReviewPromptBuilder class module."""
        return self.prompt_builder.build_review_prompt(
            filename=filename,
            language=language,
            source_code=source_code
        )

    async def _invoke_provider(self, prompt: str) -> LLMResponse:
        """Dispatches non-blocking raw text prompt data directly down to the injected LLMProvider client."""
        return await self.llm_provider.generate_review(prompt)

    def _parse_response(self, content: str) -> ParsedReviewResult:
        """Extracts and validates incoming text using the response parser trust boundary engine."""
        return self.response_parser.parse_review_response(content)

    # =====================================================================
    # Private Layer Helper Methods (Pure Mapping and Transitions: ADR-038)
    # =====================================================================
    def _map_issue_entities(self, review_id: UUID, parsed_result: ParsedReviewResult) -> list[Issue]:
        """
        Maps validated Pydantic business schemas into database ORM models.
        Enforces ADR-038 by keeping object mapping separate from repository calls.
        """
        review_id_str = str(review_id)
        return [
            Issue(
                review_id=review_id_str,
                category=issue.category,
                issue_type=issue.issue_type,
                severity=issue.severity,
                title=issue.title,
                description=issue.description,
                recommendation=issue.recommendation,
                code_snippet=issue.code_snippet,
                line_number=issue.line_number,
                confidence=issue.confidence
            )
            for issue in parsed_result.issues
        ]

    def _map_execution_telemetry(self, review_id: UUID, llm_payload: LLMResponse, duration_ms: int) -> ReviewExecution:
        """
        Maps operational runtime metrics and telemetry payload parameters to the ORM schema.
        Enforces ADR-038 by keeping metadata mapping decoupled from persistence.
        """
        return ReviewExecution(
            review_id=str(review_id),
            provider=self.llm_provider.provider_name,
            model_name=llm_payload.model_name,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            processing_time_ms=duration_ms,
            prompt_version=self.prompt_builder.PROMPT_VERSION,
            input_tokens=llm_payload.usage.input_tokens,
            output_tokens=llm_payload.usage.output_tokens,
            total_tokens=llm_payload.usage.total_tokens
        )

    def _finalize_successful_review(self, review_record: Review, parsed_result: ParsedReviewResult, duration_ms: int) -> None:
        """Updates the pre-allocated parent model state row with successful parsing properties."""
        review_record.executive_summary = parsed_result.executive_summary
        review_record.overall_score = parsed_result.overall_score
        review_record.status = ReviewStatusEnum.COMPLETED
        review_record.review_duration_ms = duration_ms
        self.review_repo.update(review_record)

    def _finalize_failed_review(self, review_record: Review, exception: Exception) -> None:
        """
        Persists a FAILED audit record in an isolated transaction after the main
        workflow transaction has been rolled back, preserving atomic boundaries.
        """
        review_id = review_record.id
        try:
            failed_review = Review(
                id=review_id,
                filename=review_record.filename,
                language=review_record.language,
                executive_summary=(
                    "Code analysis failed due to an underlying execution error. "
                    "Please check infrastructure logs for diagnostic details."
                ),
                status=ReviewStatusEnum.FAILED,
                review_duration_ms=0,
                overall_score=0.00,
            )
            ReviewRepository.persist_in_isolated_transaction(failed_review)

            stack_trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
            self._logger.warning(f"Audit log updated to FAILED state for review: {review_id}\nInternal Trace:\n{stack_trace}")

        except Exception as audit_err:
            self._logger.critical(f"Critical System Failure: Could not commit failure status to database: {str(audit_err)}")

    async def list_reviews(self, skip: int = 0, limit: int = 10) -> list[ReviewSummaryResponse]:
        """
        Retrieves a paginated list of reviews translated into lightweight summary responses.
        """
        self._logger.info(f"Listing paginated reviews: skip={skip}, limit={limit}")
        reviews = self.review_repo.list_all(skip=skip, limit=limit)
        return [
            ReviewSummaryResponse(
                review_id=review.id,
                filename=review.filename,
                language=review.language.value if hasattr(review.language, 'value') else str(review.language),
                status=review.status.value if hasattr(review.status, 'value') else str(review.status),
                overall_score=float(review.overall_score),
                created_at=review.created_at,
                issue_count=len(review.issues)
            )
            for review in reviews
        ]

    async def get_review(self, review_id: UUID) -> ReviewDetailResponse:
        """
        Retrieves a complete, detailed code review report, including issues and telemetry execution mapping.
        """
        self._logger.info(f"Fetching detailed review for ID: {review_id}")
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError(str(review_id))

        execution_dto = None
        if review.execution:
            exec_model = review.execution
            execution_dto = ExecutionResponse(
                provider=exec_model.provider,
                model_name=exec_model.model_name,
                temperature=exec_model.temperature,
                max_tokens=exec_model.max_tokens,
                processing_time_ms=exec_model.processing_time_ms,
                prompt_version=exec_model.prompt_version,
                input_tokens=exec_model.input_tokens,
                output_tokens=exec_model.output_tokens,
                total_tokens=exec_model.total_tokens
            )

        issues_list = [
            ParsedIssue(
                category=issue.category.value if hasattr(issue.category, 'value') else str(issue.category),
                issue_type=issue.issue_type,
                severity=issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                title=issue.title,
                description=issue.description,
                recommendation=issue.recommendation,
                code_snippet=issue.code_snippet,
                line_number=issue.line_number,
                confidence=issue.confidence
            )
            for issue in review.issues
        ]

        return ReviewDetailResponse(
            review_id=review.id,
            filename=review.filename,
            language=review.language.value if hasattr(review.language, 'value') else str(review.language),
            status=review.status.value if hasattr(review.status, 'value') else str(review.status),
            overall_score=float(review.overall_score),
            executive_summary=review.executive_summary,
            review_duration_ms=review.review_duration_ms,
            created_at=review.created_at,
            updated_at=review.updated_at,
            issues=issues_list,
            execution=execution_dto
        )

    async def delete_review(self, review_id: UUID) -> None:
        """
        Removes a review record from relational storage. Cascades deletion to issues and telemetry.
        """
        self._logger.info(f"Deleting review with ID: {review_id}")
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError(str(review_id))

        self.review_repo.delete(review_id)
        self.db.commit()
        self._logger.success(f"Review {review_id} and cascade dependencies deleted.")

    async def get_review_issues(self, review_id: UUID) -> list[ParsedIssue]:
        """
        Retrieves all issues associated with a specific review ID.
        """
        self._logger.info(f"Listing issues for review ID: {review_id}")
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError(str(review_id))

        issues = self.issue_repo.get_by_review_id(review_id)
        return [
            ParsedIssue(
                category=issue.category.value if hasattr(issue.category, 'value') else str(issue.category),
                issue_type=issue.issue_type,
                severity=issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                title=issue.title,
                description=issue.description,
                recommendation=issue.recommendation,
                code_snippet=issue.code_snippet,
                line_number=issue.line_number,
                confidence=issue.confidence
            )
            for issue in issues
        ]

    async def get_review_execution(self, review_id: UUID) -> ExecutionResponse:
        """
        Retrieves LLM execution metadata and metrics for a specific review.
        """
        self._logger.info(f"Fetching execution telemetry for review ID: {review_id}")
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFoundError(str(review_id))

        execution = self.execution_repo.get_by_review_id(review_id)
        if not execution:
            raise ExecutionNotFoundError(str(review_id))

        return ExecutionResponse(
            provider=execution.provider,
            model_name=execution.model_name,
            temperature=execution.temperature,
            max_tokens=execution.max_tokens,
            processing_time_ms=execution.processing_time_ms,
            prompt_version=execution.prompt_version,
            input_tokens=execution.input_tokens,
            output_tokens=execution.output_tokens,
            total_tokens=execution.total_tokens
        )

    async def dashboard_statistics(self) -> DashboardResponse:
        """
        Calculates and returns aggregated dashboard statistics.
        """
        self._logger.info("Aggregating dashboard statistics DTO.")
        review_stats = self.review_repo.get_dashboard_stats()
        issue_stats = self.issue_repo.get_severity_counts()
        return DashboardResponse(**review_stats, **issue_stats)

    async def get_model_information(self) -> ModelInfoResponse:
        """
        Exposes configured LLM settings.
        """
        self._logger.info("Fetching LLM settings config.")
        provider = settings.LLM_PROVIDER
        model = settings.GROQ_MODEL if provider == "groq" else settings.GEMINI_MODEL
        return ModelInfoResponse(
            provider=provider,
            model=model,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )

