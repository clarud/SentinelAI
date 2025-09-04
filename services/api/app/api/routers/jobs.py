from fastapi import APIRouter
from typing import List, Optional, Dict, Any
from app.services.celery_client import celery
from app.schema import email, celery as celery_schema

router = APIRouter()

from fastapi import APIRouter
from typing import Dict, Any
from app.services.celery_client import celery
from app.schema import email, celery as celery_schema

router = APIRouter()

@router.post("/triage")
def trigger_triage(req: email.EmailData):
    """
    Triggers an email triage process by sending the email data to Celery for processing.
    """
    # Convert the request Pydantic model to a dictionary (payload)
    payload: Dict[str, Any] = req.model_dump()

    # Send the task to Celery for processing, using the task name (string) and payload
    method = "email_triage"
    task = celery.send_task(method, args=[payload])

    # Return the task details (task ID, method, and arguments) as a response
    return celery_schema.CeleryResponse(
        task_id=task.id,
        method=[method],  # The task method
        arguments=payload  # Arguments passed to the task
    ).model_dump()



@router.get("/tasks/{task_id}")
def task_status(task_id: str):
    r = celery.AsyncResult(task_id)
    return {"state": r.state, "result": (r.result if r.ready() else None)}
