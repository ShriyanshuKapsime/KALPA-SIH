from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ClassificationInput(BaseModel):
    raw_description: str
    inferred_sector: Optional[str] = None


class ClassificationOutput(BaseModel):
    nic_2_digit: Optional[str] = None
    nic_5_digit: Optional[str] = None
    industry_title: Optional[str] = None
    confidence_score: float = 0.0
    matched_ontology_tags: List[str] = Field(default_factory=list)
