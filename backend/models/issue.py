from sqlalchemy import Column, String, Integer, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from backend.models.base_model import BaseModel
from backend.models.enums import CategoryEnum, SeverityEnum

class Issue(BaseModel):
    """
    Detailed analytical vulnerability entry linked back to a parent Code Review.
    """
    __tablename__ = "issues"

    review_id = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(Enum(CategoryEnum), nullable=False, index=True)
    issue_type = Column(String, nullable=False)
    severity = Column(Enum(SeverityEnum), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)      # Converted to Text
    recommendation = Column(Text, nullable=False)   # Converted to Text
    code_snippet = Column(Text, nullable=True)      # Converted to Text
    line_number = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)       # Range conceptually validated at 0.0 - 1.0

    # Relationship link mappings back up to parent database record
    review = relationship("Review", back_populates="issues")
