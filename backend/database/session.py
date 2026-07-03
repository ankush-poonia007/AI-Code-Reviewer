from sqlalchemy.orm import sessionmaker
from backend.database.database import engine

# Unified transactional session execution factory configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI Context Manager Dependency Provider.
    Yields an active transactional pipeline and forces a clean connection 
    disposal/close immediately following endpoint response termination.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
