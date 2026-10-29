from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class Team(Base):
    """Team model - tenancy root for multi-tenant support."""
    __tablename__ = "team"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"
