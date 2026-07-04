from sqlalchemy.orm import sessionmaker
from backend.database.database import engine

# Unified transactional session execution factory configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
