import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from groq import APIStatusError, APITimeoutError, APIConnectionError

from backend.providers.groq_provider import GroqProvider
from backend.providers.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMProviderUnavailableError,
    LLMProviderError
)

@pytest.fixture
def mock_groq_sdk(mocker):
    # Patch AsyncGroq in the groq_provider module
    mock_class = mocker.patch("backend.providers.groq_provider.AsyncGroq")
    mock_instance = MagicMock()
    mock_class.return_value = mock_instance

    mock_create = AsyncMock()
    mock_instance.chat.completions.create = mock_create
    return mock_create

async def test_groq_provider_success(mock_groq_sdk):
    # Setup mock completions response
    mock_choice = MagicMock()
    mock_choice.message.content = '{"overall_score": 90}'
    
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 100
    mock_usage.total_tokens = 150

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage

    mock_groq_sdk.return_value = mock_completion

    provider = GroqProvider()
    response = await provider.generate_review("test prompt")

    assert response.content == '{"overall_score": 90}'
    assert response.model_name == provider._model_name
    assert response.usage.input_tokens == 50
    assert response.usage.output_tokens == 100
    assert response.usage.total_tokens == 150

async def test_groq_provider_empty_choices(mock_groq_sdk):
    mock_completion = MagicMock()
    mock_completion.choices = []  # Empty choice array
    mock_groq_sdk.return_value = mock_completion

    provider = GroqProvider()
    with pytest.raises(LLMProviderError) as exc:
        await provider.generate_review("test prompt")
    assert "empty choices array" in str(exc.value)

async def test_groq_provider_auth_error(mock_groq_sdk):
    # Construct real HTTPStatusError parameters to satisfy Groq's APIStatusError
    mock_request = httpx.Request("POST", "https://api.groq.com")
    mock_response = httpx.Response(status_code=401, request=mock_request)
    err = APIStatusError("Unauthorized", response=mock_response, body=None)

    mock_groq_sdk.side_effect = err

    provider = GroqProvider()
    with pytest.raises(LLMAuthenticationError) as exc:
        await provider.generate_review("test prompt")
    assert "authentication or access forbidden" in str(exc.value)

async def test_groq_provider_rate_limit(mock_groq_sdk):
    mock_request = httpx.Request("POST", "https://api.groq.com")
    mock_response = httpx.Response(status_code=429, request=mock_request)
    err = APIStatusError("Rate Limit", response=mock_response, body=None)

    mock_groq_sdk.side_effect = err

    provider = GroqProvider()
    with pytest.raises(LLMRateLimitError) as exc:
        await provider.generate_review("test prompt")
    assert "rate limit exceeded" in str(exc.value)

async def test_groq_provider_unavailable(mock_groq_sdk):
    mock_request = httpx.Request("POST", "https://api.groq.com")
    mock_response = httpx.Response(status_code=503, request=mock_request)
    err = APIStatusError("Service Unavailable", response=mock_response, body=None)

    mock_groq_sdk.side_effect = err

    provider = GroqProvider()
    with pytest.raises(LLMProviderUnavailableError) as exc:
        await provider.generate_review("test prompt")
    assert "service unavailable" in str(exc.value)

async def test_groq_provider_timeout(mock_groq_sdk):
    mock_request = httpx.Request("POST", "https://api.groq.com")
    err = APITimeoutError(request=mock_request)

    mock_groq_sdk.side_effect = err

    provider = GroqProvider()
    with pytest.raises(LLMTimeoutError) as exc:
        await provider.generate_review("test prompt")
    assert "timed out" in str(exc.value)

async def test_groq_provider_connection_error(mock_groq_sdk):
    mock_request = httpx.Request("POST", "https://api.groq.com")
    err = APIConnectionError(request=mock_request)

    mock_groq_sdk.side_effect = err

    provider = GroqProvider()
    with pytest.raises(LLMProviderUnavailableError) as exc:
        await provider.generate_review("test prompt")
    assert "communicate with Groq" in str(exc.value)
