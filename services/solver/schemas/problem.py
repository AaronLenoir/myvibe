from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time
from enum import Enum
import uuid

class ConstraintKind(str, Enum):
    VACATION = "vacation"
    UNAVAILABLE = "unavailable"
    PREFERENCE_AVOID = "preference_avoid"
    PREFERENCE_WANT = "preference_want"

class Member(BaseModel):
    """Member data for the solver."""
    id: str = Field(..., description="Member UUID")
    name: str = Field(..., description="Member name")

class Day(BaseModel):
    """Day data for the solver."""
    date: date = Field(..., description="Date of the day")

class ShiftSlot(BaseModel):
    """Shift slot data for the solver."""
    date: date = Field(..., description="Date of the shift")
    shift_type_id: str = Field(..., description="Shift type UUID")
    min_staff: int = Field(..., ge=1, description="Minimum staff required")
    max_staff: int = Field(..., ge=1, description="Maximum staff allowed")

class Constraint(BaseModel):
    """Constraint data for the solver."""
    id: str = Field(..., description="Constraint UUID")
    user_id: str = Field(..., description="User UUID")
    kind: ConstraintKind = Field(..., description="Constraint kind")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    shift_type_id: Optional[str] = Field(None, description="Shift type UUID (nullable)")
    hard: bool = Field(..., description="Whether this is a hard constraint")
    penalty: int = Field(0, ge=0, description="Penalty weight for soft constraints")

class Assignment(BaseModel):
    """Assignment in a proposal."""
    date: date = Field(..., description="Assignment date")
    shift_type_id: str = Field(..., description="Shift type UUID")
    user_id: str = Field(..., description="User UUID")

class Violation(BaseModel):
    """Violation data for a proposal."""
    constraint_id: str = Field(..., description="Constraint UUID that was violated")
    constraint_kind: str = Field(..., description="Kind of violated constraint")
    hard: bool = Field(..., description="Whether this was a hard constraint violation")
    user_id: Optional[str] = Field(None, description="User UUID")
    date: Optional[date] = Field(None, description="Date of violation")
    message: str = Field(..., description="Violation message")
    penalty: int = Field(0, ge=0, description="Penalty for this violation")

class Proposal(BaseModel):
    """A complete roster proposal."""
    id: str = Field(..., description="Proposal UUID")
    period_id: str = Field(..., description="Period UUID")
    assignments: List[Assignment] = Field(..., description="List of assignments")
    violations: List[Violation] = Field(default_factory=list, description="List of violations")
    soft_penalty_total: int = Field(0, ge=0, description="Total soft penalty score")
    hard_violation_count: int = Field(0, ge=0, description="Number of hard violations")
    status: str = Field("candidate", description="Proposal status")

class ProblemData(BaseModel):
    """Complete scheduling problem data."""
    period_id: str = Field(..., description="Period UUID")
    members: List[Member] = Field(..., description="List of members")
    days: List[Day] = Field(..., description="List of days in the period")
    shift_slots: List[ShiftSlot] = Field(..., description="List of shift slots")
    constraints: List[Constraint] = Field(..., description="List of constraints")
