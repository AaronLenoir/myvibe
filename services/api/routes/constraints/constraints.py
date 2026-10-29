from fastapi import APIRouter, Depends, HTTPException, status
from typing import list
from datetime import date
from ...schemas.member_constraint import MemberConstraintCreate, MemberConstraintRead, ConstraintKind
from ...services.constraint_service import constraint_service
from ...services.user_service import user_service
from ...services.schedule_period_service import schedule_period_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.auth_service import auth_service
from fastapi.security import HTTPBearer
from ...models.user import UserRole
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/constraints", tags=["member_constraints"])

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

@router.post("", response_model=MemberConstraintRead, status_code=status.HTTP_201_CREATED, summary="Create constraint")
async def create_constraint(
    constraint_data: MemberConstraintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new member constraint."""
    try:
        # Check if period exists and user has access
        period = await schedule_period_service.get_schedule_period(db, constraint_data.period_id)
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
        
        # Check if period is in collecting_wishes status
        if period.status != "collecting_wishes":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Constraints can only be submitted during the collecting_wishes phase"
            )
        
        constraint = await constraint_service.create_constraint(
            db, constraint_data, user.id
        )
        logger.info(f"Constraint created: {constraint.id}")
        return constraint
    except Exception as e:
        logger.error(f"Create constraint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/period/{period_id}", response_model=list[MemberConstraintRead], summary="List constraints by period")
async def list_constraints_by_period(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all constraints for a schedule period."""
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
        
        constraints = await constraint_service.get_constraints_by_period(db, uuid.UUID(period_id))
        return constraints
    except Exception as e:
        logger.error(f"List constraints by period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user", response_model=list[MemberConstraintRead], summary="List constraints by current user")
async def list_constraints_by_user(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all constraints for the current user."""
    try:
        constraints = await constraint_service.get_constraints_by_user(db, current_user.user_id)
        return constraints
    except Exception as e:
        logger.error(f"List constraints by user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/user/{user_id}", response_model=list[MemberConstraintRead], summary="List constraints by user")
async def list_constraints_for_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all constraints for a specific user (managers only)."""
    try:
        # Check if current user is a manager
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can view other users' constraints"
            )
        
        constraints = await constraint_service.get_constraints_by_user(db, uuid.UUID(user_id))
        return constraints
    except Exception as e:
        logger.error(f"List constraints for user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{constraint_id}", response_model=MemberConstraintRead, summary="Get constraint")
async def get_constraint(
    constraint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific constraint."""
    try:
        constraint = await constraint_service.get_constraint(db, uuid.UUID(constraint_id))
        if not constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constraint not found"
            )
        
        # Check if user has access to this constraint (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get period to check team
        period = await schedule_period_service.get_schedule_period(db, constraint.period_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return constraint
    except Exception as e:
        logger.error(f"Get constraint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{constraint_id}", response_model=MemberConstraintRead, summary="Update constraint")
async def update_constraint(
    constraint_id: str,
    constraint_data: MemberConstraintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a constraint."""
    try:
        constraint = await constraint_service.get_constraint(db, uuid.UUID(constraint_id))
        if not constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constraint not found"
            )
        
        # Check if user owns this constraint or is a manager
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if constraint.user_id != user.id and user.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only constraint owner or manager can update this constraint"
            )
        
        # Check if period is in collecting_wishes status
        period = await schedule_period_service.get_schedule_period(db, constraint.period_id)
        if period.status != "collecting_wishes":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Constraints can only be updated during the collecting_wishes phase"
            )
        
        updated_constraint = await constraint_service.update_constraint(
            db, uuid.UUID(constraint_id), constraint_data
        )
        if not updated_constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constraint not found"
            )
        
        return updated_constraint
    except Exception as e:
        logger.error(f"Update constraint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{constraint_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete constraint")
async def delete_constraint(
    constraint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a constraint."""
    try:
        constraint = await constraint_service.get_constraint(db, uuid.UUID(constraint_id))
        if not constraint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constraint not found"
            )
        
        # Check if user owns this constraint or is a manager
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if constraint.user_id != user.id and user.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only constraint owner or manager can delete this constraint"
            )
        
        # Check if period is in collecting_wishes status
        period = await schedule_period_service.get_schedule_period(db, constraint.period_id)
        if period.status != "collecting_wishes":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Constraints can only be deleted during the collecting_wishes phase"
            )
        
        success = await constraint_service.delete_constraint(db, uuid.UUID(constraint_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constraint not found"
            )
        
        return None
    except Exception as e:
        logger.error(f"Delete constraint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/period/{period_id}/hard", response_model=list[MemberConstraintRead], summary="List hard constraints")
async def list_hard_constraints(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all hard constraints for a period."""
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
        
        constraints = await constraint_service.get_hard_constraints_by_period(db, uuid.UUID(period_id))
        return constraints
    except Exception as e:
        logger.error(f"List hard constraints failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/period/{period_id}/soft", response_model=list[MemberConstraintRead], summary="List soft constraints")
async def list_soft_constraints(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all soft constraints for a period."""
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
        
        constraints = await constraint_service.get_soft_constraints_by_period(db, uuid.UUID(period_id))
        return constraints
    except Exception as e:
        logger.error(f"List soft constraints failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
