from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import joinedload
from ..models.member_constraint import MemberConstraint, ConstraintKind
from ..models.schedule_period import SchedulePeriod
from ..models.user import User
from ..models.shift_type import ShiftType
from ..schemas.member_constraint import MemberConstraintCreate, MemberConstraintRead
import uuid
import logging
from datetime import date

logger = logging.getLogger(__name__)

class ConstraintService:
    """Service for managing member constraints."""
    
    def __init__(self):
        pass
    
    async def create_constraint(self, session: AsyncSession, constraint_data: MemberConstraintCreate, user_id: uuid.UUID) -> MemberConstraintRead:
        """Create a new member constraint."""
        constraint = MemberConstraint(
            **constraint_data.model_dump(),
            user_id=user_id
        )
        session.add(constraint)
        await session.commit()
        await session.refresh(constraint)
        logger.info(f"Created constraint: {constraint.id}")
        return MemberConstraintRead.model_validate(constraint)
    
    async def get_constraint(self, session: AsyncSession, constraint_id: uuid.UUID) -> Optional[MemberConstraintRead]:
        """Get a constraint by ID."""
        result = await session.execute(
            select(MemberConstraint).where(MemberConstraint.id == constraint_id)
        )
        constraint = result.scalar_one_or_none()
        if constraint:
            return MemberConstraintRead.model_validate(constraint)
        return None
    
    async def get_constraints_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> list[MemberConstraintRead]:
        """Get all constraints for a schedule period."""
        result = await session.execute(
            select(MemberConstraint).where(MemberConstraint.period_id == period_id)
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]
    
    async def get_constraints_by_user(self, session: AsyncSession, user_id: uuid.UUID) -> list[MemberConstraintRead]:
        """Get all constraints for a user."""
        result = await session.execute(
            select(MemberConstraint).where(MemberConstraint.user_id == user_id)
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]
    
    async def get_constraints_by_user_and_period(self, session: AsyncSession, user_id: uuid.UUID, period_id: uuid.UUID) -> list[MemberConstraintRead]:
        """Get all constraints for a user and period."""
        result = await session.execute(
            select(MemberConstraint).where(
                MemberConstraint.user_id == user_id,
                MemberConstraint.period_id == period_id
            )
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]
    
    async def get_hard_constraints_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> list[MemberConstraintRead]:
        """Get all hard constraints for a period."""
        result = await session.execute(
            select(MemberConstraint).where(
                MemberConstraint.period_id == period_id,
                MemberConstraint.kind.in_([ConstraintKind.VACATION, ConstraintKind.UNAVAILABLE])
            )
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]
    
    async def get_soft_constraints_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> list[MemberConstraintRead]:
        """Get all soft constraints for a period."""
        result = await session.execute(
            select(MemberConstraint).where(
                MemberConstraint.period_id == period_id,
                MemberConstraint.kind.in_([ConstraintKind.PREFERENCE_AVOID, ConstraintKind.PREFERENCE_WANT])
            )
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]
    
    async def update_constraint(self, session: AsyncSession, constraint_id: uuid.UUID, constraint_data: MemberConstraintCreate) -> Optional[MemberConstraintRead]:
        """Update a constraint."""
        result = await session.execute(
            update(MemberConstraint)
            .where(MemberConstraint.id == constraint_id)
            .values(**constraint_data.model_dump(exclude_unset=True))
            .returning(MemberConstraint)
        )
        constraint = result.scalar_one_or_none()
        if constraint:
            await session.commit()
            return MemberConstraintRead.model_validate(constraint)
        return None
    
    async def delete_constraint(self, session: AsyncSession, constraint_id: uuid.UUID) -> bool:
        """Delete a constraint."""
        result = await session.execute(
            delete(MemberConstraint).where(MemberConstraint.id == constraint_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted constraint: {constraint_id}")
            return True
        return False
    
    async def delete_constraints_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> int:
        """Delete all constraints for a period."""
        result = await session.execute(
            delete(MemberConstraint).where(MemberConstraint.period_id == period_id)
        )
        count = result.rowcount
        if count > 0:
            await session.commit()
            logger.info(f"Deleted {count} constraints for period: {period_id}")
        return count
    
    async def get_constraints_for_date_range(self, session: AsyncSession, period_id: uuid.UUID, start_date: date, end_date: date) -> list[MemberConstraintRead]:
        """Get constraints that overlap with a date range."""
        result = await session.execute(
            select(MemberConstraint).where(
                MemberConstraint.period_id == period_id,
                or_(
                    and_(MemberConstraint.start_date <= end_date, MemberConstraint.end_date >= start_date),
                    and_(MemberConstraint.start_date <= start_date, MemberConstraint.end_date >= start_date),
                    and_(MemberConstraint.start_date <= end_date, MemberConstraint.end_date >= end_date)
                )
            )
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]
    
    async def get_constraints_by_shift_type(self, session: AsyncSession, period_id: uuid.UUID, shift_type_id: uuid.UUID) -> list[MemberConstraintRead]:
        """Get constraints for a specific shift type."""
        result = await session.execute(
            select(MemberConstraint).where(
                MemberConstraint.period_id == period_id,
                MemberConstraint.shift_type_id == shift_type_id
            )
        )
        constraints = result.scalars().all()
        return [MemberConstraintRead.model_validate(c) for c in constraints]

# Global constraint service instance
constraint_service = ConstraintService()
