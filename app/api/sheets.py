"""Spreadsheet sync API endpoints."""

import os
import math
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.admin import AdminAccount
from app.models.sync import SheetSyncLog, SyncType, SyncTarget, SyncStatus
from app.schemas.sync import SyncLogResponse, SyncLogListResponse, ExcelExportResponse
from app.api.deps import require_admin
from app.services.excel_service import ExcelService
from app.config import settings

router = APIRouter(prefix="/sheets", tags=["Spreadsheet Integration"])


@router.post("/export", response_model=ExcelExportResponse)
def export_excel(
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Export current user data to Excel (.xlsx file)."""
    try:
        excel_svc = ExcelService(db)
        filename, count = excel_svc.export_users()

        # Log sync
        db.add(SheetSyncLog(
            sync_type=SyncType.EXPORT,
            sync_target=SyncTarget.EXCEL,
            records_affected=count,
            status=SyncStatus.SUCCESS,
            initiated_by=current_admin.id,
        ))
        db.commit()

        return ExcelExportResponse(
            filename=filename,
            records_count=count,
            download_url=f"sheets/download/{filename}",
        )
    except Exception as e:
        db.add(SheetSyncLog(
            sync_type=SyncType.EXPORT,
            sync_target=SyncTarget.EXCEL,
            records_affected=0,
            status=SyncStatus.FAILED,
            error_message=str(e),
            initiated_by=current_admin.id,
        ))
        db.commit()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{filename}")
def download_file(
    filename: str,
    current_admin: AdminAccount = Depends(require_admin),
):
    """Download an exported Excel file."""
    filepath = os.path.join(settings.EXCEL_EXPORT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@router.post("/import")
def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Import user data from an uploaded Excel file."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are accepted")

    try:
        excel_svc = ExcelService(db)
        result = excel_svc.import_users(file.file, current_admin.id)

        db.add(SheetSyncLog(
            sync_type=SyncType.IMPORT,
            sync_target=SyncTarget.EXCEL,
            records_affected=result["updated"],
            status=SyncStatus.SUCCESS if not result["errors"] else SyncStatus.PARTIAL,
            error_message="; ".join(result["errors"]) if result["errors"] else None,
            initiated_by=current_admin.id,
        ))
        db.commit()

        return result
    except Exception as e:
        db.add(SheetSyncLog(
            sync_type=SyncType.IMPORT,
            sync_target=SyncTarget.EXCEL,
            records_affected=0,
            status=SyncStatus.FAILED,
            error_message=str(e),
            initiated_by=current_admin.id,
        ))
        db.commit()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/sync-google")
def trigger_google_sync(
    full_sync: bool = False,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Trigger a push sync to Google Sheets (Admin+ access)."""
    if not settings.GOOGLE_SHEETS_ENABLED:
        raise HTTPException(status_code=400, detail="Google Sheets integration is not enabled")

    try:
        from app.services.sheets_service import GoogleSheetsService
        sheets_svc = GoogleSheetsService(db)
        count = sheets_svc.push_all() if full_sync else sheets_svc.push_changes()

        db.add(SheetSyncLog(
            sync_type=SyncType.PUSH,
            sync_target=SyncTarget.GOOGLE_SHEETS,
            records_affected=count,
            status=SyncStatus.SUCCESS,
            initiated_by=current_admin.id,
        ))
        db.commit()

        return {"message": f"Synced {count} records to Google Sheets"}
    except Exception as e:
        db.add(SheetSyncLog(
            sync_type=SyncType.PUSH,
            sync_target=SyncTarget.GOOGLE_SHEETS,
            records_affected=0,
            status=SyncStatus.FAILED,
            error_message=str(e),
            initiated_by=current_admin.id,
        ))
        db.commit()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/logs", response_model=SyncLogListResponse)
def list_sync_logs(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """List spreadsheet sync logs (Admin+ access)."""
    query = db.query(SheetSyncLog)
    total = query.count()
    logs = query.order_by(SheetSyncLog.timestamp.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return SyncLogListResponse(
        logs=[
            SyncLogResponse(
                id=log.id,
                sync_type=log.sync_type,
                sync_target=log.sync_target,
                records_affected=log.records_affected,
                status=log.status,
                error_message=log.error_message,
                initiated_by_name=log.admin.username if log.admin else None,
                timestamp=log.timestamp,
            )
            for log in logs
        ],
        total=total,
    )
