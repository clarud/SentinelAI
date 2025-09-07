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

class Message(BaseModel):
    data: str
    messageId: str
    message_id: str
    publishTime: str
    publish_time: str

class NotificationRequest(BaseModel):
    message: Message
    subscription: str
    challenge: Optional[str] = None

class NotificationResponse(BaseModel):
    status: str
    email: Optional[str] = None
    history_id: Optional[str] = None
    processed_message_id: Optional[list[str]] = None
    email_data: Optional[EmailData] = None
    task_id: Optional[str] = None

class StringRequest(BaseModel):
    text: str