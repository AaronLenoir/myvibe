from sqlalchemy import Column, String, Boolean, Text, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class Violation(Base):
    """Constraint violations for proposals."""
    __tablename__ = "violation"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("roster_proposal.id", ondelete="CASCADE"), nullable=False)
    constraint_kind = Column(String(50), nullable=False)
    hard = Column(Boolean, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"))
    date = Column(Date)
    message = Column(Text, nullable=False)
    penalty = Column(Integer, nullable=False, default=0)
    
    # Relationships
    proposal = relationship("RosterProposal")
    user = relationship("User")
    
    def __repr__(self):
        return f"<Violation(id={self.id}, proposal={self.proposal_id}, kind='{self.constraint_kind}', hard={self.hard}, penalty={self.penalty})>"
