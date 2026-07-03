from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database.session import SessionLocal
from backend.database.repositories import ReviewRepository, IssueRepository, ExecutionRepository
from backend.providers.provider_factory import ProviderFactory
from backend.services.review_service import ReviewService

def get_db() -> Generator[Session, None, None]:
    """
    Yields an active database session matching structural lifecycle conventions.
    Guarantees resources close safely right after transaction termination.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    """
    FastAPI dependency injection provider assembling the complete orchestration layer on-demand.
    Enforces ADR-029 by passing abstract providers and instance repositories down to the service layer.
    """
    # Factory resolves the abstract provider instance cleanly based on active environment variables
    llm_provider = ProviderFactory.get_provider()

    # Pass the active session along with repositories and provider interface down to the orchestrator
    return ReviewService(
        db=db,
        review_repo=ReviewRepository(db),
        issue_repo=IssueRepository(db),
        execution_repo=ExecutionRepository(db),
        llm_provider=llm_provider
    )
