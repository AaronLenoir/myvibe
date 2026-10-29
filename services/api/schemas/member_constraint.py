from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime, date
from enum import Enum

class ConstraintKind(str, Enum):
    VACATION = "vacation"
    UNAVAILABLE = "unavailable"
    PREFERENCE_AVOID = "preference_avoid"
    PREFERENCE_WANT = "preference_want"

class MemberConstraintCreate(BaseSchema):
    period_id: uuid.UUID = Field(..., description="Period ID")
    kind: ConstraintKind = Field(..., description="Constraint kind")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    shift_type_id: Optional[uuid.UUID] = Field(None, description="Shift type ID (nullable)")
    note: Optional[str] = Field(None, description="Optional note")

class MemberConstraintRead(BaseSchema):
    id: uuid.UUID
    period_id: uuid.UUID
    user_id: uuid.UUID
    kind: ConstraintKind
    start_date: date
    end_date: date
    shift_type_id: Optional[uuid.UUID]
    note: Optional[str]
    created_at: datetime
