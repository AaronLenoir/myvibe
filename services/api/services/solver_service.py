import httpx
from typing import Optional, Any, dict, list
from ..config.settings import get_settings
from ..schemas.roster_proposal import RosterProposalRead
from ..schemas.assignment import AssignmentRead
from ..schemas.violation import ViolationRead
import logging
import json

logger = logging.getLogger(__name__)

class SolverService:
    """Service for communicating with the solver microservice."""
    
    def __init__(self):
        self.settings = get_settings()
        self.solver_url = self.settings.SOLVER_URL
    
    async def solve_problem(self, problem_data: dict) -> dict:
        """Send a scheduling problem to the solver and get proposals back."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.solver_url}/solve",
                    json=problem_data
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Solver HTTP error: {e}")
            raise Exception(f"Solver request failed: {e}")
        except Exception as e:
            logger.error(f"Solver connection error: {e}")
            raise Exception(f"Could not connect to solver: {e}")
    
    async def validate_roster(self, roster_data: dict) -> dict:
        """Validate a roster against constraints."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.solver_url}/validate",
                    json=roster_data
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Validation HTTP error: {e}")
            raise Exception(f"Validation request failed: {e}")
        except Exception as e:
            logger.error(f"Validation connection error: {e}")
            raise Exception(f"Could not connect to solver for validation: {e}")
    
    async def generate_proposals(
        self,
        members: list[dict],
        days: list[dict],
        shift_slots: list[dict],
        constraints: list[dict]
    ) -> list[dict]:
        """Generate roster proposals from scheduling problem data."""
        problem_data = {
            "members": members,
            "days": days,
            "shift_slots": shift_slots,
            "constraints": constraints
        }
        
        result = await self.solve_problem(problem_data)
        return result.get("proposals", [])
    
    async def check_health(self) -> bool:
        """Check if the solver service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.solver_url}/health")
                return response.status_code == 200
        except Exception:
            return False

# Global solver service instance
solver_service = SolverService()
