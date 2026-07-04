import pytest
from sqlalchemy.orm import Session
from backend.database.repositories.review_repository import ReviewRepository
from backend.database.repositories.execution_repository import ExecutionRepository

def test_execution_repo_crud(db_session: Session, review_factory, execution_factory):
    review_repo = ReviewRepository(db_session)
    exec_repo = ExecutionRepository(db_session)

    review = review_repo.create(review_factory())
    db_session.commit()

    # 1. Create execution
    execution = execution_factory(review_id=review.id, provider="groq", model="llama-3")
    created = exec_repo.create(execution)
    assert created.id is not None
    assert created.provider == "groq"
    assert created.model_name == "llama-3"

    # 2. Get by review id
    retrieved = exec_repo.get_by_review_id(review.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.review_id == review.id
