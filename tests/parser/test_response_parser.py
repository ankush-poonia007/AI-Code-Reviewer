import pytest
from backend.providers.response_parser import ResponseParser
from backend.providers.exceptions import ResponseParsingError
from backend.schemas.review_result import ParsedReviewResult

def test_extract_json_string_raw():
    raw = '{"overall_score": 90.0, "executive_summary": "Good", "issues": []}'
    extracted = ResponseParser._extract_json_string(raw)
    assert extracted == raw

def test_extract_json_string_markdown():
    markdown = 'Some conversation\n```json\n{"overall_score": 90.0, "executive_summary": "Good", "issues": []}\n```\nFootnotes'
    extracted = ResponseParser._extract_json_string(markdown)
    assert extracted == '{"overall_score": 90.0, "executive_summary": "Good", "issues": []}'

def test_extract_json_string_markdown_no_tag():
    markdown = '```\n{"overall_score": 90.0, "executive_summary": "Good", "issues": []}\n```'
    extracted = ResponseParser._extract_json_string(markdown)
    assert extracted == '{"overall_score": 90.0, "executive_summary": "Good", "issues": []}'

def test_extract_json_string_greedy_brace():
    text = 'Resulting JSON: {"overall_score": 90.0, "executive_summary": "Good", "issues": []} is what we found.'
    extracted = ResponseParser._extract_json_string(text)
    assert extracted == '{"overall_score": 90.0, "executive_summary": "Good", "issues": []}'

def test_parse_valid_response(sample_valid_ai_response):
    parsed = ResponseParser.parse_review_response(sample_valid_ai_response)
    assert isinstance(parsed, ParsedReviewResult)
    assert parsed.overall_score == 75.0
    assert len(parsed.issues) == 2
    assert parsed.issues[0].category.value == "SECURITY_ANALYSIS"
    assert parsed.issues[0].severity.value == "CRITICAL"

def test_parse_clean_response(sample_clean_ai_response):
    parsed = ResponseParser.parse_review_response(sample_clean_ai_response)
    assert parsed.overall_score == 95.0
    assert len(parsed.issues) == 0

def test_parse_markdown_response(sample_markdown_ai_response):
    parsed = ResponseParser.parse_review_response(sample_markdown_ai_response)
    assert parsed.overall_score == 90.0
    assert len(parsed.issues) == 0

def test_parse_malformed_response(sample_malformed_ai_response):
    with pytest.raises(ResponseParsingError) as exc:
        ResponseParser.parse_review_response(sample_malformed_ai_response)
    assert "validation error" in str(exc.value) or "JSON" in str(exc.value)

def test_parse_extra_fields_response(sample_extra_fields_ai_response):
    with pytest.raises(ResponseParsingError) as exc:
        ResponseParser.parse_review_response(sample_extra_fields_ai_response)
    assert "validation error" in str(exc.value) or "schema layout" in str(exc.value)

def test_parse_empty_string():
    with pytest.raises(ResponseParsingError) as exc:
        ResponseParser.parse_review_response("")
    assert "empty text" in str(exc.value)

    with pytest.raises(ResponseParsingError) as exc:
        ResponseParser.parse_review_response("   ")
    assert "empty text" in str(exc.value)
