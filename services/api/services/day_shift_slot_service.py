from typing import Optional, list
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import joinedload
from ..models.day_shift_slot import DayShiftSlot
from ..models.schedule_period import SchedulePeriod
from ..schemas.day_shift_slot import DayShiftSlotCreate, DayShiftSlotRead, DayShiftSlotUpdate
import uuid
import logging
from datetime import date

logger = logging.getLogger(__name__)

class DayShiftSlotService:
    """Service for managing day shift slots."""
    
    def __init__(self):
        pass
    
    async def create_day_shift_slot(
        self,
        session: AsyncSession,
        slot_data: DayShiftSlotCreate,
        period_id: uuid.UUID
    ) -> DayShiftSlotRead:
        """Create a new day shift slot."""
        slot = DayShiftSlot(
            **slot_data.model_dump(),
            period_id=period_id
        )
        session.add(slot)
        await session.commit()
        await session.refresh(slot)
        logger.info(f"Created day shift slot: {slot.id}")
        return DayShiftSlotRead.model_validate(slot)
    
    async def create_multiple_day_shift_slots(
        self,
        session: AsyncSession,
        slots_data: list[tuple[date, uuid.UUID, int, int]],
        period_id: uuid.UUID
    ) -> list[DayShiftSlotRead]:
        """Create multiple day shift slots."""
        slots = []
        for date_val, shift_type_id, min_staff, max_staff in slots_data:
            slot = DayShiftSlot(
                period_id=period_id,
                date=date_val,
                shift_type_id=shift_type_id,
                min_staff=min_staff,
                max_staff=max_staff
            )
            session.add(slot)
            slots.append(slot)
        
        await session.commit()
        for slot in slots:
            await session.refresh(slot)
        
        logger.info(f"Created {len(slots)} day shift slots")
        return [DayShiftSlotRead.model_validate(slot) for slot in slots]
    
    async def get_day_shift_slot(self, session: AsyncSession, slot_id: uuid.UUID) -> Optional[DayShiftSlotRead]:
        """Get a day shift slot by ID."""
        result = await session.execute(
            select(DayShiftSlot).where(DayShiftSlot.id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if slot:
            return DayShiftSlotRead.model_validate(slot)
        return None
    
    async def get_slots_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> list[DayShiftSlotRead]:
        """Get all day shift slots for a period."""
        result = await session.execute(
            select(DayShiftSlot).where(DayShiftSlot.period_id == period_id)
            .order_by(DayShiftSlot.date, DayShiftSlot.shift_type_id)
        )
        slots = result.scalars().all()
        return [DayShiftSlotRead.model_validate(slot) for slot in slots]
    
    async def get_slots_by_date(self, session: AsyncSession, period_id: uuid.UUID, date_val: date) -> list[DayShiftSlotRead]:
        """Get all day shift slots for a specific date in a period."""
        result = await session.execute(
            select(DayShiftSlot).where(
                DayShiftSlot.period_id == period_id,
                DayShiftSlot.date == date_val
            )
        )
        slots = result.scalars().all()
        return [DayShiftSlotRead.model_validate(slot) for slot in slots]
    
    async def get_slots_by_shift_type(self, session: AsyncSession, period_id: uuid.UUID, shift_type_id: uuid.UUID) -> list[DayShiftSlotRead]:
        """Get all day shift slots for a specific shift type in a period."""
        result = await session.execute(
            select(DayShiftSlot).where(
                DayShiftSlot.period_id == period_id,
                DayShiftSlot.shift_type_id == shift_type_id
            )
        )
        slots = result.scalars().all()
        return [DayShiftSlotRead.model_validate(slot) for slot in slots]
    
    async def update_day_shift_slot(
        self,
        session: AsyncSession,
        slot_id: uuid.UUID,
        slot_data: DayShiftSlotUpdate
    ) -> Optional[DayShiftSlotRead]:
        """Update a day shift slot."""
        result = await session.execute(
            update(DayShiftSlot)
            .where(DayShiftSlot.id == slot_id)
            .values(**slot_data.model_dump(exclude_unset=True))
            .returning(DayShiftSlot)
        )
        slot = result.scalar_one_or_none()
        if slot:
            await session.commit()
            return DayShiftSlotRead.model_validate(slot)
        return None
    
    async def delete_day_shift_slot(self, session: AsyncSession, slot_id: uuid.UUID) -> bool:
        """Delete a day shift slot."""
        result = await session.execute(
            delete(DayShiftSlot).where(DayShiftSlot.id == slot_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted day shift slot: {slot_id}")
            return True
        return False
    
    async def delete_slots_by_period(self, session: AsyncSession, period_id: uuid.UUID) -> int:
        """Delete all day shift slots for a period."""
        result = await session.execute(
            delete(DayShiftSlot).where(DayShiftSlot.period_id == period_id)
        )
        count = result.rowcount
        if count > 0:
            await session.commit()
            logger.info(f"Deleted {count} day shift slots for period: {period_id}")
        return count
    
    async def get_slots_for_date_range(
        self,
        session: AsyncSession,
        period_id: uuid.UUID,
        start_date: date,
        end_date: date
    ) -> list[DayShiftSlotRead]:
        """Get day shift slots for a date range."""
        result = await session.execute(
            select(DayShiftSlot).where(
                DayShiftSlot.period_id == period_id,
                DayShiftSlot.date >= start_date,
                DayShiftSlot.date <= end_date
            )
            .order_by(DayShiftSlot.date, DayShiftSlot.shift_type_id)
        )
        slots = result.scalars().all()
        return [DayShiftSlotRead.model_validate(slot) for slot in slots]
    
    async def get_slots_with_details(self, session: AsyncSession, period_id: uuid.UUID) -> list[DayShiftSlotRead]:
        """Get day shift slots with shift type details."""
        result = await session.execute(
            select(DayShiftSlot).options(joinedload(DayShiftSlot.shift_type))
            .where(DayShiftSlot.period_id == period_id)
            .order_by(DayShiftSlot.date, DayShiftSlot.shift_type_id)
        )
        slots = result.scalars().all()
        return [DayShiftSlotRead.model_validate(slot) for slot in slots]

# Global day shift slot service instance
day_shift_slot_service = DayShiftSlotService()
