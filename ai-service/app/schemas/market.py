from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SpatialAnalysisRequest(BaseModel):
    business_id: str
    latitude: float
    longitude: float
    radius_km: float = 5.0
    sector_category: str


class MarketIntelligenceResponse(BaseModel):
    business_id: str
    competitor_count: int
    saturation_level: str
    estimated_monthly_demand: float
    nearest_infrastructure: Dict[str, Optional[float]] = Field(default_factory=dict)
