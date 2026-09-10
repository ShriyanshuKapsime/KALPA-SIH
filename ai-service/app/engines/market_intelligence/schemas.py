from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MarketIntelligenceQuery(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 5.0
    nic_code: Optional[str] = None


class MarketIntelligenceSummary(BaseModel):
    radius_km: float = 5.0
    competitor_density: float = 0.0
    catchment_population: int = 0
    spatial_features: Dict[str, Any] = Field(default_factory=dict)
