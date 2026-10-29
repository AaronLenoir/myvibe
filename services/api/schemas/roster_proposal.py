from pydantic import Field
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime
from enum import Enum

class ProposalStatus(str, Enum):
    CANDIDATE = "candidate"
    SELECTED = "selected"

class RosterProposalRead(BaseSchema):
    id: uuid.UUID
    period_id: uuid.UUID
    created_at: datetime
    soft_penalty_total: int
    hard_violation_count: int
    status: ProposalStatus
