from fastapi import APIRouter, Depends, HTTPException, status
from typing import list
from ...schemas.team import TeamCreate, TeamRead, TeamUpdate
from ...services.team_service import team_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
from ...services.auth_service import auth_service
from fastapi.security import HTTPBearer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])

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

@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED, summary="Create team")
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new team."""
    try:
        team = await team_service.create_team(db, team_data)
        logger.info(f"Team created: {team.id}")
        return team
    except Exception as e:
        logger.error(f"Create team failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=list[TeamRead], summary="List teams")
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all teams."""
    try:
        teams = await team_service.get_teams(db)
        return teams
    except Exception as e:
        logger.error(f"List teams failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{team_id}", response_model=TeamRead, summary="Get team")
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific team."""
    try:
        team = await team_service.get_team(db, uuid.UUID(team_id))
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        return team
    except Exception as e:
        logger.error(f"Get team failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{team_id}", response_model=TeamRead, summary="Update team")
async def update_team(
    team_id: str,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a team."""
    try:
        team = await team_service.update_team(db, uuid.UUID(team_id), team_data)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        return team
    except Exception as e:
        logger.error(f"Update team failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete team")
async def delete_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a team."""
    try:
        success = await team_service.delete_team(db, uuid.UUID(team_id))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        return None
    except Exception as e:
        logger.error(f"Delete team failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
