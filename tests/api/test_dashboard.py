import pytest
from backend.models.enums import ReviewStatusEnum

def test_api_dashboard_empty(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200

    data = response.json()
    assert data["total_reviews"] == 0
    assert data["completed_reviews"] == 0
    assert data["failed_reviews"] == 0
    assert data["average_score"] == 0.0
    assert data["average_processing_time"] == 0.0
    assert data["critical_issue_count"] == 0

def test_api_dashboard_populated(client, db_session, review_factory, issue_factory):
    # Setup data
    r1 = review_factory(status=ReviewStatusEnum.COMPLETED, score=90.0)
    r2 = review_factory(status=ReviewStatusEnum.COMPLETED, score=80.0)
    r3 = review_factory(status=ReviewStatusEnum.FAILED)
    
    db_session.add_all([r1, r2, r3])
    db_session.commit()

    i1 = issue_factory(review_id=r1.id, severity="CRITICAL")
    i2 = issue_factory(review_id=r2.id, severity="HIGH")
    
    db_session.add_all([i1, i2])
    db_session.commit()

    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200

    data = response.json()
    assert data["total_reviews"] == 3
    assert data["completed_reviews"] == 2
    assert data["failed_reviews"] == 1
    assert data["average_score"] == 85.0
    assert data["critical_issue_count"] == 1
    assert data["high_issue_count"] == 1
