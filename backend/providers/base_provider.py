from abc import ABC, abstractmethod
from backend.providers.response_models import LLMResponse
from backend.providers.exceptions import (
    LLMProviderError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMProviderUnavailableError,
)

__all__ = [
    "LLMProvider",
    "LLMProviderError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMProviderUnavailableError",
]


class LLMProvider(ABC):
    """
    Abstract Base Class outlining the mandatory contract for hot-swappable AI engines.
    Forces strict interface symmetry across all integrated third-party platforms.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Returns a clean string representing the unique name of the platform (e.g., 'groq', 'gemini').
        """
        pass

    @abstractmethod
    async def generate_review(self, prompt: str) -> LLMResponse:
        """
        Dispatches a fully constructed execution prompt payload to the third-party infrastructure.
        
        Args:
            prompt: Already prepared system instructions and target source code text built by an upper layer.
            
        Returns:
            A normalized LLMResponse schema object container.
            
        Raises:
            LLMAuthenticationError: For invalid or expired credentials.
            LLMRateLimitError: When platform throughput limits are exhausted.
            LLMTimeoutError: For connectivity failures.
            LLMProviderUnavailableError: For service out-of-order or DNS drops.
            LLMProviderError: For unclassified infrastructure errors.
        """
        pass
