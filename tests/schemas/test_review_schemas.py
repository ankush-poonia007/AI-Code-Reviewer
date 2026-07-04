import pytest
from pydantic import ValidationError
from backend.schemas.review_request import ReviewRequest
from backend.schemas.review_result import ParsedIssue, ParsedReviewResult
from backend.constants import ReviewCategory, ReviewSeverity

def test_review_request_validation():
    # Valid python request
    req = ReviewRequest(
        filename="main.py",
        language="python",
        source_code="print('hello')"
    )
    assert req.filename == "main.py"
    assert req.language == "python"
    assert req.source_code == "print('hello')"

def test_review_request_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        ReviewRequest(
            filename="main.py",
            language="python",
            source_code="print('hello')",
            extra_field="unsupported"  # extra="forbid"
        )

def test_review_request_invalid_language():
    with pytest.raises(ValidationError) as exc:
        ReviewRequest(
            filename="main.py",
            language="cobol",  # unsupported
            source_code="print('hello')"
        )
    assert "Unsupported language" in str(exc.value)

def test_review_request_unsafe_filename():
    with pytest.raises(ValidationError) as exc:
        ReviewRequest(
            filename="../../etc/passwd",  # directory traversal
            language="python",
            source_code="print('hello')"
        )
    assert "Filename must not contain path separators" in str(exc.value)

def test_review_request_empty_filename():
    with pytest.raises(ValidationError):
        ReviewRequest(
            filename="",
            language="python",
            source_code="print('hello')"
        )

def test_review_request_oversized_source_code():
    # Construct a payload larger than 5MB
    large_source = "a" * (6 * 1024 * 1024)
    with pytest.raises(ValidationError) as exc:
        ReviewRequest(
            filename="main.py",
            language="python",
            source_code=large_source
        )
    assert "Source code exceeds the maximum allowed size" in str(exc.value)

def test_parsed_issue_validation():
    # Valid issue
    issue = ParsedIssue(
        category=ReviewCategory.SECURITY_ANALYSIS,
        issue_type="XSS",
        severity=ReviewSeverity.HIGH,
        title="Cross site scripting",
        description="Vulnerability description",
        recommendation="Escape input",
        code_snippet="document.write(input)",
        line_number=15,
        confidence=0.9
    )
    assert issue.category == ReviewCategory.SECURITY_ANALYSIS
    assert issue.severity == ReviewSeverity.HIGH
    assert issue.confidence == 0.9

def test_parsed_issue_confidence_bounds():
    # Confidence must be between 0.0 and 1.0
    with pytest.raises(ValidationError):
        ParsedIssue(
            category=ReviewCategory.SECURITY_ANALYSIS,
            issue_type="XSS",
            severity=ReviewSeverity.HIGH,
            title="Cross site scripting",
            description="Vulnerability",
            recommendation="Fix it",
            confidence=1.5  # Out of bounds (>1.0)
        )

    with pytest.raises(ValidationError):
        ParsedIssue(
            category=ReviewCategory.SECURITY_ANALYSIS,
            issue_type="XSS",
            severity=ReviewSeverity.HIGH,
            title="Cross site scripting",
            description="Vulnerability",
            recommendation="Fix it",
            confidence=-0.1  # Out of bounds (<0.0)
        )

def test_parsed_review_result_score_bounds():
    # Score must be between 0.0 and 100.0
    with pytest.raises(ValidationError):
        ParsedReviewResult(
            overall_score=105.0,  # Out of bounds (>100.0)
            executive_summary="Summary",
            issues=[]
        )

    with pytest.raises(ValidationError):
        ParsedReviewResult(
            overall_score=-5.0,  # Out of bounds (<0.0)
            executive_summary="Summary",
            issues=[]
        )
