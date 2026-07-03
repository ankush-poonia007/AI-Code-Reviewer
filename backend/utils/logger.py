import sys
from pathlib import Path
from loguru import logger
from backend.config import settings

def setup_logging() -> None:
    """
    Configures and establishes Loguru as the exclusive centralized logging system.
    Eliminates default standard output handlers to guarantee uniform formatting.
    """
    # 1. Strip default framework logging handlers to avoid duplicated messages
    logger.remove()

    # 2. Register the high-visibility console output stream for real-time development debugging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO"
    )

    # 3. Establish a persistent, rolling log storage system inside the dedicated logs/ directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG" if settings.DEBUG else "INFO",
        encoding="utf-8"
    )

    logger.success("Centralized Loguru application engine initialized successfully.")
