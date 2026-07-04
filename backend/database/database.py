from sqlalchemy import create_engine, event, text
from backend.config import settings

# Safe extraction of the structural storage pathway
DATABASE_URL = settings.DATABASE_URL

# Establish the core engine communication wrapper instance
# connect_args is mandatory for SQLite to prevent cross-thread exceptions during API routing
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {}
)


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
        """Enable WAL mode to improve concurrent read access during open write transactions."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


def probe_connection() -> bool:
    """Returns True when the database engine accepts a connectivity probe."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
