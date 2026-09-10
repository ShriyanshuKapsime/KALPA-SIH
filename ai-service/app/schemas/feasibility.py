from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FeasibilityEvaluationRequest(BaseModel):
    business_id: str
    proposed_investment: float
    working_capital: float
    target_capacity_units: float


class DynamicSWOTResponse(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class FeasibilityEvaluationResponse(BaseModel):
    business_id: str
    overall_score: float
    viability_status: str
    ml_confidence: float
    swot: DynamicSWOTResponse
    pivot_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
