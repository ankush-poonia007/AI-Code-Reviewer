import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.providers.base_provider import LLMProvider
from backend.providers.response_models import LLMResponse, UsageMetadata

class MockLLMProvider(LLMProvider):
    """A clean, real-behaving mock LLM provider for service and integration testing."""
    def __init__(self):
        self._provider_name = "groq"
        self.content = "{}"
        self.model_name = "mock-llama-model"
        self.calls = []

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def set_response(self, content: str, model_name: str = "mock-llama-model", provider_name: str = "groq"):
        self.content = content
        self.model_name = model_name
        self._provider_name = provider_name

    async def generate_review(self, prompt: str) -> LLMResponse:
        self.calls.append(prompt)
        if isinstance(self.content, Exception):
            raise self.content
        return LLMResponse(
            content=self.content,
            model_name=self.model_name,
            usage=UsageMetadata(
                input_tokens=100,
                output_tokens=200,
                total_tokens=300
            )
        )

@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Fixture providing an instance of MockLLMProvider."""
    return MockLLMProvider()
