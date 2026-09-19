from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "pnbc_workers",
    broker=settings.get_celery_broker_url(),
    backend=settings.get_celery_result_backend(),
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per document
    worker_prefetch_multiplier=1,
)
