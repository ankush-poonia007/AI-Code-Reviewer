import pytest
from backend.models.review import Review
from backend.models.issue import Issue
from backend.models.review_execution import ReviewExecution
from backend.models.enums import ReviewStatusEnum, SeverityEnum, CategoryEnum, ProgrammingLanguageEnum

@pytest.fixture
def sample_python_code() -> str:
    return """def get_user(db, user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query).fetchall()
"""

@pytest.fixture
def sample_valid_ai_response() -> str:
    return """{
  "overall_score": 75.0,
  "executive_summary": "The file contains a serious SQL injection risk and some stylistic improvements.",
  "issues": [
    {
      "category": "SECURITY_ANALYSIS",
      "issue_type": "SQL Injection",
      "severity": "CRITICAL",
      "title": "SQL Injection vulnerability",
      "description": "Direct string interpolation detected in SQL construction.",
      "recommendation": "Rewrite the query using query parameters instead of f-strings.",
      "code_snippet": "query = f\\"SELECT * FROM users WHERE id = {user_id}\\"",
      "line_number": 2,
      "confidence": 0.95
    },
    {
      "category": "BEST_PRACTICES",
      "issue_type": "Variable Naming",
      "severity": "LOW",
      "title": "Generic naming conventions",
      "description": "The variable 'db' could be renamed to 'db_connection' to improve readability.",
      "recommendation": "Change parameter db to db_connection.",
      "code_snippet": "def get_user(db, user_id):",
      "line_number": 1,
      "confidence": 0.80
    }
  ]
}"""

@pytest.fixture
def sample_clean_ai_response() -> str:
    return """{
  "overall_score": 95.0,
  "executive_summary": "No issues found. Excellent quality code.",
  "issues": []
}"""

@pytest.fixture
def sample_markdown_ai_response() -> str:
    return """Here is the analysis results:
```json
{
  "overall_score": 90.0,
  "executive_summary": "Overall very clean code.",
  "issues": []
}
```
Footnotes: analyzed using llama-3."""

@pytest.fixture
def sample_malformed_ai_response() -> str:
    return '{"overall_score": "seventy-five", "issues": "none"}'

@pytest.fixture
def sample_extra_fields_ai_response() -> str:
    return """{
  "overall_score": 85.0,
  "executive_summary": "Summary text",
  "extra_unwanted_field": "some hallucination",
  "issues": []
}"""

@pytest.fixture
def review_factory():
    """Helper to generate a populated Review DB model instance."""
    def _create(filename="main.py", language="python", status=ReviewStatusEnum.COMPLETED, score=85.0):
        return Review(
            filename=filename,
            language=ProgrammingLanguageEnum(language),
            overall_score=score,
            executive_summary="Sample review summary",
            status=ReviewStatusEnum(status),
            review_duration_ms=1200
        )
    return _create

@pytest.fixture
def issue_factory():
    """Helper to generate a populated Issue DB model instance."""
    def _create(review_id, category="SECURITY_ANALYSIS", severity="CRITICAL", line=10):
        return Issue(
            review_id=review_id,
            category=CategoryEnum(category),
            issue_type="Test Issue",
            severity=SeverityEnum(severity),
            title="Sample Title",
            description="Sample description details",
            recommendation="Sample remediation recommendation",
            code_snippet="sample_code()",
            line_number=line,
            confidence=0.9
        )
    return _create

@pytest.fixture
def execution_factory():
    """Helper to generate a populated ReviewExecution DB model instance."""
    def _create(review_id, provider="groq", model="llama-3.3-70b-versatile"):
        return ReviewExecution(
            review_id=review_id,
            provider=provider,
            model_name=model,
            temperature=0.2,
            max_tokens=4096,
            processing_time_ms=1200,
            prompt_version="1.0.0",
            input_tokens=100,
            output_tokens=200,
            total_tokens=300
        )
    return _create
