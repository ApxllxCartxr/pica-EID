"""
Intern expiry automation task.

Runs daily at midnight:
1. Checks all active interns with expired end_date → sets status EXPIRED
2. Finds interns with end_date within 7 days → stores warning in Redis
3. Logs all actions to audit_logs
"""

import logging
from datetime import date, timedelta, datetime
import json

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User, UserCategory, UserStatus, InternshipTracking, InternshipStatus
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.intern_expiry.check_intern_expiry")
def check_intern_expiry():
    """Check for expired internships and generate warnings."""
    db = SessionLocal()
    try:
        today = date.today()
        expired_count = 0
        warning_count = 0

        # --- 1. Expire overdue interns ---
        expired_internships = db.query(InternshipTracking).join(User).filter(
            User.category == UserCategory.INTERN,
            User.status == UserStatus.ACTIVE,
            User.deleted_at == None,
            InternshipTracking.end_date < today,
            InternshipTracking.status.in_([InternshipStatus.ACTIVE, InternshipStatus.EXTENDED]),
        ).all()

        for intern_track in expired_internships:
            user = intern_track.user
            user.status = UserStatus.EXPIRED
            user.updated_at = datetime.utcnow()
            intern_track.status = InternshipStatus.EXPIRED
            intern_track.updated_at = datetime.utcnow()

            db.add(AuditLog(
                action="INTERN_EXPIRED",
                entity_type="user",
                entity_id=user.ulid,
                description=f"Internship expired. End date was {intern_track.end_date}",
                new_value={
                    "name": user.name,
                    "end_date": str(intern_track.end_date),
                    "status": "EXPIRED",
                },
            ))
            expired_count += 1

        # --- 2. Generate 7-day warnings ---
        warning_date = today + timedelta(days=7)
        upcoming_expiry = db.query(InternshipTracking).join(User).filter(
            User.category == UserCategory.INTERN,
            User.status == UserStatus.ACTIVE,
            User.deleted_at == None,
            InternshipTracking.end_date >= today,
            InternshipTracking.end_date <= warning_date,
            InternshipTracking.status.in_([InternshipStatus.ACTIVE, InternshipStatus.EXTENDED]),
        ).all()

        warnings = []
        for intern_track in upcoming_expiry:
            user = intern_track.user
            days_remaining = (intern_track.end_date - today).days
            warnings.append({
                "ulid": user.ulid,
                "name": user.name,
                "end_date": str(intern_track.end_date),
                "days_remaining": days_remaining,
            })
            warning_count += 1

        # Store warnings in Redis for dashboard display
        try:
            import redis
            from app.config import settings
            r = redis.from_url(settings.REDIS_URL)
            r.setex(
                "prismid:intern_warnings",
                86400,  # TTL: 24 hours
                json.dumps(warnings),
            )
        except Exception as e:
            logger.warning(f"Failed to store warnings in Redis: {e}")

        db.commit()
        logger.info(f"Intern expiry check: {expired_count} expired, {warning_count} warnings")
        return {"expired": expired_count, "warnings": warning_count}

    except Exception as e:
        db.rollback()
        logger.error(f"Intern expiry check failed: {e}")
        raise
    finally:
        db.close()
