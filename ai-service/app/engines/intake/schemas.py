from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RawIntakePayload(BaseModel):
    user_id: Optional[str] = None
    input_type: str = "text"  # "voice" or "text"
    raw_content: str
    language_hint: Optional[str] = "hi"


class ExtractedIntakeProfile(BaseModel):
    detected_language: str = "hi"
    transcription: str = ""
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
