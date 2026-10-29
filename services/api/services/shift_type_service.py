from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from ..models.shift_type import ShiftType
from ..schemas.shift_type import ShiftTypeCreate, ShiftTypeRead, ShiftTypeUpdate
import uuid
import logging

logger = logging.getLogger(__name__)

class ShiftTypeService:
    """Service for managing shift types."""
    
    def __init__(self):
        pass
    
    async def create_shift_type(self, session: AsyncSession, shift_type_data: ShiftTypeCreate, team_id: uuid.UUID) -> ShiftTypeRead:
        """Create a new shift type."""
        shift_type = ShiftType(
            **shift_type_data.model_dump(),
            team_id=team_id
        )
        session.add(shift_type)
        await session.commit()
        await session.refresh(shift_type)
        logger.info(f"Created shift type: {shift_type.id}")
        return ShiftTypeRead.model_validate(shift_type)
    
    async def get_shift_type(self, session: AsyncSession, shift_type_id: uuid.UUID) -> Optional[ShiftTypeRead]:
        """Get a shift type by ID."""
        result = await session.execute(
            select(ShiftType).where(ShiftType.id == shift_type_id)
        )
        shift_type = result.scalar_one_or_none()
        if shift_type:
            return ShiftTypeRead.model_validate(shift_type)
        return None
    
    async def get_shift_types_by_team(self, session: AsyncSession, team_id: uuid.UUID) -> list[ShiftTypeRead]:
        """Get all shift types for a team."""
        result = await session.execute(
            select(ShiftType).where(ShiftType.team_id == team_id)
        )
        shift_types = result.scalars().all()
        return [ShiftTypeRead.model_validate(st) for st in shift_types]
    
    async def get_active_shift_types_by_team(self, session: AsyncSession, team_id: uuid.UUID) -> list[ShiftTypeRead]:
        """Get all active shift types for a team."""
        result = await session.execute(
            select(ShiftType).where(
                ShiftType.team_id == team_id,
                ShiftType.is_active == True
            )
        )
        shift_types = result.scalars().all()
        return [ShiftTypeRead.model_validate(st) for st in shift_types]
    
    async def update_shift_type(self, session: AsyncSession, shift_type_id: uuid.UUID, shift_type_data: ShiftTypeUpdate) -> Optional[ShiftTypeRead]:
        """Update a shift type."""
        result = await session.execute(
            update(ShiftType)
            .where(ShiftType.id == shift_type_id)
            .values(**shift_type_data.model_dump(exclude_unset=True))
            .returning(ShiftType)
        )
        shift_type = result.scalar_one_or_none()
        if shift_type:
            await session.commit()
            return ShiftTypeRead.model_validate(shift_type)
        return None
    
    async def delete_shift_type(self, session: AsyncSession, shift_type_id: uuid.UUID) -> bool:
        """Delete a shift type."""
        result = await session.execute(
            delete(ShiftType).where(ShiftType.id == shift_type_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted shift type: {shift_type_id}")
            return True
        return False
    
    async def get_shift_type_with_team(self, session: AsyncSession, shift_type_id: uuid.UUID) -> Optional[ShiftTypeRead]:
        """Get a shift type with its team information."""
        result = await session.execute(
            select(ShiftType).options(joinedload(ShiftType.team))
            .where(ShiftType.id == shift_type_id)
        )
        shift_type = result.scalar_one_or_none()
        if shift_type:
            return ShiftTypeRead.model_validate(shift_type)
        return None

# Global shift type service instance
shift_type_service = ShiftTypeService()
