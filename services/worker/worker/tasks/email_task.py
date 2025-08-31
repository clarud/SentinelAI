from typing import Dict, Any
from worker.celery_app import celery
# from worker.agents.orchestrator import assess_email

@celery.task(name="email_triage")
def triage_email(email: Dict[str, Any]) -> Dict[str, Any]:
    """
    email = { user_id, message_id, thread_id?, sender, subject, text, urls[], attachments[] }
    """
    print("Task triage_email received email:", email)
    result = "placeholder result"
    # result = assess_email(email)  # returns RiskAssessment dict
    return {**email, "assessment": result}
