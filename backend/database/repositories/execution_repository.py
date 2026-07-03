from typing import Optional
from sqlalchemy.orm import Session
from backend.models import ReviewExecution

class ExecutionRepository:
    """
    Isolated data access gateway managing persistent storage of LLM engine runtime telemetry metrics.
    """
    @staticmethod
    def create(db: Session, execution_instance: ReviewExecution) -> ReviewExecution:
        """Stores structural AI orchestrator processing timings and parameters."""
        db.add(execution_instance)
        db.commit()
        db.refresh(execution_instance)
        return execution_instance

    @staticmethod
    def get_by_review_id(db: Session, review_id: str) -> Optional[ReviewExecution]:
        """Retrieves execution metrics for a specific review, enforcing the 1:1 relation boundary."""
        return db.query(ReviewExecution).filter(ReviewExecution.review_id == review_id).first()
