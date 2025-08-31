# services/worker/worker/agents/schemas.py
from pydantic import BaseModel, Field
from typing import List

class Highlight(BaseModel):
    start: int
    end: int
    reason: str

# class RiskAssessment(BaseModel):
#     verdict: str                      # "safe" | "suspicious" | "scam"
#     confidence: float = Field(ge=0, le=1)
#     score: float = Field(ge=0, le=100)
#     factors: List[str] = []
#     highlights: List[Highlight] = []

class RiskAssessment(BaseModel):
    is_scam: str                       # "scam" | "not_scam"
    confidence_level: float = Field(ge=0, le=1)
    scam_probability: float = Field(ge=0, le=100)
    explanation: str
