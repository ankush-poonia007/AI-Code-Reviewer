from pydantic import BaseModel, Field, ConfigDict

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
