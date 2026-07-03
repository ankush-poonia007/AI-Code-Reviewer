from typing import List
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
