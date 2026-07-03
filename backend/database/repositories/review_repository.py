from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.models.review import Review
from backend.models.enums import ReviewStatusEnum

class ReviewRepository:
    """
    Isolated data access gateway managing persistent CRUD actions for Review records.
    Communicates exclusively with SQLAlchemy; uses instance-based sessions.
    """
    def __init__(self, db: Session) -> None:
        """Initializes the repository with an active SQLAlchemy session."""
        self.db = db

    def create(self, review: Review) -> Review:
        """
        Persists a new code review tracking record to the database.
        Note: Commit is handled by the calling service to support transaction boundaries.
        """
        self.db.add(review)
        # Flush pending changes to the database while keeping the transaction open.
        self.db.flush()
        return review

    def get_by_id(self, review_id: UUID) -> Optional[Review]:
        """
        Retrieves a specific review record using its unique UUID key.
        """
        id_str = str(review_id)
        return self.db.query(Review).filter(Review.id == id_str).first()

    def list_all(self, skip: int = 0, limit: int = 10) -> List[Review]:
        """
        Returns a paginated list of historical code review records.
        """
        return self.db.query(Review).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

    def update_status(self, review_id: UUID, status: ReviewStatusEnum) -> Optional[Review]:
        """
        Updates the operational tracking status of an active code review thread.
        """
        id_str = str(review_id)
        review = self.db.query(Review).filter(Review.id == id_str).first()
        if review:
            review.status = status
            self.db.flush()
        return review

    def delete(self, review_id: UUID) -> bool:
        """
        Removes a code review record from the database.
        Triggers database cascade rules automatically for downstream entities.
        """
        id_str = str(review_id)
        review = self.db.query(Review).filter(Review.id == id_str).first()
        if review:
            self.db.delete(review)
            self.db.flush()
            return True
        return False
