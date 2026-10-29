from pydantic import Field, EmailStr
from .base import BaseSchema
from typing import Optional
import uuid
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    MANAGER = "manager"
    MEMBER = "member"

class UserCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255, description="User name")
    email: EmailStr = Field(..., description="User email")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    role: UserRole = Field(UserRole.MEMBER, description="User role")
    auth_provider: str = Field(..., description="Authentication provider")
    provider_subject: str = Field(..., description="Provider subject ID")

class UserRead(BaseSchema):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    email: EmailStr
    avatar_url: Optional[str]
    role: UserRole
    auth_provider: str
    provider_subject: str
    created_at: datetime

class UserUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User name")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    role: Optional[UserRole] = Field(None, description="User role")
