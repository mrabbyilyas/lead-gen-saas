"""Celery application configuration and setup."""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "lead_gen_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.background_jobs.scraping_tasks",
        "app.services.background_jobs.data_processing_tasks",
        "app.services.background_jobs.analytics_tasks",
        "app.services.background_jobs.maintenance_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.services.background_jobs.scraping_tasks.*": {"queue": "scraping"},
        "app.services.background_jobs.data_processing_tasks.*": {"queue": "processing"},
        "app.services.background_jobs.analytics_tasks.*": {"queue": "analytics"},
        "app.services.background_jobs.maintenance_tasks.*": {"queue": "maintenance"},
    },
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-expired-jobs": {
            "task": "app.services.background_jobs.maintenance_tasks.cleanup_expired_jobs",
            "schedule": 3600.0,  # Every hour
        },
        "update-job-statistics": {
            "task": "app.services.background_jobs.analytics_tasks.update_job_statistics",
            "schedule": 1800.0,  # Every 30 minutes
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f"Request: {self.request!r}")
    return "Debug task completed"
