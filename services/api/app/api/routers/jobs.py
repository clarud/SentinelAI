from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional, Dict, Any
from api.app.services.celery_client import celery
from api.app.schema import email as email_schema , celery as celery_schema, chat as chat_schema
from worker.worker.agents import orchestrator
from api.app.services import file_service

router = APIRouter()

@router.post("/triage")
def trigger_triage_email(req: email_schema.EmailData):
    """
    Triggers an email triage process by sending the email data to Celery for processing.
    """
    # Convert the request Pydantic model to a dictionary (payload)
    payload: Dict[str, Any] = req.model_dump()

    # Send the task to Celery for processing, using the task name (string) and payload
    method = "email_triage_with_email"
    task = celery.send_task(method, args=[payload])

    # Return the task details (task ID, method, and arguments) as a response
    return celery_schema.CeleryResponse(
        task_id=task.id,
        method=[method],  # The task method
        arguments=payload  # Arguments passed to the task
    ).model_dump()


@router.post("/text")
def trigger_triage_text(req: email_schema.StringRequest):
    """
    Triggers an email triage process by sending the email text to Celery for processing.
    """
    # Convert the request Pydantic model to a dictionary (payload)
    payload = req.model_dump()
    # Send the task to Celery for processing, using the task name (string) and payload
    method = "email_triage_with_text"
    task = celery.send_task(method, args=[payload])

    # Return the task details (task ID, method, and arguments) as a response
    return celery_schema.CeleryResponse(
        task_id=task.id,
        method=[method],  # The task method
        arguments=payload  # Arguments passed to the task
    ).model_dump()

@router.post("/file")
def trigger_triage_file(file: UploadFile = File(...)):
    allowed_types = {"application/pdf", "image/jpeg", "image/png"}
    
    print(f"Received file: {file.filename}, Content-Type: {file.content_type}")
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    try:
        text = file_service.convert_file_to_string(file)
        print(f"Extracted text length: {len(text)}")
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Failed to extract text from file: {str(e)}")

    payload = {"text": text}

    method = "email_triage_with_text" 
    task = celery.send_task(method, args=[payload])

    return celery_schema.CeleryResponse(
        task_id=task.id,
        method=[method],    # Fixed: should be a list to match schema
        arguments=payload   # dict of strings/JSON-safe types
    ).model_dump()

@router.post("/chat")
def chat(req: chat_schema.Conversation):
    payload: Dict[str, Any] = req.model_dump()
    method = "chat_with_conversation"
    result = orchestrator.chatbot_response(payload)
    return result

@router.get("/tasks/{task_id}")
def task_status(task_id: str):
    r = celery.AsyncResult(task_id)
    return {"state": r.state, "result": (r.result if r.ready() else None)}
