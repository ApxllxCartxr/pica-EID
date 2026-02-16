"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "prismid",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.intern_expiry",
        "app.tasks.sheet_sync",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "check-intern-expiry": {
        "task": "app.tasks.intern_expiry.check_intern_expiry",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight UTC
    },
    "sync-google-sheets": {
        "task": "app.tasks.sheet_sync.sync_to_sheets",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}
