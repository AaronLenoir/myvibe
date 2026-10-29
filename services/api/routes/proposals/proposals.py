from fastapi import APIRouter, Depends, HTTPException, status
from typing import list
from datetime import date
from ...schemas.roster_proposal import RosterProposalRead, ProposalStatus
from ...schemas.assignment import AssignmentRead, AssignmentCreate
from ...schemas.violation import ViolationRead
from ...services.proposal_service import proposal_service
from ...services.user_service import user_service
from ...services.schedule_period_service import schedule_period_service
from ...services.solver_service import solver_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.auth_service import auth_service
from fastapi.security import HTTPBearer
from ...models.user import UserRole
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["roster_proposals"])

http_bearer = HTTPBearer()

async def get_db():
    """Get database session."""
    async with database.get_session() as session:
        yield session

async def get_current_user(token: str = Depends(HTTPBearer())):
    """Get current user from token."""
    if token.credentials:
        token_data = auth_service.decode_access_token(token.credentials)
        if token_data and token_data.user_id:
            return token_data
    raise HTTPException(status_code=401, detail="Invalid token")

async def check_manager(db: AsyncSession, current_user: dict):
    """Check if current user is a manager."""
    user = await user_service.get_user(db, current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can perform this action"
        )
    return user

@router.post("/generate/{period_id}", response_model=list[RosterProposalRead], summary="Generate proposals")
async def generate_proposals(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate roster proposals for a schedule period."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if period exists and belongs to user's team
        period = await schedule_period_service.get_period_with_details(db, uuid.UUID(period_id))
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if period is in solving status
        if period.status != "solving":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Period must be in solving status to generate proposals"
            )
        
        # Check if solver is available
        solver_healthy = await solver_service.check_health()
        if not solver_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Solver service is not available"
            )
        
        # Prepare problem data for solver
        problem_data = {
            "period_id": str(period_id),
            "members": [],
            "days": [],
            "shift_slots": [],
            "constraints": []
        }
        
        # Get all users in the team
        team_users = await user_service.get_users_by_team(db, user.team_id)
        for team_user in team_users:
            problem_data["members"].append({
                "id": str(team_user.id),
                "name": team_user.name
            })
        
        # Get all days in the period
        from ...services.day_shift_slot_service import day_shift_slot_service
        slots = await day_shift_slot_service.get_slots_by_period(db, uuid.UUID(period_id))
        
        # Extract unique dates
        unique_dates = set(slot.date for slot in slots)
        for date_val in sorted(unique_dates):
            problem_data["days"].append({
                "date": date_val.isoformat()
            })
        
        # Add shift slots
        for slot in slots:
            problem_data["shift_slots"].append({
                "date": slot.date.isoformat(),
                "shift_type_id": str(slot.shift_type_id),
                "min_staff": slot.min_staff,
                "max_staff": slot.max_staff
            })
        
        # Add constraints
        from ...services.constraint_service import constraint_service
        constraints = await constraint_service.get_constraints_by_period(db, uuid.UUID(period_id))
        for constraint in constraints:
            problem_data["constraints"].append({
                "id": str(constraint.id),
                "user_id": str(constraint.user_id),
                "kind": constraint.kind,
                "start_date": constraint.start_date.isoformat(),
                "end_date": constraint.end_date.isoformat(),
                "shift_type_id": str(constraint.shift_type_id) if constraint.shift_type_id else None,
                "hard": constraint.is_hard,
                "penalty": 1 if constraint.is_soft else 0
            })
        
        # Call solver
        solver_response = await solver_service.solve_problem(problem_data)
        
        # Create proposals from solver response
        proposals = await proposal_service.generate_proposals_from_solver(
            db, uuid.UUID(period_id), solver_response
        )
        
        logger.info(f"Generated {len(proposals)} proposals for period: {period_id}")
        return proposals
    except Exception as e:
        logger.error(f"Generate proposals failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/period/{period_id}", response_model=list[RosterProposalRead], summary="List proposals by period")
async def list_proposals_by_period(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all proposals for a schedule period."""
    try:
        # Check if period exists and user has access
        period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        # Check if user has access to this period (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        proposals = await proposal_service.get_proposals_by_period(db, uuid.UUID(period_id))
        return proposals
    except Exception as e:
        logger.error(f"List proposals by period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{proposal_id}", response_model=RosterProposalRead, summary="Get proposal")
async def get_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific proposal with all details."""
    try:
        proposal = await proposal_service.get_proposal_with_details(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get period to check team
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return proposal
    except Exception as e:
        logger.error(f"Get proposal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/period/{period_id}/selected", response_model=RosterProposalRead | None, summary="Get selected proposal")
async def get_selected_proposal(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the selected proposal for a period."""
    try:
        # Check if period exists and user has access
        period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        # Check if user has access to this period (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        proposal = await proposal_service.get_selected_proposal(db, uuid.UUID(period_id))
        return proposal
    except Exception as e:
        logger.error(f"Get selected proposal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{proposal_id}/select", response_model=RosterProposalRead, summary="Select proposal")
async def select_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Select a proposal as the chosen one for its period."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if proposal exists
        proposal = await proposal_service.get_proposal(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        selected_proposal = await proposal_service.select_proposal(db, uuid.UUID(proposal_id))
        if not selected_proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        logger.info(f"Selected proposal: {proposal_id}")
        return selected_proposal
    except Exception as e:
        logger.error(f"Select proposal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{proposal_id}/assignments", response_model=list[AssignmentRead], summary="List assignments")
async def list_assignments(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all assignments for a proposal."""
    try:
        proposal = await proposal_service.get_proposal(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get period to check team
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        assignments = await proposal_service.get_assignments_by_proposal(db, uuid.UUID(proposal_id))
        return assignments
    except Exception as e:
        logger.error(f"List assignments failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{proposal_id}/violations", response_model=list[ViolationRead], summary="List violations")
async def list_violations(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all violations for a proposal."""
    try:
        proposal = await proposal_service.get_proposal(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get period to check team
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        violations = await proposal_service.get_violations_by_proposal(db, uuid.UUID(proposal_id))
        return violations
    except Exception as e:
        logger.error(f"List violations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{proposal_id}/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED, summary="Add assignment")
async def add_assignment(
    proposal_id: str,
    assignment: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add an assignment to a proposal."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if proposal exists
        proposal = await proposal_service.get_proposal(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if period is in proposed status (editable)
        if period.status != "proposed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proposal can only be edited when period is in proposed status"
            )
        
        new_assignment = await proposal_service.add_assignment(db, assignment)
        logger.info(f"Added assignment: {new_assignment.id}")
        return new_assignment
    except Exception as e:
        logger.error(f"Add assignment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove assignment")
async def remove_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove an assignment from a proposal."""
    try:
        user = await check_manager(db, current_user)
        
        # Get assignment to check proposal
        assignment = await proposal_service.get_assignment_by_id(db, uuid.UUID(assignment_id))
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Check if user has access to this assignment's proposal (same team)
        period = await schedule_period_service.get_schedule_period(db, assignment.proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if period is in proposed status (editable)
        if period.status != "proposed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proposal can only be edited when period is in proposed status"
            )
        
        success = await proposal_service.remove_assignment(db, uuid.UUID(assignment_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        return None
    except Exception as e:
        logger.error(f"Remove assignment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{proposal_id}/validate", response_model=dict, summary="Validate proposal")
async def validate_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Validate a proposal against constraints."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if proposal exists
        proposal = await proposal_service.get_proposal_with_details(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Prepare validation data
        validation_data = {
            "proposal_id": str(proposal_id),
            "assignments": [
                {
                    "date": a.date.isoformat(),
                    "shift_type_id": str(a.shift_type_id),
                    "user_id": str(a.user_id)
                }
                for a in proposal.assignments
            ],
            "constraints": []
        }
        
        # Add constraints for this period
        from ...services.constraint_service import constraint_service
        constraints = await constraint_service.get_constraints_by_period(db, proposal.period_id)
        for constraint in constraints:
            validation_data["constraints"].append({
                "id": str(constraint.id),
                "user_id": str(constraint.user_id),
                "kind": constraint.kind,
                "start_date": constraint.start_date.isoformat(),
                "end_date": constraint.end_date.isoformat(),
                "shift_type_id": str(constraint.shift_type_id) if constraint.shift_type_id else None,
                "hard": constraint.is_hard,
                "penalty": 1 if constraint.is_soft else 0
            })
        
        # Call solver for validation
        validation_result = await solver_service.validate_roster(validation_data)
        
        return validation_result
    except Exception as e:
        logger.error(f"Validate proposal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{proposal_id}/publish", response_model=RosterProposalRead, summary="Publish proposal")
async def publish_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Publish a proposal (advance period to published status)."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if proposal exists
        proposal = await proposal_service.get_proposal(db, uuid.UUID(proposal_id))
        if not proposal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proposal not found"
            )
        
        # Check if user has access to this proposal (same team)
        period = await schedule_period_service.get_schedule_period(db, proposal.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if this is the selected proposal
        selected_proposal = await proposal_service.get_selected_proposal(db, proposal.period_id)
        if not selected_proposal or selected_proposal.id != proposal.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only the selected proposal can be published"
            )
        
        # Advance period to published status
        updated_period = await schedule_period_service.advance_period_status(db, proposal.period_id)
        if not updated_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Period not found"
            )
        
        logger.info(f"Published proposal: {proposal_id}")
        return proposal
    except Exception as e:
        logger.error(f"Publish proposal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
