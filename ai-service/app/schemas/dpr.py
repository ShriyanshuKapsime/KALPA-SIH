from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DPRGenerationRequest(BaseModel):
    business_id: str
    target_scheme: str = "PMEGP"  # PMEGP, PMMY_MUDRA, STANDUP_INDIA
    report_format: str = "pdf"


class DPRGenerationResponse(BaseModel):
    report_id: str
    business_id: str
    status: str
    download_url: Optional[str] = None
    executive_summary: str
    financial_highlights: Dict[str, Any] = Field(default_factory=dict)
