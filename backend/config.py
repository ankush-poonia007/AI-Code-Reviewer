import os
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Ensure the local root .env file is proactively parsed and loaded into environment variables
load_dotenv()

class Settings(BaseModel):
    """
    Centralized Application Configuration.
    Acts as the exclusive single source of truth for runtime variables,
    enforcing rigorous Pydantic 2.x schema validation at initialization.
    """
    
    # ==========================================
    # Application Config
    # ==========================================
    APP_NAME: str = Field(default=os.getenv("APP_NAME", "AI Code Review Assistant"))
    APP_VERSION: str = Field(default=os.getenv("APP_VERSION", "1.0.0"))
    DEBUG: bool = Field(default=os.getenv("DEBUG", "True").lower() in ("true", "1", "yes", "on"))
    HOST: str = Field(default=os.getenv("HOST", "127.0.0.1"))
    PORT: int = Field(default=int(os.getenv("PORT", "8000")))

    # ==========================================
    # Database Config
    # ==========================================
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./ai_code_reviewer.db"))

    # ==========================================
    # Groq Config
    # ==========================================
    GROQ_API_KEY: str = Field(default=os.getenv("GROQ_API_KEY", ""))
    DEFAULT_MODEL: str = Field(default=os.getenv("DEFAULT_MODEL", "llama3-70b-8192"))
    MAX_TOKENS: int = Field(default=int(os.getenv("MAX_TOKENS", "4096")))
    TEMPERATURE: float = Field(default=float(os.getenv("TEMPERATURE", "0.2")))

    # ==========================================
    # Uploads & Reports Storage Config
    # ==========================================
    UPLOAD_DIR: str = Field(default=os.getenv("UPLOAD_DIR", "uploads"))
    REPORT_DIR: str = Field(default=os.getenv("REPORT_DIR", "reports"))
    MAX_FILE_SIZE_MB: int = Field(default=int(os.getenv("MAX_FILE_SIZE_MB", "5")))

    # ==========================================
    # Validation Rules
    # ==========================================
    @field_validator("GROQ_API_KEY", mode="before")
    @classmethod
    def validate_groq_key(cls, value: str) -> str:
        """
        Guards application instantiation by forcing strict validation of the Groq credential.
        Raises an immediate ValueError if the key is missing or is left as a placeholder.
        """
        cleaned_value = str(value).strip() if value else ""
        if not cleaned_value or cleaned_value == "gsk_your_actual_groq_api_key_here":
            raise ValueError(
                "\n[CRITICAL RUNTIME ERROR] GROQ_API_KEY is missing or unconfigured in your .env file.\n"
                "Please add a valid Groq API credential before launching the application backend."
            )
        return cleaned_value

# Instantiate a single, global settings object for system-wide consumption
settings = Settings()
