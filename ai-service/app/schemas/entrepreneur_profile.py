from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone


class EntrepreneurSkillsInput(BaseModel):
    skills: List[str] = Field(default_factory=list, description="List of technical, vocational, or trade skills reported by the entrepreneur")
    certified_skills: List[str] = Field(default_factory=list, description="Formally certified skills (e.g. ITI, PMKVY)")
    skill_level: Optional[str] = Field(default=None, description="NOVICE | INTERMEDIATE | EXPERT")
    source: Optional[str] = "USER_INPUT"


class EntrepreneurExperienceInput(BaseModel):
    years_of_experience: Optional[float] = Field(default=None, description="Total years of direct or related domain experience")
    domain: Optional[str] = Field(default=None, description="Domain or trade in which experience was gained")
    prior_business_ownership: Optional[bool] = Field(default=None, description="Whether the entrepreneur previously owned a venture")
    description: Optional[str] = Field(default=None, description="User reported narrative of past work")
    source: Optional[str] = "USER_INPUT"


class EntrepreneurTrainingInput(BaseModel):
    has_formal_training: Optional[bool] = Field(default=None, description="Whether the entrepreneur underwent vocational or scheme training")
    certifications: List[str] = Field(default_factory=list, description="List of completed training certificates (e.g., FoSTaC, PMKVY, EDP)")
    willing_to_undergo_training: Optional[bool] = Field(default=True, description="Willingness to take up prerequisite training")
    source: Optional[str] = "USER_INPUT"


class EntrepreneurResourcesInput(BaseModel):
    land_or_premises_available: Optional[bool] = Field(default=None, description="Whether physical land or commercial shed is available")
    available_area_sqft: Optional[float] = Field(default=None, description="Available carpet area in square feet")
    premises_ownership: Optional[str] = Field(default=None, description="OWNED | RENTED | LEASED | NONE")
    power_connection_type: Optional[str] = Field(default=None, description="SINGLE_PHASE | THREE_PHASE_COMMERCIAL | DOMESTIC | NONE")
    existing_machinery: List[str] = Field(default_factory=list, description="List of existing machines or equipment owned")
    has_water_supply: Optional[bool] = Field(default=None, description="Reliable water supply availability")
    source: Optional[str] = "USER_INPUT"


class EntrepreneurOperationsInput(BaseModel):
    commitment_type: Optional[str] = Field(default=None, description="FULL_TIME | PART_TIME | SEASONAL")
    daily_hours_available: Optional[float] = Field(default=None, description="Hours per day dedicated to the venture")
    available_family_helpers: Optional[int] = Field(default=0, description="Number of family members assisting operation")
    hired_workers_planned: Optional[int] = Field(default=0, description="Planned hired workforce")
    source: Optional[str] = "USER_INPUT"


class UserEntrepreneurProfile(BaseModel):
    skills: EntrepreneurSkillsInput = Field(default_factory=EntrepreneurSkillsInput)
    experience: EntrepreneurExperienceInput = Field(default_factory=EntrepreneurExperienceInput)
    training: EntrepreneurTrainingInput = Field(default_factory=EntrepreneurTrainingInput)
    resources: EntrepreneurResourcesInput = Field(default_factory=EntrepreneurResourcesInput)
    operations: EntrepreneurOperationsInput = Field(default_factory=EntrepreneurOperationsInput)
    available_capital: Optional[float] = Field(default=None, description="Available margin money from user in INR")
    answered_fields: List[str] = Field(default_factory=list, description="List of fields permanently answered by entrepreneur")


class ClarificationQuestion(BaseModel):
    field: str
    question: str = ""
    question_en: str = ""
    question_hi: Optional[str] = None
    question_kn: Optional[str] = None
    input_type: Union[str, List[str]] = "text"  # text | number | select | boolean | voice
    suggested_options: List[str] = Field(default_factory=list)
    priority: str = "HIGH"  # CRITICAL | HIGH | MEDIUM | LOW
    importance: str = "HIGH"  # Backward compatibility
    reason: Optional[str] = None
    benchmark: Optional[str] = None
    current_value: Optional[Any] = None

    @model_validator(mode="before")
    @classmethod
    def sync_question_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Canonicalize question prompt text
            q_text = (
                data.get("question")
                or data.get("question_en")
                or data.get("question_text")
                or data.get("prompt")
                or data.get("display_question")
                or data.get("label")
                or ""
            )
            data["question"] = q_text
            if not data.get("question_en"):
                data["question_en"] = q_text

            # Canonicalize priority / importance
            prio = data.get("priority") or data.get("importance") or "HIGH"
            data["priority"] = prio
            data["importance"] = prio

            # Default reason if not provided
            if not data.get("reason"):
                f_name = data.get("field", "field")
                data["reason"] = f"Required to evaluate deterministic entrepreneur {f_name} readiness."

            # Default benchmark if not provided
            if not data.get("benchmark"):
                f_name = data.get("field", "field")
                data["benchmark"] = f"Standard benchmark compliance for {f_name}"
        return data



class ComponentScore(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0, description="Deterministic component score between 0 and 100")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight of component in overall readiness")
    status: str = "ADEQUATE"  # STRONG | ADEQUATE | DEVELOPING | DEFICIENT | UNKNOWN
    evidence: Union[List[str], str] = ""
    evidence_source: str = "BENCHMARK_DATABASE"  # USER_INPUT | USER_CLARIFICATION | BENCHMARK_DATABASE | UNKNOWN
    benchmark_requirement: List[str] = Field(default_factory=list)
    matched_requirements: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    matched_items: List[str] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    gap: str = ""
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    calculation: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def sync_items_and_requirements(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "matched_requirements" in data and "matched_items" not in data:
                data["matched_items"] = data["matched_requirements"]
            elif "matched_items" in data and "matched_requirements" not in data:
                data["matched_requirements"] = data["matched_items"]
            if "missing_requirements" in data and "missing_items" not in data:
                data["missing_items"] = data["missing_requirements"]
            elif "missing_items" in data and "missing_requirements" not in data:
                data["missing_requirements"] = data["missing_items"]
        return data


class ReadinessGap(BaseModel):
    dimension: str  # SKILLS | EXPERIENCE | TRAINING | RESOURCES | OPERATIONS
    gap_description: str
    severity: str = "MEDIUM"  # LOW | MEDIUM | HIGH | CRITICAL
    required_intervention: str
    benchmark_reference: Optional[str] = None


class RequiredSupportItem(BaseModel):
    gap: str = ""
    priority: str = "HIGH"  # IMMEDIATE | HIGH | MEDIUM | OPTIONAL
    why_it_matters: str = ""
    recommended_action: str = ""
    resource_type: str = "LESSON"  # LESSON | CERTIFICATION | GOVERNMENT_SCHEME | ADVISORY | MENTORSHIP
    resource_title: str = ""
    summary: str = ""
    provider: str = ""
    official_url: Optional[str] = None
    estimated_duration: Optional[str] = None
    eligibility: Optional[str] = None
    source: str = "KNOWLEDGE_DATABASE"

    # Backward-compatible convenience fields for older frontend hooks
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scheme_or_program_link: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_support_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "title" not in data and "resource_title" in data:
                data["title"] = data["resource_title"]
            elif "resource_title" not in data and "title" in data:
                data["resource_title"] = data["title"]

            if "description" not in data and "summary" in data:
                data["description"] = data["summary"]
            elif "summary" not in data and "description" in data:
                data["summary"] = data["description"]

            if "scheme_or_program_link" not in data and "official_url" in data:
                data["scheme_or_program_link"] = data["official_url"]
            elif "official_url" not in data and "scheme_or_program_link" in data:
                data["official_url"] = data["scheme_or_program_link"]

            if "category" not in data and "resource_type" in data:
                data["category"] = data["resource_type"]
            elif "resource_type" not in data and "category" in data:
                data["resource_type"] = data["category"]
        return data


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
    overall_score: Optional[float] = None
    level: Optional[str] = None
    weights: Dict[str, float] = Field(default_factory=dict)
    components: Dict[str, Any] = Field(default_factory=dict)
    component_scores: Dict[str, ComponentScore] = Field(default_factory=dict)
    calculation_provenance: List[Dict[str, Any]] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[ReadinessGap] = Field(default_factory=list)
    required_support: List[RequiredSupportItem] = Field(default_factory=list)
    pending_fields: List[str] = Field(default_factory=list)
    answered_fields: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    questions: List[ClarificationQuestion] = Field(default_factory=list)
    pending_count: Optional[int] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    provenance: ProvenanceRecord = Field(default_factory=ProvenanceRecord)

    @model_validator(mode="before")
    @classmethod
    def sync_top_level_scores(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "overall_score" not in data and "readiness_score" in data:
                data["overall_score"] = data["readiness_score"]
            elif "readiness_score" not in data and "overall_score" in data:
                data["readiness_score"] = data["overall_score"]

            if "level" not in data and "readiness_level" in data:
                data["level"] = data["readiness_level"]
            elif "readiness_level" not in data and "level" in data:
                data["readiness_level"] = data["level"]

            if "components" not in data and "component_scores" in data:
                data["components"] = data["component_scores"]
            elif "component_scores" not in data and "components" in data:
                data["component_scores"] = data["components"]

            if "missing_fields" in data and "pending_fields" not in data:
                data["pending_fields"] = data["missing_fields"]
            elif "pending_fields" in data and "missing_fields" not in data:
                data["missing_fields"] = data["pending_fields"]

            # Synchronize pending_count
            if "pending_count" not in data or data.get("pending_count") is None:
                qs = data.get("questions") or []
                pf = data.get("pending_fields") or data.get("missing_fields") or []
                data["pending_count"] = max(len(qs), len(pf))
        return data
