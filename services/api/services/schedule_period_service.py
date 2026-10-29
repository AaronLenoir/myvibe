from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import joinedload
from ..models.schedule_period import SchedulePeriod, PeriodStatus
from ..models.day_shift_slot import DayShiftSlot
from ..models.member_constraint import MemberConstraint
from ..schemas.schedule_period import SchedulePeriodCreate, SchedulePeriodRead, SchedulePeriodUpdate
import uuid
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

class SchedulePeriodService:
    """Service for managing schedule periods."""
    
    def __init__(self):
        pass
    
    async def create_schedule_period(self, session: AsyncSession, period_data: SchedulePeriodCreate, team_id: uuid.UUID) -> SchedulePeriodRead:
        """Create a new schedule period."""
        period = SchedulePeriod(
            **period_data.model_dump(),
            team_id=team_id
        )
        session.add(period)
        await session.commit()
        await session.refresh(period)
        logger.info(f"Created schedule period: {period.id}")
        return SchedulePeriodRead.model_validate(period)
    
    async def get_schedule_period(self, session: AsyncSession, period_id: uuid.UUID) -> Optional[SchedulePeriodRead]:
        """Get a schedule period by ID."""
        result = await session.execute(
            select(SchedulePeriod).where(SchedulePeriod.id == period_id)
        )
        period = result.scalar_one_or_none()
        if period:
            return SchedulePeriodRead.model_validate(period)
        return None
    
    async def get_schedule_periods_by_team(self, session: AsyncSession, team_id: uuid.UUID) -> list[SchedulePeriodRead]:
        """Get all schedule periods for a team."""
        result = await session.execute(
            select(SchedulePeriod).where(SchedulePeriod.team_id == team_id)
            .order_by(SchedulePeriod.start_date.desc())
        )
        periods = result.scalars().all()
        return [SchedulePeriodRead.model_validate(p) for p in periods]
    
    async def get_current_period(self, session: AsyncSession, team_id: uuid.UUID) -> Optional[SchedulePeriodRead]:
        """Get the current active period for a team."""
        today = date.today()
        result = await session.execute(
            select(SchedulePeriod).where(
                SchedulePeriod.team_id == team_id,
                SchedulePeriod.start_date <= today,
                SchedulePeriod.end_date >= today
            ).order_by(SchedulePeriod.start_date.desc())
        )
        period = result.scalar_one_or_none()
        if period:
            return SchedulePeriodRead.model_validate(period)
        return None
    
    async def get_upcoming_periods(self, session: AsyncSession, team_id: uuid.UUID) -> list[SchedulePeriodRead]:
        """Get upcoming schedule periods for a team."""
        today = date.today()
        result = await session.execute(
            select(SchedulePeriod).where(
                SchedulePeriod.team_id == team_id,
                SchedulePeriod.start_date > today
            ).order_by(SchedulePeriod.start_date.asc())
        )
        periods = result.scalars().all()
        return [SchedulePeriodRead.model_validate(p) for p in periods]
    
    async def update_schedule_period(self, session: AsyncSession, period_id: uuid.UUID, period_data: SchedulePeriodUpdate) -> Optional[SchedulePeriodRead]:
        """Update a schedule period."""
        result = await session.execute(
            update(SchedulePeriod)
            .where(SchedulePeriod.id == period_id)
            .values(**period_data.model_dump(exclude_unset=True))
            .returning(SchedulePeriod)
        )
        period = result.scalar_one_or_none()
        if period:
            await session.commit()
            return SchedulePeriodRead.model_validate(period)
        return None
    
    async def delete_schedule_period(self, session: AsyncSession, period_id: uuid.UUID) -> bool:
        """Delete a schedule period."""
        result = await session.execute(
            delete(SchedulePeriod).where(SchedulePeriod.id == period_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted schedule period: {period_id}")
            return True
        return False
    
    async def get_period_with_details(self, session: AsyncSession, period_id: uuid.UUID) -> Optional[SchedulePeriodRead]:
        """Get a schedule period with all related data."""
        result = await session.execute(
            select(SchedulePeriod)
            .options(
                joinedload(SchedulePeriod.day_shift_slots),
                joinedload(SchedulePeriod.member_constraints),
                joinedload(SchedulePeriod.roster_proposals)
            )
            .where(SchedulePeriod.id == period_id)
        )
        period = result.scalar_one_or_none()
        if period:
            return SchedulePeriodRead.model_validate(period)
        return None
    
    async def advance_period_status(self, session: AsyncSession, period_id: uuid.UUID) -> Optional[SchedulePeriodRead]:
        """Advance the status of a schedule period."""
        result = await session.execute(
            select(SchedulePeriod).where(SchedulePeriod.id == period_id)
        )
        period = result.scalar_one_or_none()
        
        if not period:
            return None
        
        # Define status transitions
        transitions = {
            PeriodStatus.DRAFT: PeriodStatus.COLLECTING_WISHES,
            PeriodStatus.COLLECTING_WISHES: PeriodStatus.SOLVING,
            PeriodStatus.SOLVING: PeriodStatus.PROPOSED,
            PeriodStatus.PROPOSED: PeriodStatus.PUBLISHED,
            PeriodStatus.PUBLISHED: PeriodStatus.PUBLISHED  # Terminal state
        }
        
        new_status = transitions.get(period.status, period.status)
        if new_status != period.status:
            period.status = new_status
            await session.commit()
            logger.info(f"Advanced period {period_id} to {new_status}")
        
        return SchedulePeriodRead.model_validate(period)
    
    async def regress_period_status(self, session: AsyncSession, period_id: uuid.UUID) -> Optional[SchedulePeriodRead]:
        """Regress the status of a schedule period."""
        result = await session.execute(
            select(SchedulePeriod).where(SchedulePeriod.id == period_id)
        )
        period = result.scalar_one_or_none()
        
        if not period:
            return None
        
        # Define status regressions
        regressions = {
            PeriodStatus.COLLECTING_WISHES: PeriodStatus.DRAFT,
            PeriodStatus.SOLVING: PeriodStatus.COLLECTING_WISHES,
            PeriodStatus.PROPOSED: PeriodStatus.SOLVING,
            PeriodStatus.PUBLISHED: PeriodStatus.PROPOSED,
            PeriodStatus.DRAFT: PeriodStatus.DRAFT  # Cannot regress from draft
        }
        
        new_status = regressions.get(period.status, period.status)
        if new_status != period.status:
            period.status = new_status
            await session.commit()
            logger.info(f"Regressed period {period_id} to {new_status}")
        
        return SchedulePeriodRead.model_validate(period)

# Global schedule period service instance
schedule_period_service = SchedulePeriodService()
