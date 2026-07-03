from sqlalchemy import Column, String, Numeric, Integer, Enum, DateTime
from sqlalchemy.orm import relationship
from backend.models.base_model import BaseModel
from backend.models.enums import DBLanguage, DBReviewStatus

class Review(BaseModel):
    """
    Primary metadata schema tracking an independent code review execution.
    Inherits UUID primary keys and audit columns from BaseModel.
    """
    __tablename__ = "reviews"

    filename = Column(String, nullable=False)
    language = Column(Enum(DBLanguage), nullable=False, index=True)
    overall_score = Column(Numeric(5, 2), nullable=False, default=0.00)
    executive_summary = Column(String, nullable=False)
    status = Column(Enum(DBReviewStatus), nullable=False, default=DBReviewStatus.PENDING, index=True)
    review_duration_ms = Column(Integer, nullable=False, default=0)
    deleted_at = Column(DateTime, nullable=True)  # Reserved for future soft-delete usage

    # Strict structural parent relations mapped to downstream items
    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")
    execution = relationship("ReviewExecution", back_populates="review", uselist=False, cascade="all, delete-orphan")
