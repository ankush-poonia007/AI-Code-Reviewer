import httpx
from google import genai
from google.genai.errors import APIError
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

class GeminiProvider(LLMProvider):
    """
    Concrete adapter for the Google Gemini platform using the modern Google Gen AI SDK.
    Enforces thin layout boundaries without leaking client implementation details.
    """

    def __init__(self) -> None:
        """Initializes the underlying async client using variables from config.py."""
        # Using the standard modern client wrapper initialized explicitly via API key parameters
        self._client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=genai.types.HttpOptions(timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS * 1000),
        )
        self._model_name = settings.GEMINI_MODEL
        # Structured log contextualization binding following identical Groq patterns
        self._logger = logger.bind(provider="gemini", component="provider")

    @property
    def provider_name(self) -> str:
        """Standard provider key utilized system-wide for metrics and factory bindings."""
        return "gemini"

    async def generate_review(self, prompt: str) -> LLMResponse:
        """
        Dispatches the prepared string instruction prompt to Google's Gen AI Models API.
        Translates raw SDK exceptions into system-wide domain-specific exceptions.
        """
        try:
            self._logger.info(f"Dispatching async request to Gemini API using model: {self._model_name}")
            
            # Utilizing the modern client's async .aio gateway context for non-blocking execution
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=settings.TEMPERATURE,
                    max_output_tokens=settings.MAX_TOKENS,
                )
            )

            # Defensive handling parsing extracted text output payloads
            if response.text is None or not response.text.strip():
                raise LLMProviderError("Gemini returned an empty response with no completion content.")

            response_text = response.text
            
            # Safely navigate metadata tracking logs if token counters are supplied
            usage_info = response.usage_metadata
            input_tokens = usage_info.prompt_token_count if usage_info else 0
            output_tokens = usage_info.candidates_token_count if usage_info else 0
            total_tokens = usage_info.total_token_count if usage_info else (input_tokens + output_tokens)

            return LLMResponse(
                content=response_text,
                model_name=self._model_name,
                usage=UsageMetadata(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens
                )
            )

        except APIError as e:
            # Catching Google native client SDK level status errors
            status = e.code
            if status in (401, 403):
                raise LLMAuthenticationError(f"Gemini authentication or access forbidden: {str(e)}") from e
            elif status == 429:
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {str(e)}") from e
            elif status in (502, 503, 504):
                raise LLMProviderUnavailableError(f"Gemini service unavailable: {str(e)}") from e
            else:
                raise LLMProviderError(f"Gemini API error [{status}]: {str(e)}") from e

        except (httpx.TimeoutException, TimeoutError) as e:
            # Catching connection timing limits
            raise LLMTimeoutError(f"Gemini request timed out: {str(e)}") from e

        except httpx.HTTPError as e:
            # Catches all remaining underlying HTTP connection drops, DNS issues, or socket failures
            raise LLMProviderUnavailableError(f"Failed to communicate with Gemini servers: {str(e)}") from e

        except Exception as e:
            # Fallback wrapper for unclassified system faults
            raise LLMProviderError(f"Unexpected error inside Gemini adapter pipeline: {str(e)}") from e
