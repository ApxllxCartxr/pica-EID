"""SQLAlchemy model for spreadsheet sync logs."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SyncType(str, enum.Enum):
    PUSH = "PUSH"
    PULL = "PULL"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"


class SyncTarget(str, enum.Enum):
    GOOGLE_SHEETS = "GOOGLE_SHEETS"
    EXCEL = "EXCEL"


class SyncStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class SheetSyncLog(Base):
    __tablename__ = "sheet_sync_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(Enum(SyncType), nullable=False)
    sync_target = Column(Enum(SyncTarget), nullable=False)
    records_affected = Column(Integer, default=0)
    status = Column(Enum(SyncStatus), nullable=False)
    error_message = Column(Text, nullable=True)
    initiated_by = Column(Integer, ForeignKey("admin_accounts.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    admin = relationship("AdminAccount", foreign_keys=[initiated_by])
