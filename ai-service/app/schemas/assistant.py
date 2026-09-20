"""
Pydantic Schemas for Stage 15: KALPA Personal AI Business Assistant.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    analysis_id: Optional[str] = Field(None, description="Analysis UUID")
    session_id: Optional[str] = Field(None, description="Session UUID")
    conversation_id: Optional[str] = Field(None, description="Conversation UUID (optional, generated if omitted)")
    business_id: Optional[str] = Field(None, description="Business UUID (optional)")
    message: str = Field(..., description="User message / question")
    language: Optional[str] = Field("en", description="User preferred language (en, hi, te, ta, etc.)")


class GroundingSourceItem(BaseModel):
    stage: int
    source: str
    field: str
    description: str


class AssistantChatResponse(BaseModel):
    conversation_id: str
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    user_message: str
    assistant_response: str
    intent: Optional[str] = "GENERAL_BUSINESS_QUESTION"
    language: str = "en"
    grounded_sources: List[Dict[str, Any]] = []
    grounding_status: str = "GROUNDED"
    pipeline_completeness: float = 0.0
    intent_completeness: float = 0.0
    suggested_actions: List[str] = []
    message_index: int = 0
    business_status: str = "PRE_LAUNCH"
    model_provider: Optional[str] = None
    model_used: bool = False


class ConversationHistoryItem(BaseModel):
    id: str
    conversation_id: Optional[str] = None
    user_message: str
    assistant_response: Optional[str] = None
    intent: Optional[str] = None
    language: str = "en"
    grounded_sources: List[Dict[str, Any]] = []
    suggested_actions: List[str] = []
    message_index: Optional[int] = 0
    created_at: Optional[str] = None


class AssistantHistoryResponse(BaseModel):
    target_id: str
    messages: List[ConversationHistoryItem] = []


class AssistantContextResponse(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    pipeline_completeness: float = 0.0
    context: Dict[str, Any]


class AssistantSTTResponse(BaseModel):
    success: bool = True
    text: str
    language: str = "en"
    detected_language: Optional[str] = None


class AssistantTTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize to speech")
    language: Optional[str] = Field("hi", description="Language code (hi, en, te, ta, mr, bn, etc.)")
    speaker: Optional[str] = Field("shreya", description="Voice speaker profile (default: shreya)")


class AssistantTTSResponse(BaseModel):
    success: bool = True
    audio_base64: str
    format: str = "audio/wav"
    mime_type: str = "audio/wav"
    language_code: Optional[str] = None
    speaker: Optional[str] = "shreya"
    spoken_text: Optional[str] = None
    chunk_count: Optional[int] = 1


