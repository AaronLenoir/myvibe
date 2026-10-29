from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime

class TeamCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255, description="Team name")

class TeamRead(BaseSchema):
    id: uuid.UUID
    name: str
    created_at: datetime

class TeamUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Team name")
