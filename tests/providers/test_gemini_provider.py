import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from google.genai.errors import APIError

from backend.providers.gemini_provider import GeminiProvider
from backend.providers.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMProviderUnavailableError,
    LLMProviderError
)

@pytest.fixture
def mock_gemini_sdk(mocker):
    mock_client_class = mocker.patch("backend.providers.gemini_provider.genai.Client")
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance

    mock_generate = AsyncMock()
    mock_client_instance.aio.models.generate_content = mock_generate
    return mock_generate

async def test_gemini_provider_success(mock_gemini_sdk):
    mock_response = MagicMock()
    mock_response.text = '{"overall_score": 95}'
    
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 60
    mock_usage.candidates_token_count = 120
    mock_usage.total_token_count = 180
    mock_response.usage_metadata = mock_usage

    mock_gemini_sdk.return_value = mock_response

    provider = GeminiProvider()
    response = await provider.generate_review("test prompt")

    assert response.content == '{"overall_score": 95}'
    assert response.model_name == provider._model_name
    assert response.usage.input_tokens == 60
    assert response.usage.output_tokens == 120
    assert response.usage.total_tokens == 180

async def test_gemini_provider_empty_response(mock_gemini_sdk):
    mock_response = MagicMock()
    mock_response.text = None  # Empty response content
    mock_gemini_sdk.return_value = mock_response

    provider = GeminiProvider()
    with pytest.raises(LLMProviderError) as exc:
        await provider.generate_review("test prompt")
    assert "empty response" in str(exc.value)

async def test_gemini_provider_api_error_auth(mock_gemini_sdk):
    err = APIError(401, {"message": "Auth failed"})
    mock_gemini_sdk.side_effect = err

    provider = GeminiProvider()
    with pytest.raises(LLMAuthenticationError) as exc:
        await provider.generate_review("test prompt")
    assert "authentication or access forbidden" in str(exc.value)

async def test_gemini_provider_api_error_rate_limit(mock_gemini_sdk):
    err = APIError(429, {"message": "Quota exceeded"})
    mock_gemini_sdk.side_effect = err

    provider = GeminiProvider()
    with pytest.raises(LLMRateLimitError) as exc:
        await provider.generate_review("test prompt")
    assert "rate limit exceeded" in str(exc.value)

async def test_gemini_provider_api_error_unavailable(mock_gemini_sdk):
    err = APIError(503, {"message": "Service Unavailable"})
    mock_gemini_sdk.side_effect = err

    provider = GeminiProvider()
    with pytest.raises(LLMProviderUnavailableError) as exc:
        await provider.generate_review("test prompt")
    assert "service unavailable" in str(exc.value)

async def test_gemini_provider_timeout(mock_gemini_sdk):
    err = httpx.TimeoutException("Connection timed out")
    mock_gemini_sdk.side_effect = err

    provider = GeminiProvider()
    with pytest.raises(LLMTimeoutError) as exc:
        await provider.generate_review("test prompt")
    assert "timed out" in str(exc.value)

async def test_gemini_provider_http_error(mock_gemini_sdk):
    err = httpx.HTTPError("DNS resolution failed")
    mock_gemini_sdk.side_effect = err

    provider = GeminiProvider()
    with pytest.raises(LLMProviderUnavailableError) as exc:
        await provider.generate_review("test prompt")
    assert "communicate with Gemini" in str(exc.value)
