import os
from celery import Celery
from dotenv import load_dotenv
load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)

celery = Celery(
    "sentinel_ai",
    broker=BROKER_URL,
    backend=RESULT_BACKEND, 
    include=["worker.worker.tasks.email_task"]
)

celery.conf.update(
    task_default_queue="default",
    task_queues=None,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)