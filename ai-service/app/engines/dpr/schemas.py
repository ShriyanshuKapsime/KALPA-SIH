from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class DPRDocumentRequest(BaseModel):
    business_id: str
    session_id: Optional[str] = None
    analysis_id: Optional[str] = None
    scheme_code: str = "PMEGP"
    language_code: str = "en"
    target_scheme: Optional[str] = None
    report_format: str = "pdf"
    financial_package: Optional[Union[Dict[str, Any], Any]] = None
    non_financial_context: Optional[Dict[str, Any]] = None


class DPRDocumentMetadata(BaseModel):
    document_id: str
    title: str
    pages: int = 0
    file_format: str = "pdf"
    status: str = "generated"  # generated, incomplete_draft, scaffold
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    report_summary: Optional[str] = None
    completeness_status: str = "COMPLETE"
    is_dpr_eligible: bool = True
    financial_highlights: Dict[str, Any] = Field(default_factory=dict)
    dpr_package: Optional[Dict[str, Any]] = None
