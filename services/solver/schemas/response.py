from pydantic import BaseModel, Field
from typing import List
from .problem import Proposal

class SolveResponse(BaseModel):
    """Response from the solve endpoint."""
    period_id: str = Field(..., description="Period UUID")
    proposals: List[Proposal] = Field(..., description="List of generated proposals")
    generation_time_ms: float = Field(..., description="Time taken to generate proposals in milliseconds")
    num_proposals: int = Field(..., description="Number of proposals generated")
