from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from loguru import logger

from backend.config import settings
from backend.constants import validate_language, validate_safe_filename
from backend.schemas.review_request import ReviewRequest
from backend.schemas.review_response import ReviewResponse
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
