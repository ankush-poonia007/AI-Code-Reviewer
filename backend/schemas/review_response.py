from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.schemas.review_result import ParsedIssue

class ReviewResponse(BaseModel):
    """
    Public API contract schema defining what the client frontend receives.
    Strictly isolates internal infrastructure metadata from hitting network outputs.
    """
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(description="The unique 36-character UUID string identifier for the review tracking log.")
    status: str = Field(description="The final operational state of the review pipeline thread (e.g., 'COMPLETED').")
    overall_score: float = Field(description="The final deterministic quality metric score assigned by the reviewer.")
    executive_summary: str = Field(description="The high-level technical summary evaluation narrative text.")
    issues: List[ParsedIssue] = Field(default_factory=list, description="Collection of granular code defects discovered inside the file.")


class ReviewSummaryResponse(BaseModel):
    """
    Lightweight summary object returned by review lists.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_id: str = Field(description="The unique 36-character UUID identifier.")
    filename: str = Field(description="The name of the file reviewed.")
    language: str = Field(description="The programming language profile key string.")
    status: str = Field(description="The current operational status of the review (e.g. 'COMPLETED').")
    overall_score: float = Field(description="The overall quality score of the code.")
    created_at: datetime = Field(description="Timestamp when the review record was created.")
    issue_count: int = Field(description="Total number of issues found during the review.")


class ExecutionResponse(BaseModel):
    """
    Symmetrical representation of LLM execution metadata.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    provider: str = Field(description="Target ecosystem platform engine (e.g., 'groq', 'gemini').")
    model_name: str = Field(description="Exact model identifier string.")
    temperature: float = Field(description="Model generation temperature settings.")
    max_tokens: int = Field(description="Model generation max tokens settings.")
    processing_time_ms: int = Field(description="Time taken by the provider pipeline in milliseconds.")
    prompt_version: Optional[str] = Field(None, description="The version of the prompt template used.")
    input_tokens: int = Field(description="Number of prompt tokens sent to the provider.")
    output_tokens: int = Field(description="Number of completion tokens received from the provider.")
    total_tokens: int = Field(description="Sum of input and output tokens.")


class ReviewDetailResponse(BaseModel):
    """
    Complete detail representation containing review properties, issues, and execution metadata.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    review_id: str = Field(description="The unique 36-character UUID identifier.")
    filename: str = Field(description="The name of the file reviewed.")
    language: str = Field(description="The programming language profile key string.")
    status: str = Field(description="The current operational status of the review.")
    overall_score: float = Field(description="The overall quality score of the code.")
    executive_summary: str = Field(description="The high-level technical summary evaluation narrative text.")
    review_duration_ms: int = Field(description="Total execution time in milliseconds.")
    created_at: datetime = Field(description="Timestamp when the review record was created.")
    updated_at: datetime = Field(description="Timestamp when the review record was last updated.")
    issues: List[ParsedIssue] = Field(default_factory=list, description="Collection of granular code defects discovered.")
    execution: Optional[ExecutionResponse] = Field(None, description="Operational telemetry recorded during the LLM call.")


class DashboardResponse(BaseModel):
    """
    Aggregated statistical metrics for dashboard consumption.
    """
    model_config = ConfigDict(extra="forbid")

    total_reviews: int = Field(description="Total number of reviews in the system.")
    completed_reviews: int = Field(description="Number of successfully completed reviews.")
    failed_reviews: int = Field(description="Number of failed reviews.")
    average_score: float = Field(description="Average quality score across completed reviews.")
    average_processing_time: float = Field(description="Average processing time in ms across completed reviews.")
    critical_issue_count: int = Field(description="Total critical issues found across all reviews.")
    high_issue_count: int = Field(description="Total high-risk issues found across all reviews.")
    medium_issue_count: int = Field(description="Total medium-risk issues found across all reviews.")
    low_issue_count: int = Field(description="Total low-risk issues found across all reviews.")


class ModelInfoResponse(BaseModel):
    """
    Exposes active LLM settings and credentials configurations.
    """
    model_config = ConfigDict(extra="forbid")

    provider: str = Field(description="The currently configured LLM provider.")
    model: str = Field(description="The currently configured default model name.")
    temperature: float = Field(description="The model temperature setting.")
    max_tokens: int = Field(description="The maximum allowed tokens setting.")

