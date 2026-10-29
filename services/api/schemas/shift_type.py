from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime, time

class ShiftTypeCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255, description="Shift type name")
    start_time: time = Field(..., description="Shift start time")
    end_time: time = Field(..., description="Shift end time")
    color: str = Field(..., min_length=1, max_length=50, description="Shift color")
    is_active: bool = Field(True, description="Whether shift type is active")

class ShiftTypeRead(BaseSchema):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    start_time: time
    end_time: time
    color: str
    is_active: bool
    created_at: datetime

class ShiftTypeUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Shift type name")
    start_time: Optional[time] = Field(None, description="Shift start time")
    end_time: Optional[time] = Field(None, description="Shift end time")
    color: Optional[str] = Field(None, min_length=1, max_length=50, description="Shift color")
    is_active: Optional[bool] = Field(None, description="Whether shift type is active")
