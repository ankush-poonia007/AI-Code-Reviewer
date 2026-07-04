import pytest
from unittest.mock import patch

def test_health_check_endpoint_healthy(client):
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert "app_name" in data
    assert "version" in data
    assert "llm_provider" in data
    assert "timestamp" in data

def test_health_check_endpoint_degraded(client):
    # Mock probe_connection to fail
    with patch("backend.api.v1.health.probe_connection", return_value=False):
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "unhealthy"
