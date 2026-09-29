from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NICHierarchyNode(BaseModel):
    code: str = ""
    name: str = ""


class NICDetails(BaseModel):
    code: str = ""
    description: str = ""
    division: NICHierarchyNode = Field(default_factory=NICHierarchyNode)
    group: NICHierarchyNode = Field(default_factory=NICHierarchyNode)
    class_node: NICHierarchyNode = Field(default_factory=NICHierarchyNode, alias="class")
    classification_status: str = "verified"
    confidence: float = 0.0

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True
    }


class BusinessProfileSection(BaseModel):
    business_id: Optional[str] = None
    business_node_id: Optional[str] = None
    business_activity: Optional[str] = None
    nic_code: Optional[str] = None
    nic_description: Optional[str] = None
    legal_constitution: Optional[str] = None
    constitution: Optional[str] = None
    original_concept: str = ""
    normalized_concept: str = ""
    sector: str = ""
    category: str = ""
    sub_category: str = ""
    specific_business: str = ""
    nic: NICDetails = Field(default_factory=NICDetails)
    products: Any = Field(default_factory=list)
    services: Any = Field(default_factory=list)


class EntrepreneurProfileSection(BaseModel):
    skills: Any = Field(default_factory=list)
    experience: Any = Field(default_factory=list)
    resources: Any = Field(default_factory=list)
    business_stage: str = "planning"


class CoordinatesSection(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


class LocationProfileSection(BaseModel):
    name: str = ""
    village: Optional[str] = None
    block: Optional[str] = None
    district: str = ""
    state: str = ""
    country: str = "India"
    coordinates: CoordinatesSection = Field(default_factory=CoordinatesSection)
    source: str = "user"


class FinancialProfileSection(BaseModel):
    available_capital: Optional[float] = None
    currency: str = "INR"


class AnalysisRequirementsSection(BaseModel):
    direct_competitors: List[str] = Field(default_factory=list)
    adjacent_competitors: List[str] = Field(default_factory=list)
    substitute_businesses: List[str] = Field(default_factory=list)
    demand_features: List[str] = Field(default_factory=list)
    infrastructure_requirements: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    required_datasets: List[str] = Field(default_factory=list)


class DataQualitySection(BaseModel):
    profile_complete: bool = False
    missing_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validation_status: str = "PENDING"


class ProvenanceSection(BaseModel):
    stage_1_session_id: str = ""
    classification_id: Optional[str] = None
    language: str = "en"
    input_mode: str = "text"


class WorkflowSection(BaseModel):
    state: str = "BUSINESS_PROFILE_READY"
    stage_completed: int = 3
    created_at: str = ""
    updated_at: str = ""


class CanonicalBusinessProfile(BaseModel):
    """
    Stage 3 Canonical Structured Business Profile:
    The single authoritative source of truth for KALPA downstream stages.
    """
    schema_version: str = "1.0"
    profile_version: int = 1
    analysis_id: str
    session_id: str
    user_id: Optional[str] = None

    workflow: WorkflowSection = Field(default_factory=WorkflowSection)
    business_profile: BusinessProfileSection = Field(default_factory=BusinessProfileSection)
    entrepreneur_profile: EntrepreneurProfileSection = Field(default_factory=EntrepreneurProfileSection)
    location_profile: LocationProfileSection = Field(default_factory=LocationProfileSection)
    financial_profile: FinancialProfileSection = Field(default_factory=FinancialProfileSection)
    analysis_requirements: AnalysisRequirementsSection = Field(default_factory=AnalysisRequirementsSection)
    data_quality: DataQualitySection = Field(default_factory=DataQualitySection)
    provenance: ProvenanceSection = Field(default_factory=ProvenanceSection)

    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True
    }


class BuildProfileRequest(BaseModel):
    session_id: str


class BuildProfileResponse(BaseModel):
    success: bool = True
    analysis_id: str
    session_id: str
    workflow_state: str
    profile: CanonicalBusinessProfile


# Legacy compatibility models
class EntrepreneurProfileCreate(BaseModel):
    user_id: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: int = 0


class BusinessProfileCreate(BaseModel):
    business_name: Optional[str] = None
    specific_business: Optional[str] = None
