from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class EmailData(BaseModel):
    id: str
    sender: str
    subject: str
    date: str
    to: str
    snippet: str
    threadId: str
    body: str
    body_preview: str
    email_address: str