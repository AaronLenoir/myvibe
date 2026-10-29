from sqlalchemy import Column, Date, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class ConstraintKind(str):
    VACATION = "vacation"
    UNAVAILABLE = "unavailable"
    PREFERENCE_AVOID = "preference_avoid"
    PREFERENCE_WANT = "preference_want"

class MemberConstraint(Base):
    """Member constraints including vacations, unavailability, and preferences."""
    __tablename__ = "member_constraint"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_id = Column(UUID(as_uuid=True), ForeignKey("schedule_period.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    kind = Column(Enum(ConstraintKind), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    shift_type_id = Column(UUID(as_uuid=True), ForeignKey("shift_type.id", ondelete="SET NULL"))
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    
    # Relationships
    period = relationship("SchedulePeriod")
    user = relationship("User")
    shift_type = relationship("ShiftType")
    
    def __repr__(self):
        return f"<MemberConstraint(id={self.id}, user={self.user_id}, kind={self.kind}, start={self.start_date}, end={self.end_date})>"
    
    @property
    def is_hard(self) -> bool:
        """Hard constraints cannot be violated."""
        return self.kind in [ConstraintKind.VACATION, ConstraintKind.UNAVAILABLE]
    
    @property
    def is_soft(self) -> bool:
        """Soft constraints can be violated with penalty."""
        return self.kind in [ConstraintKind.PREFERENCE_AVOID, ConstraintKind.PREFERENCE_WANT]
