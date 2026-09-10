from typing import Optional, List
from pydantic import BaseModel, Field


class OpportunityQuery(BaseModel):
    district: str
    state: str
    target_sector: Optional[str] = None


class OpportunityResult(BaseModel):
    top_opportunities: List[str] = Field(default_factory=list)
    growth_drivers: List[str] = Field(default_factory=list)
    overall_rating: str = "medium"
