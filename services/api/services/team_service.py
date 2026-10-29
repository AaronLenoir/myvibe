from typing import Optional, list, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from ..models.team import Team
from ..models.user import User, UserRole
from ..schemas.team import TeamCreate, TeamRead, TeamUpdate
from ..schemas.user import UserCreate
import uuid
import logging

logger = logging.getLogger(__name__)

class TeamService:
    """Service for managing teams."""
    
    def __init__(self):
        pass
    
    async def create_team(self, session: AsyncSession, team_data: TeamCreate) -> TeamRead:
        """Create a new team."""
        team = Team(**team_data.model_dump())
        session.add(team)
        await session.commit()
        await session.refresh(team)
        logger.info(f"Created team: {team.id}")
        return TeamRead.model_validate(team)
    
    async def get_team(self, session: AsyncSession, team_id: uuid.UUID) -> Optional[TeamRead]:
        """Get a team by ID."""
        result = await session.execute(
            select(Team).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        if team:
            return TeamRead.model_validate(team)
        return None
    
    async def get_teams(self, session: AsyncSession) -> list[TeamRead]:
        """Get all teams."""
        result = await session.execute(select(Team))
        teams = result.scalars().all()
        return [TeamRead.model_validate(team) for team in teams]
    
    async def update_team(self, session: AsyncSession, team_id: uuid.UUID, team_data: TeamUpdate) -> Optional[TeamRead]:
        """Update a team."""
        result = await session.execute(
            update(Team)
            .where(Team.id == team_id)
            .values(**team_data.model_dump(exclude_unset=True))
            .returning(Team)
        )
        team = result.scalar_one_or_none()
        if team:
            await session.commit()
            return TeamRead.model_validate(team)
        return None
    
    async def delete_team(self, session: AsyncSession, team_id: uuid.UUID) -> bool:
        """Delete a team."""
        result = await session.execute(
            delete(Team).where(Team.id == team_id)
        )
        if result.rowcount > 0:
            await session.commit()
            logger.info(f"Deleted team: {team_id}")
            return True
        return False
    
    async def get_or_create_default_team(self, session: AsyncSession) -> TeamRead:
        """Get or create the default team for single-tenant MVP."""
        result = await session.execute(select(Team).limit(1))
        team = result.scalar_one_or_none()
        
        if not team:
            team = Team(name="Default Team")
            session.add(team)
            await session.commit()
            await session.refresh(team)
            logger.info(f"Created default team: {team.id}")
        
        return TeamRead.model_validate(team)

# Global team service instance
team_service = TeamService()
