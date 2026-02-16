"""SQLAlchemy models for audit logs and conversion history."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=True)
    changed_by = Column(Integer, ForeignKey("admin_accounts.id"), nullable=True)
    previous_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    admin = relationship("AdminAccount", foreign_keys=[changed_by])

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_action_time", "action", "timestamp"),
    )


class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_ulid = Column(String(26), nullable=False)
    previous_category = Column(String(20), nullable=False)
    new_category = Column(String(20), nullable=False)
    converted_by = Column(Integer, ForeignKey("admin_accounts.id"), nullable=False)
    conversion_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    roles_migrated = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    admin = relationship("AdminAccount", foreign_keys=[converted_by])


class IdMigrationMap(Base):
    """Backward-compatibility mapping from old user_ids to new ULIDs."""
    __tablename__ = "id_migration_map"

    id = Column(Integer, primary_key=True, autoincrement=True)
    old_user_id = Column(String(30), nullable=False, index=True, unique=True)
    new_ulid = Column(String(26), nullable=False, index=True)
    migrated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
