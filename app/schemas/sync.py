"""Pydantic schemas for spreadsheet sync operations."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.sync import SyncType, SyncTarget, SyncStatus


class SyncLogResponse(BaseModel):
    id: int
    sync_type: SyncType
    sync_target: SyncTarget
    records_affected: int
    status: SyncStatus
    error_message: Optional[str] = None
    initiated_by_name: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class SyncLogListResponse(BaseModel):
    logs: List[SyncLogResponse]
    total: int


class SheetSyncRequest(BaseModel):
    """Trigger a push sync to Google Sheets."""
    full_sync: bool = False  # False = incremental, True = full


class ExcelExportResponse(BaseModel):
    filename: str
    records_count: int
    download_url: str
