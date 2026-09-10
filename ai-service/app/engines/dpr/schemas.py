from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DPRDocumentRequest(BaseModel):
    business_id: str
    scheme_code: str = "PMEGP"
    language_code: str = "en"


class DPRDocumentMetadata(BaseModel):
    document_id: str
    title: str
    pages: int = 0
    file_format: str = "pdf"
    status: str = "scaffold"
