import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Centralized Application Configuration.
    Single source of truth utilizing pydantic-settings to automatically pull,
    type-convert, and validate all multi-environment provider variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ==========================================
    # Core Application Configuration
    # ==========================================
    APP_NAME: str = Field(default="AI Code Review Assistant")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)

    # ==========================================
    # Persistent Storage Layout
    # ==========================================
    DATABASE_URL: str = Field(default="sqlite:///./ai_code_reviewer.db")

    # ==========================================
    # Provider-Agnostic LLM Infrastructure
    # ==========================================
    LLM_PROVIDER: str = Field(default="groq")  # Supported: "groq", "gemini", "ollama"
    MAX_TOKENS: int = Field(default=4096)
    TEMPERATURE: float = Field(default=0.2)
    LLM_REQUEST_TIMEOUT_SECONDS: int = Field(default=120)

    # Individual Ecosystem API Target Tokens & Models
    GROQ_API_KEY: str = Field(default="")
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")

    # ==========================================
    # File Staging & Upload Directory Limits
    # ==========================================
    UPLOAD_DIR: str = Field(default="uploads")
    REPORT_DIR: str = Field(default="reports")
    MAX_FILE_SIZE_MB: int = Field(default=5)

    # ==========================================
    # Runtime Guardrail Interceptors
    # ==========================================
    @field_validator("LLM_PROVIDER", mode="before")
    @classmethod
    def validate_provider_selection(cls, value: str) -> str:
        """Ensures selected AI orchestrator engine is a recognized platform target."""
        cleaned = str(value).strip().lower() if value else "groq"
        allowed_platforms = {"groq", "gemini", "ollama"}
        if cleaned not in allowed_platforms:
            raise ValueError(
                f"\n[CONFIG CRITICAL] LLM_PROVIDER '{cleaned}' is unsupported.\n"
                f"Please update your .env to target one of: {list(allowed_platforms)}"
            )
        return cleaned

    def verify_active_credentials(self) -> None:
        """
        Dynamically intercepts and ensures the specific API key for the 
        currently chosen provider exists at application boot time.
        """
        provider = self.LLM_PROVIDER.lower()
        if provider == "groq" and (not self.GROQ_API_KEY or "your_actual" in self.GROQ_API_KEY):
            raise ValueError("\n[CONFIG CRITICAL] GROQ_API_KEY is missing or unconfigured in your .env file.")
        elif provider == "gemini" and (not self.GEMINI_API_KEY or "your_actual" in self.GEMINI_API_KEY):
            raise ValueError("\n[CONFIG CRITICAL] GEMINI_API_KEY is missing or unconfigured in your .env file.")

# Instantiate a single, global settings instance for system-wide consumption
settings = Settings()
