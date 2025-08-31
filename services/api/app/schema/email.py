from pydantic import BaseModel


class EmailRequest(BaseModel):
    to: str
    sender: str
    subject: str
    date: str
    message_id: str
    body: str 
