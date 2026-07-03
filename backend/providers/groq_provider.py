from groq import AsyncGroq, APIStatusError, APIConnectionError, APITimeoutError
from backend.providers.base_provider import LLMProvider
from backend.providers.response_models import LLMResponse, UsageMetadata
from backend.providers.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMProviderUnavailableError,
    LLMProviderError
)
from backend.config import settings
from loguru import logger

class GroqProvider(LLMProvider):
    """
    Concrete adapter for the Groq AI platform using the official AsyncGroq SDK.
    Enforces thin layout isolation boundaries following ADR-021 and ADR-022.
    """

    def __init__(self) -> None:
        """Initializes the underlying async client using variables from config.py."""
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self._model_name = settings.GROQ_MODEL
        # Structural log contextualization binding to match Gemini exactly
        self._logger = logger.bind(provider="groq", component="provider")

    @property
    def provider_name(self) -> str:
        """Standard provider key utilized system-wide for metrics and factory bindings."""
        return "groq"

    async def generate_review(self, prompt: str) -> LLMResponse:
        """
        Dispatches the prepared string instruction prompt to Groq's Chat Completions API.
        Translates raw SDK exceptions into standard domain-specific exceptions.
        """
        try:
            self._logger.info(f"Generating code review using Groq with model: {self._model_name}")
            
            # Transport mapping payload construction
            completion = await self._client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self._model_name,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
            )

            # Defensive fallback normalization handling for null values - fixed with array index extraction
            raw_content = completion.choices[0].message.content
            response_text = raw_content if raw_content is not None else ""
            
            token_stats = completion.usage
            input_tokens = token_stats.prompt_tokens if token_stats else 0
            output_tokens = token_stats.completion_tokens if token_stats else 0
            
            # Explicit dynamic fallback mapping to ensure total_tokens is never omitted
            total_tokens = (
                token_stats.total_tokens 
                if token_stats and hasattr(token_stats, "total_tokens") and token_stats.total_tokens is not None 
                else (input_tokens + output_tokens)
            )

            # Map vendor metrics cleanly to the unified transport schema container
            return LLMResponse(
                content=response_text,
                model_name=self._model_name,
                usage=UsageMetadata(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens
                )
            )

        except APIStatusError as e:
            status = e.status_code
            if status in (401, 403):
                raise LLMAuthenticationError(f"Groq authentication or access forbidden: {str(e)}") from e
            elif status == 429:
                raise LLMRateLimitError(f"Groq rate limit exceeded: {str(e)}") from e
            elif status in (502, 503, 504):
                raise LLMProviderUnavailableError(f"Groq service unavailable: {str(e)}") from e
            else:
                raise LLMProviderError(f"Groq API error [{status}]: {str(e)}") from e

        except APITimeoutError as e:
            raise LLMTimeoutError(f"Groq request timed out: {str(e)}") from e

        except APIConnectionError as e:
            raise LLMProviderUnavailableError(f"Failed to communicate with Groq servers: {str(e)}") from e

        except Exception as e:
            raise LLMProviderError(f"Unexpected error inside Groq adapter pipeline: {str(e)}") from e
