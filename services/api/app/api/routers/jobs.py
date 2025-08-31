from fastapi import APIRouter
from typing import List, Optional, Dict, Any
from app.services.celery_client import celery
from app.schema import email

router = APIRouter()

@router.post("/triage")
def trigger_triage(req: email.EmailRequest):
    payload: Dict[str, Any] = req.model_dump()
    # send by string name to avoid importing worker code in API
    method = "email_triage"
    task = celery.send_task(method, args=[payload])
    return {"task_id": task.id,
            "method": method,
            "arguments": payload}

@router.get("/tasks/{task_id}")
def task_status(task_id: str):
    r = celery.AsyncResult(task_id)
    return {"state": r.state, "result": (r.result if r.ready() else None)}
