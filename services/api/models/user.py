from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class UserRole(str):
    MANAGER = "manager"
    MEMBER = "member"

class AuthProvider(str):
    GOOGLE = "google"
    FACEBOOK = "facebook"

class User(Base):
    """User model - team members with OAuth authentication."""
    __tablename__ = "user"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    avatar_url = Column(Text)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.MEMBER)
    auth_provider = Column(Enum(AuthProvider), nullable=False)
    provider_subject = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    
    # Relationships
    team = relationship("Team", backref="users")
    constraints = relationship("MemberConstraint", backref="user", foreign_keys="MemberConstraint.user_id")
    assignments = relationship("Assignment", backref="user", foreign_keys="Assignment.user_id")
    
    __table_args__ = (
        {
            "unique_constraints": [
                ("auth_provider", "provider_subject")
            ]
        },
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role={self.role})>"
