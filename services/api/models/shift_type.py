from sqlalchemy import Column, String, Time, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class ShiftType(Base):
    """Shift type definitions with start/end times and colors."""
    __tablename__ = "shift_type"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    color = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    
    # Relationships
    team = relationship("Team", backref="shift_types")
    day_shift_slots = relationship("DayShiftSlot", backref="shift_type", foreign_keys="DayShiftSlot.shift_type_id")
    member_constraints = relationship("MemberConstraint", backref="shift_type", foreign_keys="MemberConstraint.shift_type_id")
    assignments = relationship("Assignment", backref="shift_type", foreign_keys="Assignment.shift_type_id")
    
    def __repr__(self):
        return f"<ShiftType(id={self.id}, name='{self.name}', start={self.start_time}, end={self.end_time})>"
