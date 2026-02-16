"""Periodic Google Sheets sync task."""

import logging
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.config import settings
from app.models.sync import SheetSyncLog, SyncType, SyncTarget, SyncStatus

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.sheet_sync.sync_to_sheets")
def sync_to_sheets():
    """Push user data changes to Google Sheets every 15 minutes."""
    if not settings.GOOGLE_SHEETS_ENABLED:
        return {"status": "skipped", "reason": "Google Sheets not enabled"}

    db = SessionLocal()
    try:
        from app.services.sheets_service import GoogleSheetsService
        svc = GoogleSheetsService(db)
        count = svc.push_changes()

        db.add(SheetSyncLog(
            sync_type=SyncType.PUSH,
            sync_target=SyncTarget.GOOGLE_SHEETS,
            records_affected=count,
            status=SyncStatus.SUCCESS,
        ))
        db.commit()

        logger.info(f"Google Sheets sync completed: {count} records")
        return {"status": "success", "records": count}

    except Exception as e:
        db.add(SheetSyncLog(
            sync_type=SyncType.PUSH,
            sync_target=SyncTarget.GOOGLE_SHEETS,
            records_affected=0,
            status=SyncStatus.FAILED,
            error_message=str(e),
        ))
        db.commit()
        logger.error(f"Google Sheets sync failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
