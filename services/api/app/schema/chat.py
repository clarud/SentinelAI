from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class HistoryItem(BaseModel):
    role: str
    content: str    

class Conversation(BaseModel):
    context: str
    current_input: str
    history: List[HistoryItem]

class ChatRequest(BaseModel):
    conversation: Conversation