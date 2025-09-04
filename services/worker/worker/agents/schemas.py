# services/worker/worker/agents/schemas.py
from pydantic import BaseModel, Field
from typing import List

class Highlight(BaseModel):
    start: int
    end: int
    reason: str

class RiskAssessment(BaseModel):
    is_scam: str                       # "scam" | "not_scam"
    confidence_level: float = Field(ge=0, le=1)
    scam_probability: float = Field(ge=0, le=100)
    explanation: str
    text: str
