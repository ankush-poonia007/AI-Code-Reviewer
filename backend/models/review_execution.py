from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base_model import BaseModel

class ReviewExecution(BaseModel):
    """
    Operational analytics and telemetry metrics recorded during an LLM pipeline call.
    Inherits UUID primary keys and audit columns from BaseModel.
    """
    __tablename__ = "review_executions"

    review_id = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    provider = Column(String, nullable=False)      # Target ecosystem platform engines (e.g., "groq", "gemini")
    model_name = Column(String, nullable=False)    # Exact open-weights string identifier
    temperature = Column(Float, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    prompt_version = Column(String, nullable=True)

    # Core token tracking columns synchronized with service mapping requirements
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    # Contextual connection mappings back up to parent database entity record
    review = relationship("Review", back_populates="execution")
