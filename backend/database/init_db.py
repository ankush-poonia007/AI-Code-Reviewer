from loguru import logger
from backend.database.database import engine
from backend.database.base import Base
# Explicitly import models to register them on the Base metadata tree before creation
from backend.models import Review, Issue, ReviewExecution

def init_database() -> None:
    """
    Bootstraps the relational storage engine by establishing the local SQLite database 
    and automatically generating all missing tables matching our frozen schemas.
    """
    logger.info("Initializing relational database storage schema generation...")
    try:
        # Inspect and emit table definitions to disk if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.success("Database engine tables bootstrapped and verified successfully.")
    except Exception as e:
        logger.critical(f"Database schema bootstrap failed: {str(e)}")
        raise e

if __name__ == "__main__":
    init_database()
