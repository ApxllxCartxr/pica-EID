"""SQLAlchemy model for admin accounts."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from app.database import Base


class AccessLevel(str, enum.Enum):
    VIEWER = "VIEWER"
    ADMIN = "ADMIN"
    SUPERADMIN = "SUPERADMIN"


class AdminAccount(Base):
    __tablename__ = "admin_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    access_level = Column(Enum(AccessLevel), default=AccessLevel.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
