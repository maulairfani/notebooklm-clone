import os

from celery import Celery

from app.core.config import settings

if settings.LANGSMITH_API_KEY:
    os.environ.setdefault("LANGSMITH_TRACING", settings.LANGSMITH_TRACING)
    os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY)
    os.environ.setdefault("LANGSMITH_ENDPOINT", settings.LANGSMITH_ENDPOINT)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)

celery_app = Celery("notebooklm", broker=settings.CELERY_BROKER_URL)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_backend = None
celery_app.autodiscover_tasks(["app.workers"])
