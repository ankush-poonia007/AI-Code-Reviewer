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

class ResponseParsingError(LLMProviderError):
    """
    Raised when the raw text payload cannot be cleanly parsed or fails 
    application business schema validation constraints.
    """
    pass
