import pytest
from backend.prompts.review_prompt import ReviewPromptBuilder
from backend.constants import ReviewCategory, ReviewSeverity

def test_prompt_builder_version():
    assert ReviewPromptBuilder.PROMPT_VERSION == "1.0.0"

def test_prompt_builder_structure():
    filename = "test_script.js"
    language = "javascript"
    source_code = "console.log('test');"

    prompt = ReviewPromptBuilder.build_review_prompt(
        filename=filename,
        language=language,
        source_code=source_code
    )

    # Verify key structural components are present
    assert filename in prompt
    assert language in prompt
    assert "<<<BEGIN_SOURCE_CODE>>>" in prompt
    assert "<<<END_SOURCE_CODE>>>" in prompt
    assert source_code in prompt
    assert "SECURITY_ANALYSIS" in prompt
    assert "CRITICAL" in prompt

def test_prompt_builder_is_deterministic():
    filename = "utils.py"
    language = "python"
    source_code = "def add(a, b): return a + b"

    prompt1 = ReviewPromptBuilder.build_review_prompt(filename, language, source_code)
    prompt2 = ReviewPromptBuilder.build_review_prompt(filename, language, source_code)

    assert prompt1 == prompt2
