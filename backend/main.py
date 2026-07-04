from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import settings
from backend.utils.logger import setup_logging
from backend.database.init_db import initialize_database
from backend.database.database import engine
from backend.api.exceptions import setup_exception_handlers
from backend.api.v1.health import router as health_router
from backend.api.router import api_router
from backend.providers.provider_factory import ProviderFactory


# =====================================================================
# 1️⃣ Application Lifecycle Lifespan Manager (ADR-048 Context Boundary)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages non-blocking startup and shutdown hooks for the application instance.
    Enforces ADR-048 by delaying database schema footprint creation until server boot.
    """
    logger.info("Server lifecycles initializing: Executing startup hooks...")
    try:
        settings.verify_active_credentials()
        logger.success("Active LLM provider credentials verified.")
        ProviderFactory.get_provider()
        logger.success(f"Active LLM provider '{settings.LLM_PROVIDER}' initialized successfully.")
        # Automate database schema footprint checks cleanly on actual server boot
        initialize_database()
        logger.success("Application database bootstrap hook completed successfully.")
    except Exception as e:
        logger.critical(f"Server lifespan startup hook failed catastrophically: {str(e)}")
        raise e

    yield  # Hand over operational control matrix to the Uvicorn worker thread pipeline

    logger.info("Server lifecycles terminating: Executing shutdown hooks cleanups...")
    engine.dispose()
    logger.success("Database engine connections disposed cleanly.")


# =====================================================================
# 2️⃣ Application Core Bootstrap Setup Configuration
# =====================================================================
# Initialize the logging framework sink configurations instantly
setup_logging()
logger.info(f"Assembling {settings.APP_NAME} Configuration Schemas (v{settings.APP_VERSION})...")

# Construct the central FastAPI instance bound directly to our clean lifespan manager
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade AI-powered asynchronous code analysis, quality metrics calculation, and security auditing orchestrator engine.",
    debug=settings.DEBUG,
    lifespan=lifespan,
    # Enriched Swagger Metadata Matrix Refinements
    contact={
        "name": "AI Reviewer Core Development Team",
        "url": "https://github.com",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# Bind global domain exception translation middleware framework matrix
setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the structural, isolated route controller domains
# Root level health verification gateway
app.include_router(health_router)

# Centralized version-controlled endpoint feature router
app.include_router(api_router, prefix="/api")

logger.success("FastAPI runtime orchestration container assembled completely. Standing by for worker lifecycles.")
