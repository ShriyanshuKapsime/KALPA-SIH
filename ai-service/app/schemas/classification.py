from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class InputSummary(BaseModel):
    business_concept: Optional[str] = None
    original_language: str = "en"
    normalized_business_concept: Optional[str] = None


class ConfidenceBreakdown(BaseModel):
    ontology_match: float = 0.0
    nic_activity_match: float = 0.0
    hierarchy_consistency: float = 0.0
    profile_context_consistency: float = 0.0
    candidate_separation: float = 0.0


class DeterministicConfidence(BaseModel):
    score: float = 0.0
    percentage: int = 0
    level: str = "HIGH"  # "HIGH" | "MEDIUM" | "LOW" | "INSUFFICIENT_CONFIDENCE"
    breakdown: Optional[ConfidenceBreakdown] = None


class NICSection(BaseModel):
    code: str
    title: str


class NICDivision(BaseModel):
    code: str
    title: str


class NICGroup(BaseModel):
    code: str
    title: str


class NICClass(BaseModel):
    code: str
    title: str


class NICSubclass(BaseModel):
    code: str
    title: str


class NICActivity(BaseModel):
    code: str
    official_title: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class TopCandidateRank(BaseModel):
    rank: int
    code: str
    title: str
    score: float


class OfficialNICHierarchy(BaseModel):
    version: str = "NIC-2008"
    section: Optional[NICSection] = None
    division: Optional[NICDivision] = None
    group: Optional[NICGroup] = None
    class_: Optional[NICClass] = Field(default=None, alias="class")
    subclass: Optional[NICSubclass] = None
    activity: Optional[NICActivity] = None

    model_config = {
        "populate_by_name": True
    }


class OfficialClassification(BaseModel):
    classification_status: str = "verified"  # "verified" | "needs_clarification"
    nic: Optional[OfficialNICHierarchy] = None
    confidence: Optional[DeterministicConfidence] = None
    top_candidates: List[TopCandidateRank] = Field(default_factory=list)


class OrchestratorContext(BaseModel):
    profile_ready: bool = True
    classification_verified: bool = True
    recommended_next_stage: str = "market_intelligence"
    business_activity: str
    official_nic_code: str
    nic_version: str = "NIC-2008"
    sector: str
    category: str
    location: Dict[str, Any] = Field(default_factory=dict)
    available_capital: int = 0
    skills: List[str] = Field(default_factory=list)
    language: str = "en"
    classification_confidence: float = 0.0


class LayerANIC(BaseModel):
    nic_code: str
    nic_description: str
    division: Optional[str] = None
    division_name: Optional[str] = None
    group: Optional[str] = None
    group_name: Optional[str] = None
    class_: Optional[str] = Field(default=None, alias="class")
    class_name: Optional[str] = None
    subclass: Optional[str] = None
    subclass_title: Optional[str] = None
    section: Optional[str] = None
    section_name: Optional[str] = None
    confidence: float = 0.0
    status: str = "confirmed"

    model_config = {
        "populate_by_name": True
    }


class LayerBOntology(BaseModel):
    sector: str
    category: str
    sub_category: Optional[str] = None
    subcategory: Optional[str] = None
    specific_business: str
    products: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class CandidateItem(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    score: Optional[float] = None


class ClarificationOption(BaseModel):
    label: str
    value: str


class ClarificationCard(BaseModel):
    field: str = "specific_business"
    question: str
    language: str = "en"
    options: List[ClarificationOption] = Field(default_factory=list)
    input_modes: List[str] = Field(default_factory=lambda: ["options", "text", "voice"])


class LocationProfile(BaseModel):
    name: Optional[str] = ""
    district: Optional[str] = ""
    state: Optional[str] = ""
    country: Optional[str] = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = "user_provided"


class StructuredEntrepreneurProfile(BaseModel):
    location: LocationProfile = Field(default_factory=LocationProfile)
    capital_available: Optional[int] = 0
    skills: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)


class NICSummary(BaseModel):
    code: str
    description: str
    division: Optional[str] = None
    group: Optional[str] = None


class StructuredBusinessDetails(BaseModel):
    user_business_description: Optional[str] = ""
    normalized_business_concept: Optional[str] = ""
    sector: str
    category: str
    sub_category: Optional[str] = ""
    specific_business: str
    products: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    nic: Optional[NICSummary] = None


class StructuredClassificationMeta(BaseModel):
    language: str = "en"
    confidence: float = 0.0
    classification_status: str = "complete"


class StructuredBusinessProfile(BaseModel):
    business_id: Optional[str] = None
    session_id: Optional[str] = None
    entrepreneur_profile: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None
    classification_metadata: Optional[Dict[str, Any]] = None


class ClassificationResult(BaseModel):
    success: bool = True
    session_id: Optional[str] = None
    classification_status: str = "complete"  # "complete" | "needs_clarification"
    input_summary: InputSummary
    layer_a_nic: Optional[LayerANIC] = None
    layer_b_ontology: Optional[LayerBOntology] = None
    official_classification: Optional[OfficialClassification] = None
    orchestrator_context: Optional[OrchestratorContext] = None
    classification_confidence: float = 0.0
    confidence_level: Optional[str] = "HIGH"
    confidence_breakdown: Optional[Dict[str, float]] = None
    clarification_needed: bool = False
    clarification: Optional[ClarificationCard] = None
    candidate_summary: List[CandidateItem] = Field(default_factory=list)
    structured_business_profile: Optional[Dict[str, Any]] = None
    canonical_profile: Optional[Dict[str, Any]] = None


class BusinessClassificationRequest(BaseModel):
    session_id: Optional[str] = None
    intake_id: Optional[str] = None
    business_concept: Optional[str] = None
    original_input: Optional[str] = None
    original_text: Optional[str] = None
    business_description: Optional[str] = None
    text: Optional[str] = None
    language_code: Optional[str] = "en"
    product_service: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None


class ClarifyClassificationRequest(BaseModel):
    session_id: str
    answer: str
    language_code: Optional[str] = "en"


# Legacy compatibility models
class NICCodeMatch(BaseModel):
    nic_code: str
    title: str
    digit_level: int = 5
    confidence: float = 0.0


class BusinessClassificationResponse(BaseModel):
    primary_category: str
    sub_category: str
    confidence_score: float
    matched_nic_codes: List[NICCodeMatch] = Field(default_factory=list)
    ontology_mappings: Dict[str, Any] = Field(default_factory=dict)
