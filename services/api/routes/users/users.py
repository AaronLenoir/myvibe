from fastapi import APIRouter, Depends, HTTPException, status
from typing import list
from ...schemas.user import UserCreate, UserRead, UserUpdate, UserRole
from ...services.user_service import user_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.auth_service import auth_service
from fastapi.security import HTTPBearer
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

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

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user."""
    try:
        # For MVP, use the current user's team
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current user not found"
            )
        
        new_user = await user_service.create_user(db, user_data, user.team_id)
        logger.info(f"User created: {new_user.id}")
        return new_user
    except Exception as e:
        logger.error(f"Create user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/team", response_model=list[UserRead], summary="List team users")
async def list_team_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all users in the current user's team."""
    try:
        user = await user_service.get_user(db, current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Current user not found"
            )
        
        users = await user_service.get_users_by_team(db, user.team_id)
        return users
    except Exception as e:
        logger.error(f"List team users failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserRead, summary="Get user")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user."""
    try:
        user = await user_service.get_user(db, uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=UserRead, summary="Update user")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a user."""
    try:
        # Check if current user can update this user (manager can update anyone, users can update themselves)
        current_user_obj = await user_service.get_user(db, current_user.user_id)
        target_user = await user_service.get_user(db, uuid.UUID(user_id))
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if current_user_obj.id != uuid.UUID(user_id) and current_user_obj.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can update other users"
            )
        
        updated_user = await user_service.update_user(db, uuid.UUID(user_id), user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except Exception as e:
        logger.error(f"Update user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user."""
    try:
        # Only managers can delete users
        current_user_obj = await user_service.get_user(db, current_user.user_id)
        if current_user_obj.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can delete users"
            )
        
        success = await user_service.delete_user(db, uuid.UUID(user_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return None
    except Exception as e:
        logger.error(f"Delete user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{user_id}/promote", response_model=UserRead, summary="Promote user to manager")
async def promote_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Promote a user to manager."""
    try:
        # Only managers can promote users
        current_user_obj = await user_service.get_user(db, current_user.user_id)
        if current_user_obj.role != UserRole.MANAGER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only managers can promote users"
            )
        
        # Update user role to manager
        user_data = UserUpdate(role=UserRole.MANAGER)
        updated_user = await user_service.update_user(db, uuid.UUID(user_id), user_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User promoted to manager: {user_id}")
        return updated_user
    except Exception as e:
        logger.error(f"Promote user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
