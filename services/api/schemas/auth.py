from pydantic import Field, EmailStr
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class TokenData(BaseSchema):
    user_id: Optional[uuid.UUID] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

class OAuthUser(BaseSchema):
    id: str
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None
    provider: str
