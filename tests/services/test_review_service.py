import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from backend.services.review_service import ReviewService
from backend.database.repositories import ReviewRepository, IssueRepository, ExecutionRepository
from backend.providers.exceptions import LLMProviderError, ResponseParsingError
from backend.models.review import Review
from backend.models.issue import Issue
from backend.models.review_execution import ReviewExecution
from backend.models.enums import ReviewStatusEnum

@pytest.fixture
def review_service(db_session: Session, mock_llm_provider) -> ReviewService:
    """Instantiates ReviewService with real repositories and mock LLM provider."""
    return ReviewService(
        db=db_session,
        review_repo=ReviewRepository(db_session),
        issue_repo=IssueRepository(db_session),
        execution_repo=ExecutionRepository(db_session),
        llm_provider=mock_llm_provider
    )

async def test_review_service_success_workflow(review_service, mock_llm_provider, sample_python_code, sample_valid_ai_response, db_session):
    # Setup mock provider response
    mock_llm_provider.set_response(sample_valid_ai_response)

    review_id, parsed_result = await review_service.review_code(
        filename="main.py",
        language="python",
        source_code=sample_python_code
    )

    assert review_id is not None
    assert parsed_result.overall_score == 75.0
    assert len(parsed_result.issues) == 2

    # Query DB using a clean queries to verify commits are persisted
    review_uuid = UUID(review_id)
    review_record = db_session.query(Review).filter(Review.id == review_id).first()
    assert review_record is not None
    assert review_record.status == ReviewStatusEnum.COMPLETED
    assert review_record.overall_score == 75.0

    issues = db_session.query(Issue).filter(Issue.review_id == review_id).all()
    assert len(issues) == 2
    assert {iss.line_number for iss in issues} == {1, 2}

    execution = db_session.query(ReviewExecution).filter(ReviewExecution.review_id == review_id).first()
    assert execution is not None
    assert execution.provider == "groq"
    assert execution.input_tokens == 100

async def test_review_service_transaction_integrity_on_provider_failure(review_service, mock_llm_provider, sample_python_code, db_session):
    # Configure provider to raise an exception
    mock_llm_provider.set_response(LLMProviderError("Groq service outage"))

    with pytest.raises(LLMProviderError):
        await review_service.review_code(
            filename="main.py",
            language="python",
            source_code=sample_python_code
        )

    # 1. Verify primary transaction rolled back:
    # COMPLETED review should NEVER be written after rollback
    completed_reviews = db_session.query(Review).filter(
        Review.status == ReviewStatusEnum.COMPLETED
    ).all()
    assert len(completed_reviews) == 0

    # PENDING review shouldn't be left in database under current connection session
    pending_reviews = db_session.query(Review).filter(
        Review.status == ReviewStatusEnum.PENDING
    ).all()
    assert len(pending_reviews) == 0

    # 2. Verify FAILED audit record is written and committed in isolated transaction
    # Since isolated transaction commits on a separate connection, we query the DB
    all_reviews = db_session.query(Review).all()
    assert len(all_reviews) == 1
    failed_review = all_reviews[0]
    assert failed_review.status == ReviewStatusEnum.FAILED
    assert "Code analysis failed due to an underlying execution error" in failed_review.executive_summary

    # 3. Verify no orphan child records exist for this review (issues and executions must be empty)
    associated_issues = db_session.query(Issue).filter(Issue.review_id == failed_review.id).all()
    assert len(associated_issues) == 0

    associated_executions = db_session.query(ReviewExecution).filter(ReviewExecution.review_id == failed_review.id).all()
    assert len(associated_executions) == 0

async def test_review_service_transaction_integrity_on_parser_failure(review_service, mock_llm_provider, sample_python_code, sample_malformed_ai_response, db_session):
    # Configure provider to return malformed JSON content
    mock_llm_provider.set_response(sample_malformed_ai_response)

    with pytest.raises(ResponseParsingError):
        await review_service.review_code(
            filename="main.py",
            language="python",
            source_code=sample_python_code
        )

    # Verify primary transaction rolled back and FAILED audit record is saved
    all_reviews = db_session.query(Review).all()
    assert len(all_reviews) == 1
    failed_review = all_reviews[0]
    assert failed_review.status == ReviewStatusEnum.FAILED
    assert "malformed" in failed_review.executive_summary.lower() or "did not adhere" in failed_review.executive_summary.lower() or "fail" in failed_review.executive_summary.lower()

    # Verify no orphan issues or executions
    assert db_session.query(Issue).filter(Issue.review_id == failed_review.id).count() == 0
    assert db_session.query(ReviewExecution).filter(ReviewExecution.review_id == failed_review.id).count() == 0

async def test_review_service_list_reviews(review_service, db_session, review_factory):
    from datetime import datetime, timezone, timedelta
    base_time = datetime.now(timezone.utc)
    
    # Insert 2 review records with strictly increasing created_at times
    review1 = review_factory(score=85)
    review1.created_at = base_time - timedelta(seconds=10)
    review2 = review_factory(score=90)
    review2.created_at = base_time

    db_session.add(review1)
    db_session.add(review2)
    db_session.commit()

    summaries = await review_service.list_reviews(skip=0, limit=10)
    assert len(summaries) == 2
    assert summaries[0].review_id == str(review2.id) # Ordered newest first

async def test_review_service_get_review_detail(review_service, db_session, review_factory, issue_factory, execution_factory):
    review = review_factory()
    db_session.add(review)
    db_session.commit()

    issue = issue_factory(review_id=review.id)
    execution = execution_factory(review_id=review.id)
    db_session.add(issue)
    db_session.add(execution)
    db_session.commit()

    detail = await review_service.get_review(UUID(review.id))
    assert detail.review_id == str(review.id)
    assert len(detail.issues) == 1
    assert detail.execution is not None
    assert detail.execution.provider == "groq"

async def test_review_service_delete_review(review_service, db_session, review_factory, issue_factory, execution_factory):
    review = review_factory()
    db_session.add(review)
    db_session.commit()

    issue = issue_factory(review_id=review.id)
    execution = execution_factory(review_id=review.id)
    db_session.add(issue)
    db_session.add(execution)
    db_session.commit()

    # Perform cascade deletion
    await review_service.delete_review(UUID(review.id))

    # Verify cascading deleted everything
    assert db_session.query(Review).filter(Review.id == review.id).first() is None
    assert db_session.query(Issue).filter(Issue.review_id == review.id).count() == 0
    assert db_session.query(ReviewExecution).filter(ReviewExecution.review_id == review.id).first() is None

async def test_review_service_dashboard_statistics(review_service, db_session, review_factory, issue_factory):
    # Populate DB with dashboard values
    review1 = review_factory(status=ReviewStatusEnum.COMPLETED, score=90)
    review2 = review_factory(status=ReviewStatusEnum.COMPLETED, score=80)
    review3 = review_factory(status=ReviewStatusEnum.FAILED)
    db_session.add_all([review1, review2, review3])
    db_session.commit()

    issue1 = issue_factory(review_id=review1.id, severity="CRITICAL")
    issue2 = issue_factory(review_id=review2.id, severity="HIGH")
    db_session.add_all([issue1, issue2])
    db_session.commit()

    stats = await review_service.dashboard_statistics()
    assert stats.total_reviews == 3
    assert stats.completed_reviews == 2
    assert stats.failed_reviews == 1
    assert stats.average_score == 85.0
    assert stats.critical_issue_count == 1
    assert stats.high_issue_count == 1
