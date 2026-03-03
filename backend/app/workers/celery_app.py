from celery import Celery

from app.core.config import settings

celery_app = Celery("notebooklm", broker=settings.CELERY_BROKER_URL)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_backend = None
celery_app.autodiscover_tasks(["app.workers"])
