from pydantic import BaseModel


class EmailRequest(BaseModel):
    sender: str
    subject: str
    date: str
    body: str 
