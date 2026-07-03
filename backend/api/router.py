from fastapi import APIRouter
from backend.api.v1.review import router as review_router

# The absolute single gateway point for all current and future versioned APIs (ADR-047)
api_router = APIRouter()

# Nest the feature controller inside the versioned /v1 prefix namespace
api_router.include_router(review_router, prefix="/v1")
