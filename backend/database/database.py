from sqlalchemy import create_engine
from backend.config import settings

# Safe extraction of the structural storage pathway
DATABASE_URL = settings.DATABASE_URL

# Establish the core engine communication wrapper instance
# connect_args is mandatory for SQLite to prevent cross-thread exceptions during API routing
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}
)
