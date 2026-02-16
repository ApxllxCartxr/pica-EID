"""Dashboard API endpoints: stats, warnings, trends, and audit export."""

import json
import csv
import io
import math
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User, UserCategory, UserStatus
from app.models.role import Role
from app.models.audit import AuditLog
from app.models.admin import AdminAccount
from app.api.deps import require_viewer, require_admin
from app.config import settings

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_admin: AdminAccount = Depends(require_viewer)):
    """Get dashboard statistics with proper DI."""
    total_users = db.query(User).filter(User.deleted_at == None).count()
    active_users = db.query(User).filter(User.status == UserStatus.ACTIVE, User.deleted_at == None).count()
    total_interns = db.query(User).filter(User.category == UserCategory.INTERN, User.deleted_at == None).count()
    total_employees = db.query(User).filter(User.category == UserCategory.EMPLOYEE, User.deleted_at == None).count()
    total_roles = db.query(Role).filter(Role.is_active == True).count()
    recent_actions = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5).all()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_interns": total_interns,
        "total_employees": total_employees,
        "total_roles": total_roles,
        "recent_actions": [
            {
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in recent_actions
        ],
    }


@router.get("/warnings")
def get_intern_warnings():
    """Get cached intern expiry warnings from Redis."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        data = r.get("prismid:intern_warnings")
        if data:
            return {"warnings": json.loads(data)}
        return {"warnings": []}
    except Exception:
        return {"warnings": []}


@router.get("/stats/trend")
def get_user_trend(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_viewer),
):
    """Get user creation trend data for the last N days."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Query daily user creation counts
    results = (
        db.query(
            func.date(User.created_at).label("day"),
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= start_date, User.deleted_at == None)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )

    # Build a complete date range with zeros for missing days
    date_counts = {str(r.day): r.count for r in results}
    trend = []
    for i in range(days):
        d = (start_date + timedelta(days=i)).date()
        trend.append({"date": str(d), "count": date_counts.get(str(d), 0)})

    return {"trend": trend, "days": days}


@router.get("/audit/export")
def export_audit_csv(
    action: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_admin: AdminAccount = Depends(require_admin),
):
    """Export audit logs as CSV download."""
    from sqlalchemy.orm import joinedload

    query = db.query(AuditLog).options(joinedload(AuditLog.admin))

    if action:
        query = query.filter(AuditLog.action == action)
    if date_from:
        query = query.filter(AuditLog.timestamp >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(AuditLog.timestamp <= datetime.combine(date_to, datetime.max.time()))

    logs = query.order_by(AuditLog.timestamp.desc()).limit(5000).all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Action", "Entity Type", "Entity ID", "Changed By", "Description", "IP Address", "Timestamp"])

    for log in logs:
        writer.writerow([
            log.id,
            log.action,
            log.entity_type,
            log.entity_id or "",
            log.admin.username if log.admin else "",
            log.description or "",
            log.ip_address or "",
            log.timestamp.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"},
    )
