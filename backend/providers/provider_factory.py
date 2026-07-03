from typing import Dict, Type
from backend.config import settings
from backend.providers.base_provider import LLMProvider
from backend.providers.groq_provider import GroqProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.exceptions import LLMProviderError

class ProviderFactory:
    """
    Stateless registry-driven factory responsible for resolving and instantiating 
    the configured AI model provider adapter, adhering to ADR-024.
    """

    # Declarative class registry mapping string lookup identifiers to un-instantiated class types
    _REGISTRY: Dict[str, Type[LLMProvider]] = {
        "groq": GroqProvider,
        "gemini": GeminiProvider
    }

    @classmethod
    def get_provider(cls) -> LLMProvider:
        """
        Dynamically looks up and instantiates the active AI provider based on environment settings.
        
        Returns:
            An instantiated concrete implementation of the LLMProvider base class.
            
        Raises:
            LLMProviderError: If the configured provider string is missing from the registry mapping.
        """
        # Safely extract the normalized active target configuration key string
        active_provider_key = settings.LLM_PROVIDER.lower().strip()

        # Perform the dictionary mapping lookup transaction
        provider_class = cls._REGISTRY.get(active_provider_key)

        if not provider_class:
            # Deterministic sorted lookup keys tracking to ensure stable production logs
            supported_options = sorted(cls._REGISTRY.keys())
            raise LLMProviderError(
                f"Configuration Error: LLM_PROVIDER '{active_provider_key}' is invalid or unsupported. "
                f"Please update your environment settings to target one of: {supported_options}"
            )

        # Lazy Instantiation occurs exactly on-demand right here
        return provider_class()
