from datetime import datetime, timezone
from sqlalchemy import Column, DateTime

class TimestampMixin:
    """
    Decoupled SQLAlchemy Mixin providing automated UTC audit trail timestamps 
    for tracking object generation and updates.
    """
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
