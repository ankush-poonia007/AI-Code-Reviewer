import pytest
from io import BytesIO
from unittest.mock import patch
from backend.main import app
from backend.api.dependencies import get_review_service
from backend.services.review_service import ReviewService
from backend.database.repositories import ReviewRepository, IssueRepository, ExecutionRepository
from backend.providers.exceptions import LLMProviderError, ResponseParsingError
from backend.models.review import Review
from backend.models.enums import ReviewStatusEnum

@pytest.fixture(autouse=True)
def override_review_service(db_session, mock_llm_provider):
    service = ReviewService(
        db=db_session,
        review_repo=ReviewRepository(db_session),
        issue_repo=IssueRepository(db_session),
        execution_repo=ExecutionRepository(db_session),
        llm_provider=mock_llm_provider
    )
    def _override():
        return service
    app.dependency_overrides[get_review_service] = _override
    yield service
    app.dependency_overrides.pop(get_review_service, None)

def test_api_submit_review_success(client, mock_llm_provider, sample_valid_ai_response):
    mock_llm_provider.set_response(sample_valid_ai_response)

    payload = {
        "filename": "app.py",
        "language": "python",
        "source_code": "def process(): pass"
    }
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "review_id" in data
    assert data["status"] == "COMPLETED"
    assert data["overall_score"] == 75.0
    assert len(data["issues"]) == 2

def test_api_submit_review_validation_errors(client):
    # 1. Missing required field (filename)
    payload = {
        "language": "python",
        "source_code": "print('hello')"
    }
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 422

    # 2. Empty source code
    payload = {
        "filename": "app.py",
        "language": "python",
        "source_code": ""
    }
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 422

    # 3. Malformed payload - extra field
    payload = {
        "filename": "app.py",
        "language": "python",
        "source_code": "print('hello')",
        "extra_field": "not_allowed"
    }
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 422

def test_api_submit_review_provider_failure(client, mock_llm_provider):
    mock_llm_provider.set_response(LLMProviderError("Outage"))

    payload = {
        "filename": "app.py",
        "language": "python",
        "source_code": "print('hello')"
    }
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"] == "AI Engine Operational Error"

def test_api_submit_review_parser_failure(client, mock_llm_provider, sample_malformed_ai_response):
    mock_llm_provider.set_response(sample_malformed_ai_response)

    payload = {
        "filename": "app.py",
        "language": "python",
        "source_code": "print('hello')"
    }
    response = client.post("/api/v1/review", json=payload)
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"] == "Response Formatting Failure"

def test_api_submit_review_file_success(client, mock_llm_provider, sample_valid_ai_response):
    mock_llm_provider.set_response(sample_valid_ai_response)

    file_data = {
        "language": (None, "python"),
        "file": ("script.py", BytesIO(b"def compute(): pass"), "text/plain")
    }
    response = client.post("/api/v1/review/file", files=file_data)
    assert response.status_code == 200

    data = response.json()
    assert "review_id" in data
    assert data["status"] == "COMPLETED"
    assert data["overall_score"] == 75.0

def test_api_submit_review_file_unsupported_language(client):
    file_data = {
        "language": (None, "pdf"),  # unsupported language
        "file": ("script.py", BytesIO(b"def compute(): pass"), "text/plain")
    }
    response = client.post("/api/v1/review/file", files=file_data)
    assert response.status_code == 400
    assert "unsupported language" in response.json()["detail"].lower()

def test_api_submit_review_file_empty(client):
    file_data = {
        "language": (None, "python"),
        "file": ("script.py", BytesIO(b""), "text/plain")
    }
    response = client.post("/api/v1/review/file", files=file_data)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_api_submit_review_file_utf8_decode_failure(client):
    # Non-utf8 binary data (e.g. invalid bytes)
    file_data = {
        "language": (None, "python"),
        "file": ("script.py", BytesIO(b"\x80\x81\x82"), "text/plain")
    }
    response = client.post("/api/v1/review/file", files=file_data)
    assert response.status_code == 400
    assert "utf-8" in response.json()["detail"].lower()

def test_api_submit_review_file_unsafe_filename(client):
    file_data = {
        "language": (None, "python"),
        "file": ("../../etc/passwd", BytesIO(b"def check(): pass"), "text/plain")
    }
    response = client.post("/api/v1/review/file", files=file_data)
    assert response.status_code == 400
    assert "separators" in response.json()["detail"].lower()
