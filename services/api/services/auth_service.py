import httpx
import uuid
from typing import Optional, dict
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config.settings import get_settings
from ..config.auth import AuthConfig
from ..schemas.auth import OAuthUser, TokenData
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for OAuth providers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.auth_config = AuthConfig()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, user_data: TokenData) -> str:
        """Create JWT access token."""
        data = user_data.model_dump()
        expire = datetime.utcnow() + timedelta(minutes=self.settings.JWT_EXPIRE_MINUTES)
        data["exp"] = expire
        encoded_jwt = jwt.encode(data, self.settings.JWT_SECRET, algorithm=self.settings.JWT_ALGORITHM)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate JWT access token."""
        try:
            payload = jwt.decode(token, self.settings.JWT_SECRET, algorithms=[self.settings.JWT_ALGORITHM])
            user_id = payload.get("user_id")
            email = payload.get("email")
            role = payload.get("role")
            if user_id is None:
                return None
            return TokenData(user_id=uuid.UUID(str(user_id)), email=email, role=role)
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None
    
    async def authenticate_google(self, token: str) -> OAuthUser:
        """Authenticate user with Google OAuth."""
        if not self.auth_config.google_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google authentication is not configured"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Get user info from Google
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                user_data = response.json()
                
                return OAuthUser(
                    id=user_data.get("sub"),
                    email=user_data.get("email"),
                    name=user_data.get("name", ""),
                    avatar_url=user_data.get("picture"),
                    provider="google"
                )
        except httpx.HTTPError as e:
            logger.error(f"Google OAuth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed"
            )
    
    async def authenticate_facebook(self, token: str) -> OAuthUser:
        """Authenticate user with Facebook OAuth."""
        if not self.auth_config.facebook_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook authentication is not configured"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Get user info from Facebook
                response = await client.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={
                        "access_token": token,
                        "fields": "id,email,name,picture.type(large)"
                    }
                )
                response.raise_for_status()
                user_data = response.json()
                
                # Get picture URL
                picture_url = None
                if "picture" in user_data:
                    picture_response = await client.get(user_data["picture"]["data"]["url"])
                    picture_url = user_data["picture"]["data"]["url"]
                
                return OAuthUser(
                    id=user_data.get("id"),
                    email=user_data.get("email", ""),
                    name=user_data.get("name", ""),
                    avatar_url=picture_url,
                    provider="facebook"
                )
        except httpx.HTTPError as e:
            logger.error(f"Facebook OAuth error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Facebook authentication failed"
            )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash (for future use if passwords are added)."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash password (for future use if passwords are added)."""
        return self.pwd_context.hash(password)

# Global auth service instance
auth_service = AuthService()
