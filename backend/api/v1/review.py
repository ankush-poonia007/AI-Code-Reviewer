from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException, Query, Path
from loguru import logger

from backend.config import settings
from backend.constants import validate_language, validate_safe_filename
from backend.schemas.review_request import ReviewRequest
from backend.schemas.review_response import (
    ReviewResponse,
    ReviewSummaryResponse,
    ReviewDetailResponse,
    ExecutionResponse,
    DashboardResponse,
    ModelInfoResponse,
)
from backend.schemas.review_result import ParsedIssue
from backend.models.enums import ReviewStatusEnum
from backend.api.dependencies import get_review_service
from backend.services.review_service import ReviewService

router = APIRouter(tags=["Code Review Engine"])

# =====================================================================
# 1️⃣ Route A: Programmatic JSON Payload Endpoint (Code Snippets / UI)
# =====================================================================
@router.post(
    "/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a code text snippet asset for automated AI review analysis"
)
async def submit_code_review(
    payload: ReviewRequest,
    review_service: ReviewService = Depends(get_review_service)
) -> ReviewResponse:
    """
    Exposes the versioned POST /api/v1/review controller gateway.
    Accepts an explicit raw JSON body structure containing file metadata and source strings.
    """
    logger.info(f"API Gate intercept [JSON]: Submitting code analysis for file '{payload.filename}'")

    # Dispatch parameters straight down to the injected workflow orchestrator
    review_id, parsed_result = await review_service.review_code(
        filename=payload.filename,
        language=payload.language,
        source_code=payload.source_code
    )

    # Map across the API response schema boundary (ADR-039)
    return ReviewResponse(
        review_id=review_id,
        status=ReviewStatusEnum.COMPLETED.value,
        overall_score=parsed_result.overall_score,
        executive_summary=parsed_result.executive_summary,
        issues=parsed_result.issues
    )


# =====================================================================
# 2️⃣ Route B: Multipart Form Binary File Upload Endpoint (Swagger / CLI)
# =====================================================================
@router.post(
    "/review/file",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a physical binary file asset for automated AI review analysis"
)
async def upload_file_review(
    language: str = Form(..., description="The programming language profile key string (e.g., 'python')."),
    file: UploadFile = File(..., description="The physical code asset file to stream and evaluate."),
    review_service: ReviewService = Depends(get_review_service)
) -> ReviewResponse:
    """
    Exposes the versioned POST /api/v1/review/file controller gateway.
    Accepts a multipart form parameter payload, parsing the binary file data stream natively in memory.
    """
    logger.info(f"API Gate intercept [Multipart]: Uploading file analysis for target language '{language}'")

    try:
        validated_language = validate_language(language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # 1. Defensively extract filename and decode binary file stream data into a clean string string
    filename = file.filename if file.filename else "uploaded_asset.txt"
    try:
        filename = validate_safe_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    file_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
        )
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty. Please upload a non-empty source file."
        )
    try:
        source_code = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not valid UTF-8 text. Please upload a plain-text source file."
        )

    # 2. Dispatch extracted parameters straight down to the same injected workflow orchestrator
    review_id, parsed_result = await review_service.review_code(
        filename=filename,
        language=validated_language,
        source_code=source_code
    )

    # 3. Map across the API response schema boundary (ADR-039)
    return ReviewResponse(
        review_id=review_id,
        status=ReviewStatusEnum.COMPLETED.value,
        overall_score=parsed_result.overall_score,
        executive_summary=parsed_result.executive_summary,
        issues=parsed_result.issues
    )


# =====================================================================
# 3️⃣ Remaining Production REST API Management & Stats Endpoints
# =====================================================================
@router.get(
    "/reviews",
    response_model=List[ReviewSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all historical code reviews"
)
async def list_reviews(
    skip: int = Query(0, ge=0, description="Number of reviews to skip for pagination."),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of reviews to return."),
    review_service: ReviewService = Depends(get_review_service)
) -> List[ReviewSummaryResponse]:
    """
    Returns a paginated list of historical code review summaries, ordered newest first.
    Lightweight summary objects exclude executive summary text, issues, and execution metadata.
    """
    logger.info(f"API Gate intercept: Fetching paginated reviews (skip={skip}, limit={limit})")
    return await review_service.list_reviews(skip=skip, limit=limit)


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete code review details"
)
async def get_review(
    review_id: UUID = Path(..., description="The unique 36-character UUID string identifier of the review."),
    review_service: ReviewService = Depends(get_review_service)
) -> ReviewDetailResponse:
    """
    Returns a complete detailed review report including issues and LLM provider execution telemetry.
    Raises 404 if the review does not exist.
    """
    logger.info(f"API Gate intercept: Fetching complete review for ID: {review_id}")
    return await review_service.get_review(review_id)


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a code review record"
)
async def delete_review(
    review_id: UUID = Path(..., description="The unique 36-character UUID string identifier of the review."),
    review_service: ReviewService = Depends(get_review_service)
) -> None:
    """
    Permanently deletes a code review record and automatically cascade deletes all associated issues and execution metadata.
    Returns 204 No Content on success. Raises 404 if the review is missing.
    """
    logger.info(f"API Gate intercept: Requesting deletion of review ID: {review_id}")
    await review_service.delete_review(review_id)


@router.get(
    "/reviews/{review_id}/issues",
    response_model=List[ParsedIssue],
    status_code=status.HTTP_200_OK,
    summary="Get issues list for a code review"
)
async def get_review_issues(
    review_id: UUID = Path(..., description="The unique 36-character UUID string identifier of the review."),
    review_service: ReviewService = Depends(get_review_service)
) -> List[ParsedIssue]:
    """
    Returns the collection of granular issues identified during a specific code review.
    Returns an empty array `[]` if no issues exist. Raises 404 if the review record is missing.
    """
    logger.info(f"API Gate intercept: Fetching issues for review ID: {review_id}")
    return await review_service.get_review_issues(review_id)


@router.get(
    "/reviews/{review_id}/execution",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get execution metadata for a code review"
)
async def get_review_execution(
    review_id: UUID = Path(..., description="The unique 36-character UUID string identifier of the review."),
    review_service: ReviewService = Depends(get_review_service)
) -> ExecutionResponse:
    """
    Returns the operational telemetry metadata recorded during the LLM provider call for a specific review.
    Raises 404 if either the review is missing or the execution telemetry is missing.
    """
    logger.info(f"API Gate intercept: Fetching execution metadata for review ID: {review_id}")
    return await review_service.get_review_execution(review_id)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get code review dashboard statistics"
)
async def get_dashboard_stats(
    review_service: ReviewService = Depends(get_review_service)
) -> DashboardResponse:
    """
    Returns aggregated metrics for dashboard visualization, including total counts, averages, and severity distributions.
    """
    logger.info("API Gate intercept: Requesting dashboard statistics aggregation.")
    return await review_service.dashboard_statistics()


@router.get(
    "/models",
    response_model=ModelInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active LLM settings configuration"
)
async def get_model_info(
    review_service: ReviewService = Depends(get_review_service)
) -> ModelInfoResponse:
    """
    Exposes configured LLM settings including default model name, temperature, max tokens, and active provider target.
    """
    logger.info("API Gate intercept: Requesting active LLM settings configuration.")
    return await review_service.get_model_information()

