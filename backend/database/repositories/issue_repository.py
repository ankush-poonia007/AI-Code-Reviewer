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

    def get_severity_counts(self) -> dict:
        """
        Aggregates issue counts by severity for the dashboard stats.
        """
        from sqlalchemy import func
        from backend.models.enums import SeverityEnum

        results = (
            self.db.query(Issue.severity, func.count(Issue.id))
            .group_by(Issue.severity)
            .all()
        )

        counts = {
            "critical_issue_count": 0,
            "high_issue_count": 0,
            "medium_issue_count": 0,
            "low_issue_count": 0,
        }

        for severity, count in results:
            if severity == SeverityEnum.CRITICAL or severity == "CRITICAL":
                counts["critical_issue_count"] = count
            elif severity == SeverityEnum.HIGH or severity == "HIGH":
                counts["high_issue_count"] = count
            elif severity == SeverityEnum.MEDIUM or severity == "MEDIUM":
                counts["medium_issue_count"] = count
            elif severity == SeverityEnum.LOW or severity == "LOW":
                counts["low_issue_count"] = count

        return counts

