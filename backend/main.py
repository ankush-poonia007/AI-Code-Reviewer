from fastapi import FastAPI
from loguru import logger
from backend.utils import setup_logging
from backend.config import settings
from backend.api.health import router as health_router

# =====================================================================
# Centralized System Diagnostics Logging Initialization
# =====================================================================
setup_logging()
logger.info(f"Booting up {settings.APP_NAME} Framework (v{settings.APP_VERSION})...")

# =====================================================================
# Application Core Instantiation & Production Metadata
# =====================================================================
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "An automated code analysis engine designed to evaluate source files, "
        "detect bugs, assess security risks, and generate comprehensive quality scores "
        "via Large Language Models."
    ),
    version=settings.APP_VERSION
)

# =====================================================================
# Router Registration Layer
# =====================================================================
# Attaches feature-based layout routing modules safely to the core engine instance
app.include_router(health_router)

logger.success("FastAPI routers successfully mounted. Application ready.")
