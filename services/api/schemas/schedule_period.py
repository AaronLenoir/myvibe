from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime, date
from enum import Enum

class PeriodStatus(str, Enum):
    DRAFT = "draft"
    COLLECTING_WISHES = "collecting_wishes"
    SOLVING = "solving"
    PROPOSED = "proposed"
    PUBLISHED = "published"

class SchedulePeriodCreate(BaseSchema):
    start_date: date = Field(..., description="Period start date")
    end_date: date = Field(..., description="Period end date")
    status: PeriodStatus = Field(PeriodStatus.DRAFT, description="Period status")

class SchedulePeriodRead(BaseSchema):
    id: uuid.UUID
    team_id: uuid.UUID
    start_date: date
    end_date: date
    status: PeriodStatus
    created_at: datetime

class SchedulePeriodUpdate(BaseSchema):
    start_date: Optional[date] = Field(None, description="Period start date")
    end_date: Optional[date] = Field(None, description="Period end date")
    status: Optional[PeriodStatus] = Field(None, description="Period status")
