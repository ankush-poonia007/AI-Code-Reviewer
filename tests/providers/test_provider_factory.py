import pytest
from backend.config import settings
from backend.providers.provider_factory import ProviderFactory
from backend.providers.groq_provider import GroqProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.exceptions import LLMProviderError

def test_provider_factory_singleton():
    # Set provider to groq
    settings.LLM_PROVIDER = "groq"
    provider1 = ProviderFactory.get_provider()
    provider2 = ProviderFactory.get_provider()

    assert isinstance(provider1, GroqProvider)
    assert provider1 is provider2

    # Switch provider to gemini
    settings.LLM_PROVIDER = "gemini"
    provider3 = ProviderFactory.get_provider()
    provider4 = ProviderFactory.get_provider()

    assert isinstance(provider3, GeminiProvider)
    assert provider3 is provider4
    assert provider1 is not provider3

def test_provider_factory_invalid_provider():
    settings.LLM_PROVIDER = "invalid_provider_name"
    with pytest.raises(LLMProviderError) as exc:
        ProviderFactory.get_provider()
    assert "invalid or unsupported" in str(exc.value)

    # Clean up settings to a valid state
    settings.LLM_PROVIDER = "groq"
