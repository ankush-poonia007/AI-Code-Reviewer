import pytest
from sqlalchemy.orm import Session
from backend.database.repositories.review_repository import ReviewRepository
from backend.database.repositories.issue_repository import IssueRepository
from backend.models.enums import ReviewStatusEnum, SeverityEnum

def test_issue_repo_crud(db_session: Session, review_factory, issue_factory):
    review_repo = ReviewRepository(db_session)
    issue_repo = IssueRepository(db_session)

    # Setup parent review record
    review = review_repo.create(review_factory())
    db_session.commit()

    # 1. Create issue
    issue = issue_factory(review_id=review.id, line=5)
    created = issue_repo.create(issue)
    assert created.id is not None
    assert created.line_number == 5

    # 2. Get by review id
    issues = issue_repo.get_by_review_id(review.id)
    assert len(issues) == 1
    assert issues[0].id == created.id

    # 3. Delete by review id
    deleted = issue_repo.delete_by_review_id(review.id)
    assert deleted is True
    assert len(issue_repo.get_by_review_id(review.id)) == 0

def test_issue_repo_create_many_and_sorting(db_session: Session, review_factory, issue_factory):
    review_repo = ReviewRepository(db_session)
    issue_repo = IssueRepository(db_session)

    review = review_repo.create(review_factory())
    db_session.commit()

    # Create issues with mixed line numbers
    issues_list = [
        issue_factory(review_id=review.id, line=10),
        issue_factory(review_id=review.id, line=2),
        issue_factory(review_id=review.id, line=15)
    ]
    issue_repo.create_many(issues_list)
    db_session.commit()

    retrieved = issue_repo.get_by_review_id(review.id)
    assert len(retrieved) == 3
    # Check deterministic line number ascending sorting
    assert retrieved[0].line_number == 2
    assert retrieved[1].line_number == 10
    assert retrieved[2].line_number == 15

def test_issue_repo_severity_counts(db_session: Session, review_factory, issue_factory):
    review_repo = ReviewRepository(db_session)
    issue_repo = IssueRepository(db_session)

    review = review_repo.create(review_factory())
    db_session.commit()

    # Check empty severity counts
    empty_counts = issue_repo.get_severity_counts()
    assert empty_counts["critical_issue_count"] == 0
    assert empty_counts["high_issue_count"] == 0
    assert empty_counts["medium_issue_count"] == 0
    assert empty_counts["low_issue_count"] == 0

    # Insert issues with different severities
    issue_repo.create(issue_factory(review_id=review.id, severity="CRITICAL"))
    issue_repo.create(issue_factory(review_id=review.id, severity="CRITICAL"))
    issue_repo.create(issue_factory(review_id=review.id, severity="HIGH"))
    issue_repo.create(issue_factory(review_id=review.id, severity="MEDIUM"))
    db_session.commit()

    counts = issue_repo.get_severity_counts()
    assert counts["critical_issue_count"] == 2
    assert counts["high_issue_count"] == 1
    assert counts["medium_issue_count"] == 1
    assert counts["low_issue_count"] == 0
