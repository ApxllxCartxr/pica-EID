"""SQLAlchemy models for roles and user-role assignments."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)  # Removed unique=True
    description = Column(Text, nullable=True)
    clearance_level = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    user_roles = relationship("UserRole", back_populates="role")

    __table_args__ = (
        Index("ix_roles_name_active", "name", unique=True, postgresql_where=is_active.is_(True), sqlite_where=is_active.is_(True)),
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(Integer, ForeignKey("admin_accounts.id"), nullable=True)
    removed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("AdminAccount", foreign_keys=[assigned_by])

    __table_args__ = (
        Index("ix_user_roles_active", "user_id", "role_id"),
        UniqueConstraint("user_id", "role_id", name="uq_user_role_active"),
    )
