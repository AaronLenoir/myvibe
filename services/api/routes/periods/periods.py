from fastapi import APIRouter, Depends, HTTPException, status
from typing import list
from datetime import date
from ...schemas.schedule_period import SchedulePeriodCreate, SchedulePeriodRead, SchedulePeriodUpdate, PeriodStatus
from ...services.schedule_period_service import schedule_period_service
from ...services.user_service import user_service
from ...services.day_shift_slot_service import day_shift_slot_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.auth_service import auth_service
from fastapi.security import HTTPBearer
from ...models.user import UserRole
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/periods", tags=["schedule_periods"])

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

@router.post("", response_model=SchedulePeriodRead, status_code=status.HTTP_201_CREATED, summary="Create schedule period")
async def create_period(
    period_data: SchedulePeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new schedule period."""
    try:
        user = await check_manager(db, current_user)
        
        # Validate dates
        if period_data.start_date > period_data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
        
        period = await schedule_period_service.create_schedule_period(
            db, period_data, user.team_id
        )
        logger.info(f"Schedule period created: {period.id}")
        return period
    except Exception as e:
        logger.error(f"Create schedule period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=list[SchedulePeriodRead], summary="List schedule periods")
async def list_periods(
    status: PeriodStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all schedule periods for the current user's team."""
    try:
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        periods = await schedule_period_service.get_schedule_periods_by_team(db, user.team_id)
        
        # Filter by status if provided
        if status:
            periods = [p for p in periods if p.status == status]
        
        return periods
    except Exception as e:
        logger.error(f"List schedule periods failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/current", response_model=SchedulePeriodRead | None, summary="Get current period")
async def get_current_period(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the current active schedule period."""
    try:
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        period = await schedule_period_service.get_current_period(db, user.team_id)
        return period
    except Exception as e:
        logger.error(f"Get current period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/upcoming", response_model=list[SchedulePeriodRead], summary="Get upcoming periods")
async def get_upcoming_periods(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming schedule periods."""
    try:
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        periods = await schedule_period_service.get_upcoming_periods(db, user.team_id)
        return periods
    except Exception as e:
        logger.error(f"Get upcoming periods failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{period_id}", response_model=SchedulePeriodRead, summary="Get schedule period")
async def get_period(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific schedule period."""
    try:
        period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        # Check if user has access to this period (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return period
    except Exception as e:
        logger.error(f"Get schedule period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{period_id}/details", response_model=SchedulePeriodRead, summary="Get period with details")
async def get_period_details(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a schedule period with all related data."""
    try:
        period = await schedule_period_service.get_period_with_details(db, uuid.UUID(period_id))
        if not period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        # Check if user has access to this period (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return period
    except Exception as e:
        logger.error(f"Get schedule period details failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{period_id}", response_model=SchedulePeriodRead, summary="Update schedule period")
async def update_period(
    period_id: str,
    period_data: SchedulePeriodUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a schedule period."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if period exists and belongs to user's team
        existing_period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not existing_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        if existing_period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Validate dates if provided
        if period_data.start_date and period_data.end_date:
            if period_data.start_date > period_data.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date must be before end date"
                )
        
        updated_period = await schedule_period_service.update_schedule_period(
            db, uuid.UUID(period_id), period_data
        )
        if not updated_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        return updated_period
    except Exception as e:
        logger.error(f"Update schedule period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete schedule period")
async def delete_period(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a schedule period."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if period exists and belongs to user's team
        existing_period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not existing_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        if existing_period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = await schedule_period_service.delete_schedule_period(db, uuid.UUID(period_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        return None
    except Exception as e:
        logger.error(f"Delete schedule period failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{period_id}/advance", response_model=SchedulePeriodRead, summary="Advance period status")
async def advance_period_status(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Advance the status of a schedule period."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if period exists and belongs to user's team
        existing_period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not existing_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        if existing_period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        updated_period = await schedule_period_service.advance_period_status(db, uuid.UUID(period_id))
        if not updated_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        logger.info(f"Advanced period status: {period_id}")
        return updated_period
    except Exception as e:
        logger.error(f"Advance period status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{period_id}/regress", response_model=SchedulePeriodRead, summary="Regress period status")
async def regress_period_status(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Regress the status of a schedule period."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if period exists and belongs to user's team
        existing_period = await schedule_period_service.get_schedule_period(db, uuid.UUID(period_id))
        if not existing_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        if existing_period.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        updated_period = await schedule_period_service.regress_period_status(db, uuid.UUID(period_id))
        if not updated_period:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule period not found"
            )
        
        logger.info(f"Regressed period status: {period_id}")
        return updated_period
    except Exception as e:
        logger.error(f"Regress period status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
