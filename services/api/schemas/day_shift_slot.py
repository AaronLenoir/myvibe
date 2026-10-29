from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import date

class DayShiftSlotCreate(BaseSchema):
    date: date = Field(..., description="Date of the shift slot")
    shift_type_id: uuid.UUID = Field(..., description="Shift type ID")
    min_staff: int = Field(1, ge=1, description="Minimum staff required")
    max_staff: int = Field(1, ge=1, description="Maximum staff allowed")

class DayShiftSlotRead(BaseSchema):
    id: uuid.UUID
    period_id: uuid.UUID
    date: date
    shift_type_id: uuid.UUID
    min_staff: int
    max_staff: int

class DayShiftSlotUpdate(BaseSchema):
    date: Optional[date] = Field(None, description="Date of the shift slot")
    shift_type_id: Optional[uuid.UUID] = Field(None, description="Shift type ID")
    min_staff: Optional[int] = Field(None, ge=1, description="Minimum staff required")
    max_staff: Optional[int] = Field(None, ge=1, description="Maximum staff allowed")
