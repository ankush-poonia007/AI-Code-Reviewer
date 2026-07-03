from typing import List, Optional
from pydantic import BaseModel, Field, confloat, ConfigDict
from backend.constants import ReviewCategory, ReviewSeverity

class ParsedIssue(BaseModel):
    """
    Business validation schema representing a single code defect found by the AI.
    """
    # Enforce strict property validation to block structural hallucinations
    model_config = ConfigDict(extra="forbid")

    category: ReviewCategory = Field(description="The domain category classification of the defect.")
    issue_type: str = Field(description="The granular specific type of bug (e.g. 'SQL Injection').")
    severity: ReviewSeverity = Field(description="The risk threat impact classification tier.")
    title: str = Field(description="A concise title summarizing the vulnerability.")
    description: str = Field(description="An exhaustive technical analysis of why this is a problem.")
    recommendation: str = Field(description="An actionable, step-by-step resolution remediation fix.")
    code_snippet: Optional[str] = Field(default=None, description="The direct matching block of problematic code.")
    line_number: Optional[int] = Field(default=None, description="Target line number inside the code asset file.")
    confidence: Optional[confloat(ge=0.0, le=1.0)] = Field(default=1.0, description="Confidence metric bounded tightly between 0.0 and 1.0.")


class ParsedReviewResult(BaseModel):
    """
    Business validation schema representing a complete parsed AI review output report.
    """
    # Enforce strict property validation to block structural hallucinations
    model_config = ConfigDict(extra="forbid")

    overall_score: confloat(ge=0.0, le=100.0) = Field(description="Deterministic quality metric grade bounded tightly between 0.0 and 100.0.")
    executive_summary: str = Field(description="High-level markdown or text summary of the code quality analysis.")
    issues: List[ParsedIssue] = Field(default_factory=list, description="Collection of granular isolated software flaws discovered.")
