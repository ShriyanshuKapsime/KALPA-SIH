from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EntrepreneurProfileCreate(BaseModel):
    user_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    education_level: Optional[str] = None
    caste_category: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    sub_district_block: Optional[str] = None
    village_town: Optional[str] = None
    pincode: Optional[str] = None
    prior_experience_years: float = 0.0
    primary_skills: List[str] = Field(default_factory=list)
    risk_appetite: str = "moderate"
    available_own_capital: float = 0.0


class BusinessProfileCreate(BaseModel):
    entrepreneur_id: str
    business_name: Optional[str] = None
    venture_description: str
    target_scale: str = "micro"
    proposed_investment: float = 0.0
    location_pincode: Optional[str] = None
    location_district: Optional[str] = None
    location_state: Optional[str] = None
