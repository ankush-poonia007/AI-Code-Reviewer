from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.config import settings
from backend.constants import validate_language, validate_safe_filename

class ReviewRequest(BaseModel):
    """
    Public API request schema validating incoming user code review requests.
    Enforces a strict trust boundary by completely forbidding extra untracked fields.
    """
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(
        ..., 
        min_length=1, 
        description="The name of the file being submitted for review (e.g., 'main.py')."
    )
    language: str = Field(
        ..., 
        min_length=1, 
        description="The programming language profile key string (e.g., 'python')."
    )
    source_code: str = Field(
        ..., 
        min_length=1, 
        description="The raw unparsed code string contents requiring analysis."
    )

    @field_validator("filename")
    @classmethod
    def validate_filename_field(cls, value: str) -> str:
        return validate_safe_filename(value)

    @field_validator("language")
    @classmethod
    def validate_language_field(cls, value: str) -> str:
        return validate_language(value)

    @field_validator("source_code")
    @classmethod
    def validate_source_code_size(cls, value: str) -> str:
        encoded = value.encode("utf-8")
        max_bytes = settings.max_source_code_bytes
        if len(encoded) > max_bytes:
            raise ValueError(
                f"Source code exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
            )
        return value
