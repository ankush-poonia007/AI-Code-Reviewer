from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.exc import SQLAlchemyError

from backend.providers.exceptions import (
    LLMProviderError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMProviderUnavailableError,
    ResponseParsingError,
)
from backend.services.exceptions import ReviewNotFoundError, ExecutionNotFoundError

# API infrastructure logging proxy binding
api_logger = logger.bind(component="api", system="exceptions")


# =====================================================================
# 1️⃣ Standardized API Error Response Schema (Pydantic Model)
# =====================================================================
class APIErrorResponse(BaseModel):
    """
    Symmetrical public API schema defining error output payloads.
    Guarantees formatting consistency across all centralized exception endpoints.
    """
    model_config = ConfigDict(extra="forbid")

    error: str = Field(description="A clear, high-level structural categorization token of the error.")
    detail: str = Field(description="A user-friendly, actionable explanation message of what went wrong.")


# =====================================================================
# 2️⃣ Global Exception Registration Matrix Handler
# =====================================================================
def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handler intercepts across the FastAPI engine app instance.
    Translates incoming domain and persistence exceptions safely into the public error contract.
    Enforces ADR-046 by completely removing infrastructure-specific text from public responses.
    """

    @app.exception_handler(LLMAuthenticationError)
    async def authentication_exception_handler(request: Request, exc: LLMAuthenticationError) -> JSONResponse:
        api_logger.exception("Unauthorized client intercept: Invalid provider credentials matching target configuration loop.")
        response_payload = APIErrorResponse(
            error="Authentication Failure",
            detail="The server encountered an error authenticating with the AI model provider infrastructure backend."
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=response_payload.model_dump()
        )

    @app.exception_handler(LLMRateLimitError)
    async def ratelimit_exception_handler(request: Request, exc: LLMRateLimitError) -> JSONResponse:
        api_logger.exception("Throughput quota limit exhausted intercept: Throttling endpoint hit.")
        response_payload = APIErrorResponse(
            error="Rate Limit Exceeded",
            detail="AI model engine maximum request throughput capacity or key quotas are currently fully exhausted."
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=response_payload.model_dump()
        )

    @app.exception_handler(LLMTimeoutError)
    async def timeout_exception_handler(request: Request, exc: LLMTimeoutError) -> JSONResponse:
        api_logger.exception("Gateway connection timeout intercept: Network latency boundary reached with vendor server.")
        response_payload = APIErrorResponse(
            error="Provider Timeout",
            detail="The upstream AI model infrastructure failed to generate an analysis response within the latency limits."
        )
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=response_payload.model_dump()
        )

    @app.exception_handler(LLMProviderUnavailableError)
    async def provider_unavailable_exception_handler(request: Request, exc: LLMProviderUnavailableError) -> JSONResponse:
        api_logger.exception("Upstream infrastructure out-of-order intercept: Remote platform service unavailable.")
        response_payload = APIErrorResponse(
            error="Provider Unavailable",
            detail="The third-party model inference server platform is currently unreachable, down, or under active maintenance."
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_payload.model_dump()
        )

    @app.exception_handler(ResponseParsingError)
    async def parsing_exception_handler(request: Request, exc: ResponseParsingError) -> JSONResponse:
        api_logger.exception("Trust boundary schema validation crash intercept: AI payload failed layout rules.")
        response_payload = APIErrorResponse(
            error="Response Formatting Failure",
            detail="The AI engine responded, but its output data format failed trust boundary verification rules."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_payload.model_dump()
        )

    @app.exception_handler(LLMProviderError)
    async def generic_provider_exception_handler(request: Request, exc: LLMProviderError) -> JSONResponse:
        api_logger.exception("Unclassified ecosystem infrastructure intercept: Runtime engine error.")
        # Refinement: Fully isolates raw text string messages from spilling across network boundaries
        response_payload = APIErrorResponse(
            error="AI Engine Operational Error",
            detail="The AI provider encountered an unexpected internal error while running code review computations."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_payload.model_dump()
        )

    @app.exception_handler(ReviewNotFoundError)
    async def review_not_found_exception_handler(request: Request, exc: ReviewNotFoundError) -> JSONResponse:
        api_logger.warning(f"Review not found: {exc.review_id}")
        response_payload = APIErrorResponse(
            error="Review Not Found",
            detail=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response_payload.model_dump()
        )

    @app.exception_handler(ExecutionNotFoundError)
    async def execution_not_found_exception_handler(request: Request, exc: ExecutionNotFoundError) -> JSONResponse:
        api_logger.warning(f"Execution telemetry not found: {exc.review_id}")
        response_payload = APIErrorResponse(
            error="Execution Telemetry Not Found",
            detail=str(exc)
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=response_payload.model_dump()
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        api_logger.exception("Persistence transaction abort intercept: Relational storage engine crash.")
        response_payload = APIErrorResponse(
            error="Storage Engine Error",
            detail="A critical relational tracking error occurred while trying to commit the review records to disk storage."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_payload.model_dump()
        )

    @app.exception_handler(Exception)
    async def universal_fallback_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        api_logger.exception("Unhandled catastrophic system crash intercept: Root exception loop fired.")
        response_payload = APIErrorResponse(
            error="Internal System Server Error",
            detail="An unhandled, catastrophic core system exception occurred inside the application backend lifecycle."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_payload.model_dump()
        )
