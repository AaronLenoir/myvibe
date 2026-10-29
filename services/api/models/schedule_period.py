from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base

class PeriodStatus(str):
    DRAFT = "draft"
    COLLECTING_WISHES = "collecting_wishes"
    SOLVING = "solving"
    PROPOSED = "proposed"
    PUBLISHED = "published"

class SchedulePeriod(Base):
    """Schedule period representing a weekly or monthly roster period."""
    __tablename__ = "schedule_period"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(PeriodStatus), nullable=False, default=PeriodStatus.DRAFT)
    created_at = Column(DateTime(timezone=True), server_default="now()")
    
    # Relationships
    team = relationship("Team", backref="schedule_periods")
    day_shift_slots = relationship("DayShiftSlot", backref="period", foreign_keys="DayShiftSlot.period_id")
    member_constraints = relationship("MemberConstraint", backref="period", foreign_keys="MemberConstraint.period_id")
    roster_proposals = relationship("RosterProposal", backref="period", foreign_keys="RosterProposal.period_id")
    
    def __repr__(self):
        return f"<SchedulePeriod(id={self.id}, start={self.start_date}, end={self.end_date}, status={self.status})>"
