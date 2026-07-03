from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.models.review_execution import ReviewExecution

class ExecutionRepository:
    """
    Isolated data access gateway managing persistent CRUD actions for ReviewExecution logs.
    Communicates exclusively with SQLAlchemy; uses instance-based sessions.
    """

    def __init__(self, db: Session) -> None:
        """Initializes the repository with an active SQLAlchemy session."""
        self.db = db

    def create(self, execution: ReviewExecution) -> ReviewExecution:
        """
        Persists runtime AI metrics and provider execution profiles to the database.
        Note: Commit is handled by the calling service to support transaction boundaries.
        """
        self.db.add(execution)
        # Flush pending changes to the database while keeping the transaction open.
        self.db.flush()
        return execution

    def get_by_review_id(self, review_id: UUID) -> Optional[ReviewExecution]:
        """
        Retrieves the exact 1:1 execution tracking telemetry mapped to a specific review.
        """
        id_str = str(review_id)
        return self.db.query(ReviewExecution).filter(ReviewExecution.review_id == id_str).first()
