"""Audit log API endpoints."""

from datetime import datetime, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from pydantic import BaseModel
import math

from app.database import get_db
from app.models.audit import AuditLog
from app.models.admin import AdminAccount
from app.api.deps import require_admin

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    changed_by_name: Optional[str] = None
    previous_value: Optional[dict] = None
    new_value: Optional[dict] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    pages: int


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """List audit logs with filtering (Admin+ access)."""
    query = db.query(AuditLog).options(joinedload(AuditLog.admin))

    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.combine(date_to, datetime.max.time()))

    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return AuditLogListResponse(
        logs=[
            AuditLogResponse(
                id=log.id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                changed_by_name=log.admin.username if log.admin else None,
                previous_value=log.previous_value,
                new_value=log.new_value,
                description=log.description,
                ip_address=log.ip_address,
                timestamp=log.timestamp,
            )
            for log in logs
        ],
        total=total,
        page=page,
        pages=math.ceil(total / per_page) if total > 0 else 1,
    )
