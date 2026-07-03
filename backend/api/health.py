import time
from fastapi import APIRouter
from loguru import logger
from backend.config import settings

# Unified Router Instantiation
router = APIRouter()

@router.get("/", tags=["System Gateway"])
async def root_gateway():
    """
    Primary API Root Entry Point.
    Provides standard welcome metadata, application versions, and core interface paths.
    """
    logger.info("System root welcome gateway requested.")
    return {
        "message": f"Welcome to the {settings.APP_NAME} REST API Engine.",
        "status": "online",
        "version": settings.APP_VERSION,
        "documentation": "/docs"
    }

@router.get("/api/v1/health", tags=["System Diagnostics"])
async def system_health_check():
    """
    Versioned Infrastructure Health Monitoring Endpoint.
    Returns fundamental service status profiles, current runtime epochs, and environmental flags.
    """
    logger.info("API Version 1 diagnostics check requested by client pipeline.")
    return {
        "status": "healthy",
        "environment": "development" if settings.DEBUG else "production",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }
