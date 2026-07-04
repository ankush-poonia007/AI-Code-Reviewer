import time
from fastapi import APIRouter
from loguru import logger
from backend.config import settings
from backend.database.database import probe_connection

router = APIRouter()

@router.get("/health", tags=["System Status"])
async def system_health_check():
    """
    Infrastructure Health Monitoring Endpoint.
    Returns general runtime statuses and environment parameters.
    """
    logger.info("API diagnostics request intercepted at version 1 checkpoint.")

    if probe_connection():
        db_status = "healthy"
    else:
        db_status = "unhealthy"
        logger.error("Health check database probe failed.")

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "environment": "development" if settings.DEBUG else "production",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "database": db_status,
        "timestamp": time.time()
    }
