from abc import ABC, abstractmethod
from backend.providers.response_models import LLMResponse


# =====================================================================
# 1️⃣ Core Exception Taxonomy
# =====================================================================
class LLMProviderError(Exception):
    """Base application domain exception for all AI provider-layer operational failures."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when vendor API credential authentication fails (e.g., HTTP 401)."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when hitting third-party execution or quota throttling limits (e.g., HTTP 429)."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when network latency exceeds client connection boundaries."""
    pass


class LLMProviderUnavailableError(LLMProviderError):
    """Raised when remote endpoints are unreachable due to DNS failures or maintenance."""
    pass


# =====================================================================
# 2️⃣ The Abstract Provider Contract (ABC)
# =====================================================================
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
