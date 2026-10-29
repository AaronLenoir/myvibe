from pydantic import BaseModel, Field
from typing import List
from datetime import date
from .problem import Assignment, Violation

class ValidationData(BaseModel):
    """Data for validating a roster."""
    proposal_id: str = Field(..., description="Proposal UUID")
    assignments: List[Assignment] = Field(..., description="List of assignments to validate")
    constraints: List[dict] = Field(..., description="List of constraints to validate against")

class ValidateResponse(BaseModel):
    """Response from validation."""
    proposal_id: str = Field(..., description="Proposal UUID")
    valid: bool = Field(..., description="Whether the roster is valid")
    hard_violation_count: int = Field(0, ge=0, description="Number of hard violations")
    soft_penalty_total: int = Field(0, ge=0, description="Total soft penalty score")
    violations: List[Violation] = Field(default_factory=list, description="List of violations")
    pass: bool = Field(..., description="Whether validation passed")
