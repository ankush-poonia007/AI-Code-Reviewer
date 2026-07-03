from sqlalchemy import Column, String, Numeric, Integer, Enum, Text
from sqlalchemy.orm import relationship
from backend.models.base_model import BaseModel
from backend.models.enums import ProgrammingLanguageEnum, ReviewStatusEnum

class Review(BaseModel):
    """
    Primary metadata schema tracking an independent code review execution.
    """
    __tablename__ = "reviews"

    filename = Column(String, nullable=False)
    language = Column(Enum(ProgrammingLanguageEnum), nullable=False, index=True)
    overall_score = Column(Numeric(5, 2), nullable=False, default=0.00)
    executive_summary = Column(Text, nullable=False)  # Converted to Text for large summary payloads
    status = Column(Enum(ReviewStatusEnum), nullable=False, default=ReviewStatusEnum.PENDING, index=True)
    review_duration_ms = Column(Integer, nullable=False, default=0)

    # Strict structural parent relations mapped to downstream items
    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")
    execution = relationship("ReviewExecution", back_populates="review", uselist=False, cascade="all, delete-orphan")
