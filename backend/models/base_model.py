from backend.database import Base
from backend.models.mixins.uuid_mixin import UUIDMixin
from backend.models.mixins.timestamp_mixin import TimestampMixin

class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Unified application base model.
    Combines UUID primary keys and Audit Timestamps via multi-inheritance.
    Declares abstract status to prevent direct table generation by SQLAlchemy.
    """
    __abstract__ = True
