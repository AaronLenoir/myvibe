from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from typing import Optional
from ...schemas.auth import Token, TokenData, OAuthUser
from ...services.auth_service import auth_service
from ...services.user_service import user_service
from ...services.team_service import team_service
from ...config.database import database
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security schemes
http_bearer = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_db():
    """Get database session."""
    async with database.get_session() as session:
        yield session

@router.post("/google", response_model=Token, summary="Authenticate with Google")
async def authenticate_google(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user with Google OAuth token."""
    try:
        # Authenticate with Google
        oauth_user = await auth_service.authenticate_google(token)
        
        # Get or create team (for MVP, use default team)
        team = await team_service.get_or_create_default_team(db)
        
        # Get or create user
        existing_user = await user_service.get_user_by_provider(
            db, oauth_user.provider, oauth_user.id
        )
        
        if existing_user:
            user = existing_user
        else:
            # Check if this is the first user (becomes manager)
            user = await user_service.get_first_user_or_create_manager(
                db, team.id,
                user_service.UserCreate(
                    name=oauth_user.name,
                    email=oauth_user.email,
                    avatar_url=oauth_user.avatar_url,
                    auth_provider=oauth_user.provider,
                    provider_subject=oauth_user.id
                )
            )
        
        # Create access token
        token_data = TokenData(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        access_token = auth_service.create_access_token(token_data)
        
        logger.info(f"User authenticated: {user.id} ({oauth_user.provider})")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "team_id": str(user.team_id)
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Google authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed"
        )

@router.post("/facebook", response_model=Token, summary="Authenticate with Facebook")
async def authenticate_facebook(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user with Facebook OAuth token."""
    try:
        # Authenticate with Facebook
        oauth_user = await auth_service.authenticate_facebook(token)
        
        # Get or create team (for MVP, use default team)
        team = await team_service.get_or_create_default_team(db)
        
        # Get or create user
        existing_user = await user_service.get_user_by_provider(
            db, oauth_user.provider, oauth_user.id
        )
        
        if existing_user:
            user = existing_user
        else:
            # Check if this is the first user (becomes manager)
            user = await user_service.get_first_user_or_create_manager(
                db, team.id,
                user_service.UserCreate(
                    name=oauth_user.name,
                    email=oauth_user.email,
                    avatar_url=oauth_user.avatar_url,
                    auth_provider=oauth_user.provider,
                    provider_subject=oauth_user.id
                )
            )
        
        # Create access token
        token_data = TokenData(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        access_token = auth_service.create_access_token(token_data)
        
        logger.info(f"User authenticated: {user.id} ({oauth_user.provider})")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "team_id": str(user.team_id)
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Facebook authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Facebook authentication failed"
        )

@router.get("/me", summary="Get current user")
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Get information about the current authenticated user."""
    try:
        # Decode token
        token_data = auth_service.decode_access_token(token)
        if not token_data or not token_data.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = await user_service.get_user(db, token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": str(user.id),
            "team_id": str(user.team_id),
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "auth_provider": user.auth_provider,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Refresh the access token."""
    try:
        # Decode old token
        token_data = auth_service.decode_access_token(token)
        if not token_data or not token_data.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = await user_service.get_user(db, token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create new token
        new_token_data = TokenData(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        new_access_token = auth_service.create_access_token(new_token_data)
        
        return Token(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=30 * 60,
            user={
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "team_id": str(user.team_id)
            }
        )
    
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
