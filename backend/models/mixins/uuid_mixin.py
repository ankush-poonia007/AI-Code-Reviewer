import uuid
from sqlalchemy import Column, String

class UUIDMixin:
    """
    Decoupled SQLAlchemy Mixin providing a secure, 36-character 
    UUID v4 primary identity key for relational models.
    """
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
