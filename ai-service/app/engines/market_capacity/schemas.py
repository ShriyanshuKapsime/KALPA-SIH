from typing import Optional, Dict, Any
from pydantic import BaseModel


class MarketCapacityRequest(BaseModel):
    sector_code: str
    target_pincode: str
    proposed_monthly_units: float


class MarketCapacityResponse(BaseModel):
    total_estimated_demand_units: float = 0.0
    existing_supply_units: float = 0.0
    unmet_gap_units: float = 0.0
    saturation_ratio: float = 0.0
