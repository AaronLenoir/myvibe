from fastapi import APIRouter, Depends, HTTPException, status
from typing import list
from ...schemas.shift_type import ShiftTypeCreate, ShiftTypeRead, ShiftTypeUpdate
from ...services.shift_type_service import shift_type_service
from ...services.user_service import user_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.auth_service import auth_service
from fastapi.security import HTTPBearer
from ...models.user import UserRole
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shift-types", tags=["shift_types"])

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

@router.post("", response_model=ShiftTypeRead, status_code=status.HTTP_201_CREATED, summary="Create shift type")
async def create_shift_type(
    shift_type_data: ShiftTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new shift type."""
    try:
        user = await check_manager(db, current_user)
        shift_type = await shift_type_service.create_shift_type(
            db, shift_type_data, user.team_id
        )
        logger.info(f"Shift type created: {shift_type.id}")
        return shift_type
    except Exception as e:
        logger.error(f"Create shift type failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=list[ShiftTypeRead], summary="List shift types")
async def list_shift_types(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all shift types for the current user's team."""
    try:
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        shift_types = await shift_type_service.get_active_shift_types_by_team(db, user.team_id)
        return shift_types
    except Exception as e:
        logger.error(f"List shift types failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{shift_type_id}", response_model=ShiftTypeRead, summary="Get shift type")
async def get_shift_type(
    shift_type_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific shift type."""
    try:
        shift_type = await shift_type_service.get_shift_type(db, uuid.UUID(shift_type_id))
        if not shift_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        # Check if user has access to this shift type (same team)
        user = await user_service.get_user(db, current_user.user_id)
        if shift_type.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return shift_type
    except Exception as e:
        logger.error(f"Get shift type failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{shift_type_id}", response_model=ShiftTypeRead, summary="Update shift type")
async def update_shift_type(
    shift_type_id: str,
    shift_type_data: ShiftTypeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a shift type."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if shift type exists and belongs to user's team
        existing_shift_type = await shift_type_service.get_shift_type(db, uuid.UUID(shift_type_id))
        if not existing_shift_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        if existing_shift_type.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        updated_shift_type = await shift_type_service.update_shift_type(
            db, uuid.UUID(shift_type_id), shift_type_data
        )
        if not updated_shift_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        return updated_shift_type
    except Exception as e:
        logger.error(f"Update shift type failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{shift_type_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete shift type")
async def delete_shift_type(
    shift_type_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a shift type."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if shift type exists and belongs to user's team
        existing_shift_type = await shift_type_service.get_shift_type(db, uuid.UUID(shift_type_id))
        if not existing_shift_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        if existing_shift_type.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        success = await shift_type_service.delete_shift_type(db, uuid.UUID(shift_type_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        return None
    except Exception as e:
        logger.error(f"Delete shift type failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{shift_type_id}/deactivate", response_model=ShiftTypeRead, summary="Deactivate shift type")
async def deactivate_shift_type(
    shift_type_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a shift type."""
    try:
        user = await check_manager(db, current_user)
        
        # Check if shift type exists and belongs to user's team
        existing_shift_type = await shift_type_service.get_shift_type(db, uuid.UUID(shift_type_id))
        if not existing_shift_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        if existing_shift_type.team_id != user.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        updated_shift_type = await shift_type_service.update_shift_type(
            db, uuid.UUID(shift_type_id), ShiftTypeUpdate(is_active=False)
        )
        
        if not updated_shift_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shift type not found"
            )
        
        logger.info(f"Shift type deactivated: {shift_type_id}")
        return updated_shift_type
    except Exception as e:
        logger.error(f"Deactivate shift type failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
