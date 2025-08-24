import os
from dotenv import load_dotenv
from celery import Celery

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0") # not set up

celery = Celery("sentinelai", broker=REDIS_URL, backend=REDIS_URL)

