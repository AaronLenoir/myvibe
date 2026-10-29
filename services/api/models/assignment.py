from sqlalchemy import Column, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class Assignment(Base):
    """Individual assignments of users to shifts in a proposal."""
    __tablename__ = "assignment"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("roster_proposal.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    shift_type_id = Column(UUID(as_uuid=True), ForeignKey("shift_type.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    
    # Relationships
    proposal = relationship("RosterProposal")
    user = relationship("User")
    shift_type = relationship("ShiftType")
    
    __table_args__ = (
        UniqueConstraint("proposal_id", "date", "shift_type_id", "user_id", name="uq_assignment"),
    )
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, proposal={self.proposal_id}, user={self.user_id}, date={self.date}, shift={self.shift_type_id})>"
