from typing import Dict, Any
from worker.worker.celery_app import celery
from worker.worker.agents import orchestrator

@celery.task(name="email_triage_with_email")
def triage_email(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    email = { user_id, message_id, thread_id?, sender, subject, text, urls[], attachments[] }
    """
    print("Task triage_email received email:", email)
    result = orchestrator.assess_document(email)  # returns RiskAssessment dict
    print("Assessment result:", result)
    return {**email, "assessment": result}

@celery.task(name="email_triage_with_text")
def triage_email_text(text: Dict[str, str]) -> Dict[str, Any]:
    """
    email = { user_id, message_id, thread_id?, sender, subject, text, urls[], attachments[] }
    """
    text = text.get("text", "")
    print("Task triage_string received :", text)
    result = orchestrator.assess_document(text)  # returns RiskAssessment dict
    print("Assessment result:", result)
    return {"text": text, "assessment": result}

