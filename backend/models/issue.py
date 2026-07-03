from sqlalchemy import Column, String, Integer, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.models.base_model import BaseModel
from backend.models.enums import DBCategory, DBSeverity

class Issue(BaseModel):
    """
    Detailed analytical vulnerability entry linked back to a parent Code Review.
    Inherits UUID primary keys and audit columns from BaseModel.
    """
    __tablename__ = "issues"

    review_id = Column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(Enum(DBCategory), nullable=False, index=True)
    issue_type = Column(String, nullable=False)
    severity = Column(Enum(DBSeverity), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)
    code_snippet = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)

    # Relationship link mappings back up to parent database record
    review = relationship("Review", back_populates="issues")
