from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FeasibilityInput(BaseModel):
    business_id: str
    capex: float
    opex: float
    market_score: float
    entrepreneur_experience_years: float


class FeasibilityOutput(BaseModel):
    overall_score: float = 0.0
    viability_status: str = "pending"
    risk_factors: List[str] = Field(default_factory=list)
    confidence_interval: float = 0.0
