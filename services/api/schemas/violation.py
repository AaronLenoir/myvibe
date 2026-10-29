from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import date

class ViolationRead(BaseSchema):
    id: uuid.UUID
    proposal_id: uuid.UUID
    constraint_kind: str
    hard: bool
    user_id: Optional[uuid.UUID]
    date: Optional[date]
    message: str
    penalty: int
