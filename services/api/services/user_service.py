from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from sqlalchemy.orm import joinedload
from ..models.user import User, UserRole
from ..models.team import Team
from ..schemas.user import UserCreate, UserRead, UserUpdate
import uuid
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users."""
    
    def __init__(self):
        pass
    
    async def create_user(self, session: AsyncSession, user_data: UserCreate, team_id: uuid.UUID) -> UserRead:
        """Create a new user."""
        # Check if user with same provider and subject already exists
        result = await session.execute(
            select(User).where(
                User.auth_provider == user_data.auth_provider,
                User.provider_subject == user_data.provider_subject
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.info(f"User already exists: {existing_user.id}")
            return UserRead.model_validate(existing_user)
        
        user = User(
            **user_data.model_dump(),
            team_id=team_id
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Created user: {user.id}")
        return UserRead.model_validate(user)
    
    async def get_user(self, session: AsyncSession, user_id: uuid.UUID) -> Optional[UserRead]:
        """Get a user by ID."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            return UserRead.model_validate(user)
        return None
    
    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[UserRead]:
        """Get a user by email."""
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if user:
            return UserRead.model_validate(user)
        return None
    
    async def get_user_by_provider(self, session: AsyncSession, provider: str, subject: str) -> Optional[UserRead]:
        """Get a user by auth provider and subject."""
        result = await session.execute(
            select(User).where(
                User.auth_provider == provider,
                User.provider_subject == subject
            )
        )
        user = result.scalar_one_or_none()
        if user:
            return UserRead.model_validate(user)
        return None
    
    async def get_users_by_team(self, session: AsyncSession, team_id: uuid.UUID) -> list[UserRead]:
        """Get all users in a team."""
        result = await session.execute(
            select(User).where(User.team_id == team_id)
        )
        users = result.scalars().all()
        return [UserRead.model_validate(user) for user in users]
    
    async def update_user(self, session: AsyncSession, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[UserRead]:
        """Update a user."""
        result = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**user_data.model_dump(exclude_unset=True))
            .returning(User)
        )
        user = result.scalar_one_or_none()
        if user:
            await session.commit()
            return UserRead.model_validate(user)
        return None
    
    async def delete_user(self, session: AsyncSession, user_id: uuid.UUID) -> bool:
        """Delete a user."""
        result = await session.execute(
            delete(User).where(User.id == user_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted user: {user_id}")
            return True
        return False
    
    async def get_first_user_or_create_manager(self, session: AsyncSession, team_id: uuid.UUID, user_data: UserCreate) -> UserRead:
        """Get first user or create a manager if no users exist."""
        result = await session.execute(
            select(User).where(User.team_id == team_id).limit(1)
        )
        first_user = result.scalar_one_or_none()
        
        if not first_user:
            # Create first user as manager
            user = User(
                **user_data.model_dump(),
                team_id=team_id,
                role=UserRole.MANAGER
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created first user as manager: {user.id}")
            return UserRead.model_validate(user)
        
        # Check if any user is a manager
        result = await session.execute(
            select(User).where(
                User.team_id == team_id,
                User.role == UserRole.MANAGER
            ).limit(1)
        )
        manager = result.scalar_one_or_none()
        
        if not manager:
            # Promote first user to manager
            first_user.role = UserRole.MANAGER
            await session.commit()
            logger.info(f"Promoted first user to manager: {first_user.id}")
        
        return UserRead.model_validate(first_user)

# Global user service instance
user_service = UserService()
