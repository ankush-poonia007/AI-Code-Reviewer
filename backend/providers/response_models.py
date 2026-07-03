from pydantic import BaseModel, Field

class UsageMetadata(BaseModel):
    """
    Encapsulated token consumption metrics for language model executions.
    """
    input_tokens: int = Field(default=0, description="Total tokens consumed in the instruction payload.")
    output_tokens: int = Field(default=0, description="Total tokens generated in the completion payload.")
    total_tokens: int = Field(default=0, description="Sum of input and output tokens for the execution transaction.")


class LLMResponse(BaseModel):
    """
    Standard transportation payload schema for language model outputs.
    Guarantees the core business layer never sees raw vendor SDK structures.
    """
    content: str = Field(description="The raw unparsed text response string returned from the AI engine.")
    model_name: str = Field(description="The explicit model identifier string that processed the transaction.")
    usage: UsageMetadata = Field(default_factory=UsageMetadata, description="Granular token consumption parameters tracker.")
