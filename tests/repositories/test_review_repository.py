import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from backend.database.repositories.review_repository import ReviewRepository
from backend.models.review import Review
from backend.models.enums import ReviewStatusEnum, ProgrammingLanguageEnum

def test_review_repo_crud(db_session: Session, review_factory):
    repo = ReviewRepository(db_session)

    # 1. Create
    new_review = review_factory(filename="test.py", language="python", status=ReviewStatusEnum.PENDING)
    created = repo.create(new_review)
    assert created.id is not None
    assert created.status == ReviewStatusEnum.PENDING

    # In-session query should find it
    retrieved = repo.get_by_id(created.id)
    assert retrieved is not None
    assert retrieved.filename == "test.py"

    # 2. Update status
    repo.update_status(created.id, ReviewStatusEnum.COMPLETED)
    assert created.status == ReviewStatusEnum.COMPLETED

    # 3. Update generic field
    created.overall_score = 92.5
    repo.update(created)
    
    db_session.commit()

    # Query from new database connection/session to ensure persistence
    retrieved2 = repo.get_by_id(created.id)
    assert retrieved2.overall_score == 92.5
    assert retrieved2.status == ReviewStatusEnum.COMPLETED

    # 4. Delete
    deleted = repo.delete(created.id)
    assert deleted is True
    db_session.commit()

    assert repo.get_by_id(created.id) is None

def test_review_repo_list_pagination(db_session: Session, review_factory):
    repo = ReviewRepository(db_session)
    from datetime import datetime, timezone, timedelta
    base_time = datetime.now(timezone.utc)

    # Create 5 reviews with strictly increasing timestamps
    for i in range(5):
        rev = review_factory(filename=f"file_{i}.py", score=80.0 + i)
        rev.created_at = base_time + timedelta(seconds=i)
        repo.create(rev)
    db_session.commit()

    # Test list_all ordering and pagination
    all_reviews = repo.list_all(skip=0, limit=10)
    assert len(all_reviews) == 5
    # Order should be created_at desc (newest first)
    assert all_reviews[0].filename == "file_4.py"

    # Test offset limit
    subset = repo.list_all(skip=2, limit=2)
    assert len(subset) == 2
    assert subset[0].filename == "file_2.py"

def test_review_repo_persist_in_isolated_transaction(db_session: Session, review_factory):
    repo = ReviewRepository(db_session)
    import uuid
    
    # 1. Create a review model in memory (not added to db_session yet)
    review = review_factory(filename="audit.py", status=ReviewStatusEnum.FAILED)
    review.id = str(uuid.uuid4())  # Explicitly assign ID in memory
    review_id = review.id

    # Persist via isolated transaction (should insert)
    ReviewRepository.persist_in_isolated_transaction(review)

    # Check that it exists in our current test session
    db_session.expire_all()
    inserted = repo.get_by_id(review_id)
    assert inserted is not None
    assert inserted.status == ReviewStatusEnum.FAILED
    assert inserted.filename == "audit.py"

    # 2. Mutate state and update via isolated transaction (should update)
    updated_review = review_factory(filename="audit.py", status=ReviewStatusEnum.COMPLETED, score=88.0)
    updated_review.id = review_id
    ReviewRepository.persist_in_isolated_transaction(updated_review)

    db_session.expire_all()
    updated = repo.get_by_id(review_id)
    assert updated.status == ReviewStatusEnum.COMPLETED
    assert updated.overall_score == 88.0

def test_review_repo_dashboard_stats(db_session: Session, review_factory):
    repo = ReviewRepository(db_session)

    # Empty stats
    empty_stats = repo.get_dashboard_stats()
    assert empty_stats["total_reviews"] == 0
    assert empty_stats["completed_reviews"] == 0
    assert empty_stats["failed_reviews"] == 0
    assert empty_stats["average_score"] == 0.0

    # Populated stats
    repo.create(review_factory(status=ReviewStatusEnum.COMPLETED, score=90.0))
    repo.create(review_factory(status=ReviewStatusEnum.COMPLETED, score=80.0))
    repo.create(review_factory(status=ReviewStatusEnum.FAILED))
    db_session.commit()

    stats = repo.get_dashboard_stats()
    assert stats["total_reviews"] == 3
    assert stats["completed_reviews"] == 2
    assert stats["failed_reviews"] == 1
    assert stats["average_score"] == 85.0
