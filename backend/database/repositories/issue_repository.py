from typing import List
from sqlalchemy.orm import Session
from backend.models import Issue

class IssueRepository:
    """
    Isolated data access gateway managing persistent CRUD actions for parsed analytical Issue logs.
    """
    @staticmethod
    def bulk_create(db: Session, issue_instances: List[Issue]) -> List[Issue]:
        """Bulk inserts a collection of generated issues linked to a review session."""
        db.add_all(issue_instances)
        db.commit()
        return issue_instances

    @staticmethod
    def get_by_review_id(db: Session, review_id: str) -> List[Issue]:
        """Pulls all detailed issue findings mapped to a single parent code review record."""
        return db.query(Issue).filter(Issue.review_id == review_id).all()
