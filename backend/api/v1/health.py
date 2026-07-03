import time
from fastapi import APIRouter
from loguru import logger
from backend.config import settings

router = APIRouter()

@router.get("/health", tags=["System Status"])
async def system_health_check():
    """
    Infrastructure Health Monitoring Endpoint.
    Returns general runtime statuses and environment parameters.
    """
    logger.info("API diagnostics request intercepted at version 1 checkpoint.")
    return {
        "status": "healthy",
        "environment": "development" if settings.DEBUG else "production",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }
