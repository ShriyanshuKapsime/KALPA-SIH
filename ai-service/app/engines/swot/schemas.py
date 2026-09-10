from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SWOTInput(BaseModel):
    business_id: str
    location_attributes: Dict[str, Any] = Field(default_factory=dict)
    financial_ratios: Dict[str, Any] = Field(default_factory=dict)
    entrepreneur_attributes: Dict[str, Any] = Field(default_factory=dict)


class SWOTMatrix(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
