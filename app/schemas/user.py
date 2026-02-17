"""Pydantic schemas for user-related API operations."""

from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.models.user import UserCategory, UserStatus


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    category: UserCategory
    domain_id: Optional[int] = None
    division_id: Optional[int] = None
    date_of_joining: Optional[date] = None
    start_date: Optional[date] = None  # Will be auto-populated from date_of_joining for interns
    end_date: Optional[date] = None    # Required for interns
    role_ids: Optional[List[int]] = []

    @model_validator(mode="before")
    @classmethod
    def clean_empty_dates(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ["start_date", "end_date", "date_of_joining"]:
                if data.get(field) == "":
                    data[field] = None
        return data


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    domain_id: Optional[int] = None
    division_id: Optional[int] = None
    date_of_joining: Optional[date] = None
    status: Optional[UserStatus] = None
    version: Optional[int] = None  # For optimistic locking

    @model_validator(mode="before")
    @classmethod
    def clean_empty_dates(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("date_of_joining") == "":
                data["date_of_joining"] = None
        return data


class UserResponse(BaseModel):
    id: int
    ulid: str
    display_id: str
    name: str
    email: str
    phone_number: Optional[str] = None
    category: UserCategory
    status: UserStatus
    domain_name: Optional[str] = None
    division_name: Optional[str] = None
    roles: List[str] = []
    conversion_date: Optional[datetime] = None
    date_of_joining: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserSearchQuery(BaseModel):
    name: Optional[str] = None
    ulid: Optional[str] = None
    role: Optional[str] = None
    category: Optional[UserCategory] = None
    status: Optional[UserStatus] = None
    domain_id: Optional[int] = None
    division_id: Optional[int] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class UserSearchResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int


class InternConvertRequest(BaseModel):
    """Request body for converting an intern to employee."""
    migrate_roles: bool = True


class InternExtendRequest(BaseModel):
    """Request body for extending an intern's end date."""
    new_end_date: date
    reason: str = Field(..., min_length=5, max_length=500)
