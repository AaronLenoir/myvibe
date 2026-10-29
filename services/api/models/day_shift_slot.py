from sqlalchemy import Column, Date, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class DayShiftSlot(Base):
    """Shift slots assigned to specific dates within a schedule period."""
    __tablename__ = "day_shift_slot"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_id = Column(UUID(as_uuid=True), ForeignKey("schedule_period.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    shift_type_id = Column(UUID(as_uuid=True), ForeignKey("shift_type.id"), nullable=False)
    min_staff = Column(Integer, nullable=False, default=1)
    max_staff = Column(Integer, nullable=False, default=1)
    
    # Relationships
    period = relationship("SchedulePeriod", backref="day_shift_slots")
    shift_type = relationship("ShiftType")
    
    __table_args__ = (
        UniqueConstraint("period_id", "date", "shift_type_id", name="uq_day_shift_slot"),
    )
    
    def __repr__(self):
        return f"<DayShiftSlot(id={self.id}, date={self.date}, shift={self.shift_type_id}, min={self.min_staff}, max={self.max_staff})>"
