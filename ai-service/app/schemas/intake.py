from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TextInputRequest(BaseModel):
    text: str = Field(..., description="User vernacular or English business description")
    language_code: Optional[str] = Field(default=None, description="Optional ISO code override (e.g. 'kn', 'hi', 'en', 'mr')")
    user_id: Optional[str] = None
    selected_language: Optional[str] = Field(default=None, description="Manually selected UI language")


class VoiceIntakeRequest(BaseModel):
    language_code: Optional[str] = Field(default=None, description="Optional language hint for STT")
    user_id: Optional[str] = None
    selected_language: Optional[str] = Field(default=None, description="Manually selected UI language")


class ContinueIntakeRequest(BaseModel):
    intake_id: Optional[str] = Field(default=None, description="Active intake session UUID (alias for session_id)")
    session_id: Optional[str] = Field(default=None, description="Active intake session UUID")
    answers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Structured answers for missing fields")
    text: Optional[str] = Field(default=None, description="Conversational text response to follow-up")
    field: Optional[str] = Field(default=None, description="Specific field being answered")
    language_code: Optional[str] = Field(default=None, description="Current language code")
    gps_location: Optional[Dict[str, Any]] = Field(default=None, description="Optional browser GPS coordinates / location")


class LocationData(BaseModel):
    name: str = Field(default="", description="Village, Town, City or Location phrase")
    district: str = Field(default="", description="District name")
    state: str = Field(default="", description="State name")
    country: str = Field(default="India")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    source: str = Field(default="unresolved", description="'user' | 'gps' | 'unresolved'")


class ExistingBusinessData(BaseModel):
    exists: bool = False
    type: str = Field(default="")
    current_status: str = Field(default="")


class NextActionOption(BaseModel):
    label: str
    value: str


class NextAction(BaseModel):
    type: str = Field(default="complete", description="'clarification' | 'complete'")
    field: Optional[str] = Field(default=None, description="Missing field needing clarification")
    question: Optional[str] = Field(default="", description="Localized clarification question")
    helper_text: Optional[str] = Field(default="", description="Localized helper guidance")
    language: str = Field(default="en", description="Language code for the question")
    input_modes: List[str] = Field(default_factory=lambda: ["text", "voice"])
    tts_supported: bool = True
    options: Optional[List[NextActionOption]] = None


class LanguageDetail(BaseModel):
    detected: str = "English"
    code: str = "en"
    selected: str = "en"


# Target Stage 1 Data Contract Profile
class Stage1Profile(BaseModel):
    session_id: str
    original_input: str = ""
    input_mode: str = "text"  # "voice" | "text"

    detected_language: str = "English"
    language_code: str = "en"
    selected_language: Optional[str] = None

    business_concept: Optional[str] = None
    business_category_hint: Optional[str] = None

    intent: str = "unknown"  # "start_business" | "expand_business" | "existing_business" | "unknown"
    business_stage: str = "planning"  # "idea" | "planning" | "existing"

    available_capital: Optional[int] = None
    capital_currency: str = "INR"

    proposed_location: LocationData = Field(default_factory=LocationData)

    entrepreneur_skills: List[str] = Field(default_factory=list)
    skills_status: str = "unspecified"  # "collected" | "no_experience" | "unspecified"

    existing_business: ExistingBusinessData = Field(default_factory=ExistingBusinessData)

    missing_fields: List[str] = Field(default_factory=list)
    clarification_history: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: Dict[str, float] = Field(default_factory=dict)

    stage_1_complete: bool = False

    # Backwards-compatibility helper properties for nested lookups
    @property
    def intake_id(self) -> str:
        return self.session_id


class Stage1IntakeResponse(BaseModel):
    success: bool = True
    session_id: str
    language: LanguageDetail
    profile: Stage1Profile
    missing_fields: List[str] = Field(default_factory=list)
    next_action: NextAction


class VoiceIntakeResponse(BaseModel):
    success: bool = True
    transcript: str
    session_id: str
    language: LanguageDetail
    profile: Stage1Profile
    missing_fields: List[str] = Field(default_factory=list)
    next_action: NextAction


# Legacy compatibility schema models
class LanguageInfo(BaseModel):
    language_code: str = "en"
    language_name: str = "English"


class InputMetadata(BaseModel):
    input_type: str = "text"
    original_text: str = ""
    normalized_text: str = ""
    language_code: str = "en"
    language_name: str = "English"


class IntentInfo(BaseModel):
    primary_intent: str = "start_new_business"
    business_stage: str = "planning"


class BusinessInfo(BaseModel):
    business_idea: Optional[str] = None
    business_description: Optional[str] = None
    product_service: Optional[str] = None
    products: List[str] = Field(default_factory=list)


class EntrepreneurInfo(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = None


class FinancialInfo(BaseModel):
    capital_available: Optional[int] = None
    currency: str = "INR"
    investment_capacity: Optional[str] = None


class LocationInfo(BaseModel):
    village: Optional[str] = None
    town: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    mentioned_location: Optional[str] = None


class FollowUpQuestion(BaseModel):
    field: str
    question: str


class UserIntakeProfile(BaseModel):
    intake_id: str
    input: InputMetadata
    intent: IntentInfo
    business: BusinessInfo
    entrepreneur: EntrepreneurInfo
    financial: FinancialInfo
    location: LocationInfo
    requirements: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    follow_up_questions: List[FollowUpQuestion] = Field(default_factory=list)
    pipeline_status: str = "completed"
    # Stage 1 enhanced fields
    session_id: Optional[str] = None
    profile: Optional[Stage1Profile] = None
    next_action: Optional[NextAction] = None
