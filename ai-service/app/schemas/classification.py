from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BusinessClassificationRequest(BaseModel):
    business_description: str
    context_tags: List[str] = Field(default_factory=list)


class NICCodeMatch(BaseModel):
    nic_code: str
    title: str
    digit_level: int
    confidence: float


class BusinessClassificationResponse(BaseModel):
    primary_category: str
    sub_category: str
    confidence_score: float
    matched_nic_codes: List[NICCodeMatch] = Field(default_factory=list)
    ontology_mappings: Dict[str, Any] = Field(default_factory=dict)
