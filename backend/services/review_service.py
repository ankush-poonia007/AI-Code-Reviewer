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
from backend.schemas.review_result import ParsedReviewResult


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

        # Commit PENDING record before the LLM call to avoid holding SQLite locks during network I/O
        self.db.commit()
        
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
