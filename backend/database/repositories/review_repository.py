from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from backend.models.review import Review
from backend.models.enums import ReviewStatusEnum
from backend.database.session import SessionLocal

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

    def update(self, review: Review) -> Review:
        """
        Persists in-memory mutations on a tracked review entity within the active transaction.
        Note: Commit is handled by the calling service to support transaction boundaries.
        """
        self.db.flush()
        return review

    @staticmethod
    def persist_in_isolated_transaction(review: Review) -> None:
        """
        Persists or updates a review record in a standalone transaction.
        Used for audit recovery after the primary workflow transaction has been rolled back.
        Inserts when the rolled-back PENDING row no longer exists; updates if a row remains.
        """
        db = SessionLocal()
        try:
            existing = db.query(Review).filter(Review.id == review.id).first()
            if existing:
                existing.status = review.status
                existing.executive_summary = review.executive_summary
                existing.review_duration_ms = review.review_duration_ms
                existing.overall_score = review.overall_score
            else:
                db.add(review)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

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

    def get_dashboard_stats(self) -> dict:
        """
        Aggregates dashboard stats from the reviews table:
        total_reviews, completed_reviews, failed_reviews, average_score, average_processing_time
        """
        from sqlalchemy import func

        total = self.db.query(func.count(Review.id)).scalar() or 0
        completed = self.db.query(func.count(Review.id)).filter(Review.status == ReviewStatusEnum.COMPLETED).scalar() or 0
        failed = self.db.query(func.count(Review.id)).filter(Review.status == ReviewStatusEnum.FAILED).scalar() or 0
        avg_score = self.db.query(func.avg(Review.overall_score)).filter(Review.status == ReviewStatusEnum.COMPLETED).scalar() or 0.0
        avg_duration = self.db.query(func.avg(Review.review_duration_ms)).filter(Review.status == ReviewStatusEnum.COMPLETED).scalar() or 0.0

        return {
            "total_reviews": total,
            "completed_reviews": completed,
            "failed_reviews": failed,
            "average_score": float(avg_score),
            "average_processing_time": float(avg_duration)
        }

