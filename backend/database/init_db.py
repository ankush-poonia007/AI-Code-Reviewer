from loguru import logger
from backend.database import Base, engine

def initialize_database() -> None:
    """
    Ensures the structural relational database schemas exist on disk before 
    the application layer boots up. This function is completely idempotent.
    """
    logger.info("Initializing database schema...")
    try:
        # Core SQLAlchemy mechanism to verify schema existence and create missing structural paths
        Base.metadata.create_all(bind=engine)
        logger.success("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {str(e)}")
        raise e


if __name__ == "__main__":
    # Provides clean, direct terminal invocation support
    initialize_database()
