import pytest
from uuid import uuid4
from backend.models.enums import ReviewStatusEnum
from backend.models.review import Review

def test_api_models_endpoint(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200

    data = response.json()
    assert "provider" in data
    assert "model" in data
    assert "temperature" in data
    assert "max_tokens" in data

def test_api_reviews_list_pagination(client, db_session, review_factory):
    # Populate DB
    for i in range(15):
        r = review_factory(filename=f"file_{i}.py")
        db_session.add(r)
    db_session.commit()

    # List all default (limit 10)
    response = client.get("/api/v1/reviews")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

    # Custom pagination
    response = client.get("/api/v1/reviews?skip=10&limit=10")
    data = response.json()
    assert len(data) == 5

def test_api_get_review_detail(client, db_session, review_factory, issue_factory, execution_factory):
    # Missing review id
    response = client.get(f"/api/v1/reviews/{uuid4()}")
    assert response.status_code == 404

    # Invalid UUID format
    response = client.get("/api/v1/reviews/not-a-uuid")
    assert response.status_code == 422

    # Success case
    r = review_factory()
    db_session.add(r)
    db_session.commit()

    iss = issue_factory(review_id=r.id)
    exe = execution_factory(review_id=r.id)
    db_session.add_all([iss, exe])
    db_session.commit()

    response = client.get(f"/api/v1/reviews/{r.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["review_id"] == str(r.id)
    assert len(data["issues"]) == 1
    assert data["execution"]["provider"] == "groq"

def test_api_delete_review(client, db_session, review_factory, issue_factory, execution_factory):
    r = review_factory()
    db_session.add(r)
    db_session.commit()

    iss = issue_factory(review_id=r.id)
    exe = execution_factory(review_id=r.id)
    db_session.add_all([iss, exe])
    db_session.commit()

    # Delete
    response = client.delete(f"/api/v1/reviews/{r.id}")
    assert response.status_code == 204

    # Try to delete missing
    response = client.delete(f"/api/v1/reviews/{uuid4()}")
    assert response.status_code == 404

    # Verify database cascade deleted everything
    assert db_session.query(Review).filter(Review.id == r.id).count() == 0

def test_api_get_review_issues(client, db_session, review_factory, issue_factory):
    # Missing
    response = client.get(f"/api/v1/reviews/{uuid4()}/issues")
    assert response.status_code == 404

    # Success
    r = review_factory()
    db_session.add(r)
    db_session.commit()

    iss = issue_factory(review_id=r.id)
    db_session.add(iss)
    db_session.commit()

    response = client.get(f"/api/v1/reviews/{r.id}/issues")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["line_number"] == iss.line_number

def test_api_get_review_execution(client, db_session, review_factory, execution_factory):
    # Missing review
    response = client.get(f"/api/v1/reviews/{uuid4()}/execution")
    assert response.status_code == 404

    r = review_factory()
    db_session.add(r)
    db_session.commit()

    # Review exists but execution missing
    response = client.get(f"/api/v1/reviews/{r.id}/execution")
    assert response.status_code == 404

    # Success
    exe = execution_factory(review_id=r.id)
    db_session.add(exe)
    db_session.commit()

    response = client.get(f"/api/v1/reviews/{r.id}/execution")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "groq"
    assert data["model_name"] == "llama-3.3-70b-versatile"
