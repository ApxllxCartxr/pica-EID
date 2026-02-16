"""Pydantic schemas for role-related API operations."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    clearance_level: int = Field(1, ge=1, le=10)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    clearance_level: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None
    version: Optional[int] = None  # For optimistic locking


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    clearance_level: int
    is_active: bool
    assigned_users_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int


class UserRoleAssign(BaseModel):
    role_id: int


class UserRoleRemove(BaseModel):
    role_id: int
