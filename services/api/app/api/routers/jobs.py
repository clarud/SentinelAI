from fastapi import APIRouter
from pydantic import BaseModel
from app.services import celery_client

router = APIRouter()

class TriageRequest(BaseModel):
    message_id: str
    user_id: str

@router.post("/triage")
def trigger_triage(payload: TriageRequest):
    # Fire-and-forget a Celery task by name; no import of worker code
    res = celery_client.celery.send_task("triage_email", args=[payload.message_id, payload.user_id])
    return {"task_id": res.id}

@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    r = celery_client.celery.AsyncResult(task_id)
    return {"state": r.state, "result": (r.result if r.ready() else None)}
