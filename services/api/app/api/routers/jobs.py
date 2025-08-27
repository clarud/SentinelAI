from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.celery_client import celery

router = APIRouter()

class Attachment(BaseModel):
    id: str
    filename: Optional[str] = None
    mime: Optional[str] = None
    size: Optional[int] = None

class TriageRequest(BaseModel):
    user_id: str
    message_id: str
    thread_id: Optional[str] = None
    sender: str = ""
    subject: str = ""
    text: str = ""
    urls: List[str] = []
    attachments: List[Attachment] = []

@router.post("/triage")
def trigger_triage(req: TriageRequest):
    payload: Dict[str, Any] = req.model_dump()
    # send by string name to avoid importing worker code in API
    method = "email_triage"
    task = celery.send_task(method, args=[payload])
    print(payload)
    return {"task_id": task.id,
            "method": method,
            "arguments": payload}

@router.get("/tasks/{task_id}")
def task_status(task_id: str):
    r = celery.AsyncResult(task_id)
    return {"state": r.state, "result": (r.result if r.ready() else None)}
