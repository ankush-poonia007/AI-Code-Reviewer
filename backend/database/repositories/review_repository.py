from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models import Review
from backend.models.enums import DBReviewStatus

class ReviewRepository:
    """
    Isolated data access gateway managing persistent CRUD actions for Review records.
    """
    @staticmethod
    def create(db: Session, review_instance: Review) -> Review:
        """Saves a fresh core review initialization record to disk."""
        db.add(review_instance)
        db.commit()
        db.refresh(review_instance)
        return review_instance

    @staticmethod
    def get_by_id(db: Session, review_id: str) -> Optional[Review]:
        """Retrieves a specific review by its unique UUID key while respecting soft deletes."""
        return db.query(Review).filter(Review.id == review_id, Review.deleted_at.is_(None)).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 10) -> List[Review]:
        """Returns a paginated list of non-deleted historical review logs."""
        return db.query(Review).filter(Review.deleted_at.is_(None)).offset(skip).limit(limit).all()

    @staticmethod
    def update_status(db: Session, review_id: str, status: DBReviewStatus) -> Optional[Review]:
        """Updates the operational execution state of an active review tracking thread."""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            review.status = status
            db.commit()
            db.refresh(review)
        return review
