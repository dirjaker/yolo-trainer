from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "yolo_trainer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 24,        # 24h hard limit per task
    task_soft_time_limit=3600 * 23,    # 23h soft limit
    worker_prefetch_multiplier=1,      # one task at a time per worker
    worker_max_tasks_per_child=10,     # restart worker after 10 tasks (memory cleanup)
)

celery_app.autodiscover_tasks(["app.tasks"])
