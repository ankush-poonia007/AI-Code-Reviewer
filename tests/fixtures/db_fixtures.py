import pytest
from sqlalchemy.orm import Session

from backend.database import Base, engine as db_engine
from backend.database.session import SessionLocal
from backend.database.repositories import ReviewRepository, IssueRepository, ExecutionRepository
from backend.models.review import Review
from backend.models.issue import Issue
from backend.models.review_execution import ReviewExecution
from backend.api.dependencies import get_db
from backend.main import app

@pytest.fixture(scope="session", autouse=True)
def setup_db_schema():
    """Ensure database schema is created on test session start."""
    Base.metadata.create_all(bind=db_engine)
    yield
    # We let cleanup_test_db in conftest.py clean up the actual database files on disk.

@pytest.fixture
def db_session() -> Session:
    """
    Provides a clean database session for each test.
    Deletes all records after the test run to ensure strict isolation.
    """
    session = SessionLocal()
    yield session
    session.close()

    # Isolated cleanup session to clear the tables after the test runs
    cleanup_session = SessionLocal()
    try:
        # Delete dependent tables first to respect foreign keys
        cleanup_session.query(Issue).delete()
        cleanup_session.query(ReviewExecution).delete()
        cleanup_session.query(Review).delete()
        cleanup_session.commit()
    except Exception:
        cleanup_session.rollback()
    finally:
        cleanup_session.close()

@pytest.fixture(autouse=True)
def override_api_db(db_session: Session):
    """Automatically overrides the FastAPI dependency to use the test session."""
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def client():
    """Provides a TestClient wrapper around the FastAPI application."""
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
