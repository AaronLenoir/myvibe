from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar

T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            # Add custom JSON encoders here if needed
        }
    )

class ResponseSchema(BaseSchema, Generic[T]):
    """Generic response schema with success flag and data."""
    success: bool = True
    data: T | None = None
    message: str | None = None
    error: str | None = None

class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response schema."""
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
