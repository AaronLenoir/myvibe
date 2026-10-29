from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import date

class AssignmentCreate(BaseSchema):
    proposal_id: uuid.UUID = Field(..., description="Proposal ID")
    date: date = Field(..., description="Assignment date")
    shift_type_id: uuid.UUID = Field(..., description="Shift type ID")
    user_id: uuid.UUID = Field(..., description="User ID")

class AssignmentRead(BaseSchema):
    id: uuid.UUID
    proposal_id: uuid.UUID
    date: date
    shift_type_id: uuid.UUID
    user_id: uuid.UUID
