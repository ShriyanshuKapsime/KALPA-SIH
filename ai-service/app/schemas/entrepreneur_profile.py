from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EntrepreneurSkillsInput(BaseModel):
    skills: List[str] = Field(default_factory=list, description="List of technical, vocational, or trade skills reported by the entrepreneur")
    certified_skills: List[str] = Field(default_factory=list, description="Formally certified skills (e.g. ITI, PMKVY)")
    skill_level: Optional[str] = Field(default=None, description="NOVICE | INTERMEDIATE | EXPERT")


class EntrepreneurExperienceInput(BaseModel):
    years_of_experience: Optional[float] = Field(default=None, description="Total years of direct or related domain experience")
    domain: Optional[str] = Field(default=None, description="Domain or trade in which experience was gained")
    prior_business_ownership: Optional[bool] = Field(default=None, description="Whether the entrepreneur previously owned a venture")
    description: Optional[str] = Field(default=None, description="User reported narrative of past work")


class EntrepreneurTrainingInput(BaseModel):
    has_formal_training: Optional[bool] = Field(default=None, description="Whether the entrepreneur underwent vocational or scheme training")
    certifications: List[str] = Field(default_factory=list, description="List of completed training certificates (e.g., FoSTaC, PMKVY, EDP)")
    willing_to_undergo_training: Optional[bool] = Field(default=True, description="Willingness to take up prerequisite training")


class EntrepreneurResourcesInput(BaseModel):
    land_or_premises_available: Optional[bool] = Field(default=None, description="Whether physical land or commercial shed is available")
    available_area_sqft: Optional[float] = Field(default=None, description="Available carpet area in square feet")
    premises_ownership: Optional[str] = Field(default=None, description="OWNED | RENTED | LEASED | NONE")
    power_connection_type: Optional[str] = Field(default=None, description="SINGLE_PHASE | THREE_PHASE_COMMERCIAL | DOMESTIC | NONE")
    existing_machinery: List[str] = Field(default_factory=list, description="List of existing machines or equipment owned")
    has_water_supply: Optional[bool] = Field(default=None, description="Reliable water supply availability")


class EntrepreneurOperationsInput(BaseModel):
    commitment_type: Optional[str] = Field(default=None, description="FULL_TIME | PART_TIME | SEASONAL")
    daily_hours_available: Optional[float] = Field(default=None, description="Hours per day dedicated to the venture")
    available_family_helpers: Optional[int] = Field(default=0, description="Number of family members assisting operation")
    hired_workers_planned: Optional[int] = Field(default=0, description="Planned hired workforce")


class UserEntrepreneurProfile(BaseModel):
    skills: EntrepreneurSkillsInput = Field(default_factory=EntrepreneurSkillsInput)
    experience: EntrepreneurExperienceInput = Field(default_factory=EntrepreneurExperienceInput)
    training: EntrepreneurTrainingInput = Field(default_factory=EntrepreneurTrainingInput)
    resources: EntrepreneurResourcesInput = Field(default_factory=EntrepreneurResourcesInput)
    operations: EntrepreneurOperationsInput = Field(default_factory=EntrepreneurOperationsInput)
    available_capital: Optional[float] = Field(default=None, description="Available margin money from user in INR")


class ClarificationQuestion(BaseModel):
    field: str
    question_en: str
    question_hi: str
    question_kn: Optional[str] = None
    input_type: str = "text"  # text | number | select | boolean | voice
    suggested_options: List[str] = Field(default_factory=list)
    importance: str = "HIGH"  # CRITICAL | HIGH | MEDIUM


class ComponentScore(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Deterministic component score between 0 and 100")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight of component in overall readiness")
    status: str = "ADEQUATE"  # STRONG | ADEQUATE | DEVELOPING | DEFICIENT | UNKNOWN
    evidence: str = ""
    matched_items: List[str] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class ReadinessGap(BaseModel):
    dimension: str  # SKILLS | EXPERIENCE | TRAINING | RESOURCES | OPERATIONS
    gap_description: str
    severity: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL
    required_intervention: str
    benchmark_reference: Optional[str] = None


class RequiredSupportItem(BaseModel):
    category: str  # TRAINING | INFRASTRUCTURE | SCHEME | ADVISORY | MENTORSHIP
    title: str
    description: str
    scheme_or_program_link: Optional[str] = None
    priority: str = "HIGH"  # IMMEDIATE | HIGH | MEDIUM | OPTIONAL


class ProvenanceRecord(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    engine: str = "STAGE_10_ENTREPRENEUR_PROFILE_ENGINE"
    version: str = "1.0.0"
    evaluation_type: str = "DETERMINISTIC_RULES"
    benchmark_node_id: Optional[str] = None
    data_sources: List[str] = Field(default_factory=lambda: ["user_intake", "business_ontology", "knowledge_database"])


class EntrepreneurProfileRequest(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    user_profile: Optional[UserEntrepreneurProfile] = None
    entrepreneur_profile: Optional[Dict[str, Any]] = None  # Flexible dictionary format from Stage 1/3
    business_profile: Optional[Dict[str, Any]] = None
    location_profile: Optional[Dict[str, Any]] = None
    financial_profile: Optional[Dict[str, Any]] = None


class EntrepreneurReadinessResponse(BaseModel):
    success: bool = True
    status: str = "READY"  # READY | PROFILE_INCOMPLETE
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    business_title: str = "Target Micro-Enterprise"
    business_node_id: Optional[str] = None
    readiness_score: float = Field(0.0, ge=0.0, le=100.0)
    readiness_level: str = "UNKNOWN"  # HIGH | MODERATE | DEVELOPING | LOW | INCOMPLETE | UNKNOWN
    component_scores: Dict[str, ComponentScore] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[ReadinessGap] = Field(default_factory=list)
    required_support: List[RequiredSupportItem] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    questions: List[ClarificationQuestion] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    provenance: ProvenanceRecord = Field(default_factory=ProvenanceRecord)
