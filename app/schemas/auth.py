"""Pydantic schemas for authentication."""

from typing import Optional
from pydantic import BaseModel, Field
from app.models.admin import AccessLevel


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_level: AccessLevel
    username: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AdminCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    email: Optional[str] = None
    display_name: Optional[str] = None
    access_level: AccessLevel = AccessLevel.VIEWER
