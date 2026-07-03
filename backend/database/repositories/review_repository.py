from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.review import Review
from backend.models.enums import ReviewStatusEnum

class ReviewRepository:
    """
    Isolated data access gateway managing persistent CRUD actions for Review records.
    Communicates exclusively with SQLAlchemy; contains no business or AI logic.
    """
    def __init__(self, db: Session) -> None:
        """Initializes the repository with an active SQLAlchemy session."""
        self.db = db

    @staticmethod
    def create(self, review: Review) -> Review:
        """
        Persists a new code review tracking record to the database.
        Note: Commit is handled by the calling service to support transaction boundaries.
        """
        self.db.add(review)
        # Flush pending changes to the database while keeping the transaction open.
        self.db.flush()
        return review


    @staticmethod
    def get_by_id(db: Session, review_id: str) -> Optional[Review]:
        """
        Retrieves a specific review record using its unique UUID text key.
        """
        return db.query(Review).filter(Review.id == review_id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 10) -> List[Review]:
        """
        Returns a paginated list of historical code review records.
        """
        return db.query(Review).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_status(db: Session, review_id: str, status: ReviewStatusEnum) -> Optional[Review]:
        """
        Updates the operational tracking status of an active code review thread.
        """
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            review.status = status
            db.flush()
        return review

    @staticmethod
    def delete(db: Session, review_id: str) -> bool:
        """
        Removes a code review record from the database.
        Triggers database cascade rules automatically for downstream entities.
        """
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            db.delete(review)
            db.flush()
            return True
        return False
