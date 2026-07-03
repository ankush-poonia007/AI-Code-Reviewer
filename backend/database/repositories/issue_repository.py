from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from backend.models.issue import Issue

class IssueRepository:
    """
    Isolated data access gateway managing persistent CRUD actions for parsed analytical Issue logs.
    Communicates exclusively with SQLAlchemy; uses instance-based sessions.
    """

    def __init__(self, db: Session) -> None:
        """Initializes the repository with an active SQLAlchemy session."""
        self.db = db

    def create(self, issue: Issue) -> Issue:
        """
        Persists a single generated issue to the database.
        Note: Commit is handled by the calling service to support transaction boundaries.
        """
        self.db.add(issue)
        self.db.flush()  # Flush pending changes to the database while keeping the transaction open.
        return issue

    def create_many(self, issues: List[Issue]) -> List[Issue]:
        """
        Bulk inserts a collection of generated issues efficiently in one operation.
        Note: Commit is handled by the calling service to support transaction boundaries.
        """
        if not issues:
            return issues
            
        self.db.add_all(issues)
        # Synchronize pending additions to the database while keeping the transaction open.
        self.db.flush()
        return issues

    def get_by_review_id(self, review_id: UUID) -> List[Issue]:
        """
        Retrieves all issues belonging to a specific review sorted deterministically by line number.
        """
        id_str = str(review_id)
        return (
            self.db.query(Issue)
            .filter(Issue.review_id == id_str)
            .order_by(Issue.line_number.asc())
            .all()
        )


    def delete_by_review_id(self, review_id: UUID) -> bool:
        """
        Removes all issues mapping back to a specific review parent record.
        """
        id_str = str(review_id)
        deleted_count = self.db.query(Issue).filter(Issue.review_id == id_str).delete(synchronize_session=False)
        if deleted_count > 0:
            self.db.flush()
            return True
        return False
