"""
Pydantic Schemas for Stage 6: Market Intelligence Engine.
Defines strict data models for Stage 5 input ingestion, deterministic indicators,
Stage 7 ML feature contracts, benchmark comparisons, and calculation provenance.
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class DataStatus(str, Enum):
    ACTUAL = "ACTUAL"
    PROXY = "PROXY"
    MISSING = "MISSING"
    UNAVAILABLE = "UNAVAILABLE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class CatchmentZone(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    EXTENDED = "EXTENDED"
    OUTSIDE = "OUTSIDE"


class CompetitivePressureLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class MarketCapacityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    SATURATED = "SATURATED"
    UNKNOWN = "UNKNOWN"


class DemandSignalStrength(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    EMERGING = "EMERGING"
    WEAK = "WEAK"
    UNKNOWN = "UNKNOWN"


class InfrastructureReadiness(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN_DATA_GAP = "UNKNOWN_DATA_GAP"


class SupplyRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    ELEVATED_DUE_TO_DATA_GAP = "ELEVATED_DUE_TO_DATA_GAP"


class SeasonalRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class EvidenceConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


# -----------------------------------------------------------------------------
# Cleaned Evidence Models
# -----------------------------------------------------------------------------

class SourceMetadata(BaseModel):
    source_id: Optional[str] = None
    organization: Optional[str] = None
    source_type: Optional[str] = "OFFICIAL_DATASET"
    dataset_name: Optional[str] = None
    url: Optional[str] = None


class CleanedDemographicMetric(BaseModel):
    metric: str
    value: Union[int, float, None]
    unit: str
    geography: Dict[str, Any] = Field(default_factory=dict)
    geographic_precision: str = "district"
    data_status: DataStatus = DataStatus.ACTUAL
    proxy: bool = False
    proxy_reason: Optional[str] = None
    source: SourceMetadata = Field(default_factory=SourceMetadata)
    reference_period: Optional[str] = None
    confidence: float = 0.90


class CleanedCompetitorItem(BaseModel):
    competitor_type: str = "direct"  # direct | adjacent | substitute
    business_name: str
    category: Optional[str] = None
    location: Dict[str, Any] = Field(default_factory=dict)
    distance_km: float = 0.0
    catchment_zone: CatchmentZone = CatchmentZone.PRIMARY
    is_cluster: bool = False
    is_proxy: bool = False
    source: SourceMetadata = Field(default_factory=SourceMetadata)
    confidence: float = 0.85


class CleanedDemandIndicator(BaseModel):
    indicator_name: str
    category: str
    raw_value: Union[int, float, str, None]
    normalized_value: Optional[float] = None
    unit: str
    business_relevance: Optional[str] = None
    geography: Dict[str, Any] = Field(default_factory=dict)
    geographic_precision: str = "district"
    data_status: DataStatus = DataStatus.ACTUAL
    proxy: bool = False
    source: SourceMetadata = Field(default_factory=SourceMetadata)
    confidence: float = 0.85


class CleanedSupplyHub(BaseModel):
    hub_name: str
    hub_type: str
    distance_km: float
    catchment_zone: CatchmentZone = CatchmentZone.PRIMARY
    commodities_available: List[str] = Field(default_factory=list)
    accessibility_rating: str = "moderate"
    source: SourceMetadata = Field(default_factory=SourceMetadata)
    data_status: DataStatus = DataStatus.ACTUAL
    confidence: float = 0.85


class CleanedInfrastructureRequirement(BaseModel):
    requirement: str
    status: str = "UNKNOWN"  # AVAILABLE | PARTIAL | UNAVAILABLE | UNKNOWN
    evidence_available: bool = False
    evidence_detail: Optional[str] = None
    impact: str = "HIGH"
    data_status: DataStatus = DataStatus.UNKNOWN


class CleanedSeasonalityFactor(BaseModel):
    month: str
    multiplier: float
    is_peak: bool = False
    is_lean: bool = False


# -----------------------------------------------------------------------------
# Analysis Results & Indicators
# -----------------------------------------------------------------------------

class GeospatialAnalysisResult(BaseModel):
    coordinates: Dict[str, float] = Field(default_factory=dict)
    resolved_location: Dict[str, Any] = Field(default_factory=dict)
    target_precision: str = "village"
    data_precision: str = "district"
    precision_gap: bool = False
    primary_radius_km: float = 15.0
    secondary_radius_km: float = 50.0
    entities_in_primary_zone: int = 0
    entities_in_secondary_zone: int = 0
    confidence: float = 0.90


class CompetitorCategoryAnalysis(BaseModel):
    count: int = 0
    cluster_count: int = 0
    proximity_weighted_count: float = 0.0
    items: List[CleanedCompetitorItem] = Field(default_factory=list)


class CompetitionAnalysisResult(BaseModel):
    direct: CompetitorCategoryAnalysis = Field(default_factory=CompetitorCategoryAnalysis)
    adjacent: CompetitorCategoryAnalysis = Field(default_factory=CompetitorCategoryAnalysis)
    substitute: CompetitorCategoryAnalysis = Field(default_factory=CompetitorCategoryAnalysis)
    total_competitors: int = 0
    competition_density_per_10k: float = 0.0
    competitive_pressure_score: float = 0.0  # 0.0 to 1.0
    competitive_pressure: CompetitivePressureLevel = CompetitivePressureLevel.MODERATE
    drivers: List[str] = Field(default_factory=list)
    saturation_threshold: float = 1.2
    confidence: float = 0.85
    calculation_method: str = "weighted_proximity_density"


class DemandEvidenceAnalysisResult(BaseModel):
    population_feature: Dict[str, Any] = Field(default_factory=dict)
    household_feature: Dict[str, Any] = Field(default_factory=dict)
    consumption_proxy: Dict[str, Any] = Field(default_factory=dict)
    purchasing_power_proxy: Dict[str, Any] = Field(default_factory=dict)
    seasonal_demand: Dict[str, Any] = Field(default_factory=dict)
    consumption_signals: List[Dict[str, Any]] = Field(default_factory=list)
    demographic_signals: List[Dict[str, Any]] = Field(default_factory=list)
    economic_signals: List[Dict[str, Any]] = Field(default_factory=list)
    demand_signal_strength: DemandSignalStrength = DemandSignalStrength.MODERATE
    demand_signal_score: float = 0.50
    data_coverage: float = 0.80
    confidence: float = 0.85


class InfrastructureAnalysisResult(BaseModel):
    readiness: InfrastructureReadiness = InfrastructureReadiness.UNKNOWN_DATA_GAP
    readiness_score: float = 0.0
    requirements: List[CleanedInfrastructureRequirement] = Field(default_factory=list)
    satisfied_requirements_count: int = 0
    total_requirements_count: int = 0
    critical_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.30


class SupplyEcosystemAnalysisResult(BaseModel):
    accessibility: str = "HIGH"
    hub_count: int = 0
    nearest_hub_distance_km: Optional[float] = None
    critical_input_coverage: Dict[str, Any] = Field(default_factory=dict)
    distance_assessment: str = "ACCEPTABLE"
    supply_risk: SupplyRiskLevel = SupplyRiskLevel.LOW
    supply_risk_score: float = 0.20
    hubs: List[CleanedSupplyHub] = Field(default_factory=list)
    confidence: float = 0.80


class MarketAccessAnalysisResult(BaseModel):
    catchment: Dict[str, Any] = Field(default_factory=dict)
    population_reach: int = 0
    accessibility: str = "HIGH"
    geographic_accessibility_score: float = 0.80
    transport_reach_km: float = 15.0
    confidence: float = 0.80


class SeasonalityAnalysisResult(BaseModel):
    peak_months: List[str] = Field(default_factory=list)
    lean_months: List[str] = Field(default_factory=list)
    peak_multiplier: float = 1.0
    lean_multiplier: float = 1.0
    monthly_multipliers: Dict[str, float] = Field(default_factory=dict)
    annual_volatility: float = 0.0
    seasonal_risk: SeasonalRiskLevel = SeasonalRiskLevel.LOW
    seasonal_notes: Optional[str] = None
    confidence: float = 0.90


class MarketCapacityAnalysisResult(BaseModel):
    status: MarketCapacityStatus = MarketCapacityStatus.LIMITED
    capacity_signal: str = "MODERATE_PRESSURE"
    net_capacity_score: float = 0.50  # Demand score minus competitive pressure
    competition_pressure: str = "MODERATE"
    demand_signal: str = "MODERATE"
    evidence_level: EvidenceConfidenceLevel = EvidenceConfidenceLevel.MODERATE
    limitations: List[str] = Field(default_factory=list)
    confidence: float = 0.70


class MarketIndicators(BaseModel):
    geospatial_analysis: GeospatialAnalysisResult = Field(default_factory=GeospatialAnalysisResult)
    competition: CompetitionAnalysisResult = Field(default_factory=CompetitionAnalysisResult)
    demand_evidence: DemandEvidenceAnalysisResult = Field(default_factory=DemandEvidenceAnalysisResult)
    infrastructure: InfrastructureAnalysisResult = Field(default_factory=InfrastructureAnalysisResult)
    supply_ecosystem: SupplyEcosystemAnalysisResult = Field(default_factory=SupplyEcosystemAnalysisResult)
    market_access: MarketAccessAnalysisResult = Field(default_factory=MarketAccessAnalysisResult)
    seasonality: SeasonalityAnalysisResult = Field(default_factory=SeasonalityAnalysisResult)
    market_capacity: MarketCapacityAnalysisResult = Field(default_factory=MarketCapacityAnalysisResult)


# -----------------------------------------------------------------------------
# Stage 7 Feature Contract: MarketFeatures
# -----------------------------------------------------------------------------

class MarketFeatures(BaseModel):
    business_features: Dict[str, Any] = Field(default_factory=dict)
    location_features: Dict[str, Any] = Field(default_factory=dict)
    demographic_features: Dict[str, Any] = Field(default_factory=dict)
    economic_features: Dict[str, Any] = Field(default_factory=dict)
    market_access_features: Dict[str, Any] = Field(default_factory=dict)
    competition_features: Dict[str, Any] = Field(default_factory=dict)
    supply_features: Dict[str, Any] = Field(default_factory=dict)
    infrastructure_features: Dict[str, Any] = Field(default_factory=dict)
    seasonal_features: Dict[str, Any] = Field(default_factory=dict)
    demand_evidence_features: Dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Provenance, Benchmarks & Traceability
# -----------------------------------------------------------------------------

class BenchmarkComparison(BaseModel):
    benchmark_id: str
    benchmark_name: str
    benchmark_value: Any
    actual_value: Any
    comparison_result: str
    variance_percentage: Optional[float] = None
    source: Optional[str] = None


class BenchmarkAnalysis(BaseModel):
    benchmarks_used: List[str] = Field(default_factory=list)
    comparisons: List[BenchmarkComparison] = Field(default_factory=list)


class CalculationProvenance(BaseModel):
    indicator: str
    value: Any
    calculation_method: str
    formula: str
    inputs: List[str] = Field(default_factory=list)
    benchmarks_used: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence: float = 0.85


class EvidenceGap(BaseModel):
    gap_id: str
    category: str
    description: str
    severity: str = "HIGH"
    impact: str = "Confidence discounted; requires primary verification or proxy modeling"


class Stage6Confidence(BaseModel):
    geospatial_analysis: float = 0.90
    competition_analysis: float = 0.85
    infrastructure_analysis: float = 0.30
    supply_analysis: float = 0.80
    demand_evidence_analysis: float = 0.80
    market_capacity_analysis: float = 0.70
    overall_market_confidence: float = 0.75
    proxy_dependency_score: float = 0.20
    data_gaps_count: int = 0


class EvidenceQuality(BaseModel):
    overall_confidence: float = 0.75
    component_confidence: Dict[str, float] = Field(default_factory=dict)
    proxy_dependency: float = 0.20
    data_gaps: List[EvidenceGap] = Field(default_factory=list)


class NextStageContract(BaseModel):
    stage: int = 7
    component: str = "DEMAND_PREDICTION_ML_MODEL"
    input_contract: str = "market_features"


class ExecutionMetadata(BaseModel):
    engine: str = "deterministic_market_intelligence_engine"
    engine_version: str = "1.0.0"
    llm_used: bool = False
    status: str = "SUCCESS"
    execution_time_seconds: float = 0.0


# -----------------------------------------------------------------------------
# Top-Level Stage 5 Input & Stage 6 Output Models
# -----------------------------------------------------------------------------

class Stage5Input(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow: Dict[str, Any] = Field(default_factory=dict)
    business_context: Dict[str, Any] = Field(default_factory=dict)
    location_context: Dict[str, Any] = Field(default_factory=dict)
    collection_plan: Dict[str, Any] = Field(default_factory=dict)
    market_evidence: Dict[str, Any] = Field(default_factory=dict)
    evidence_quality: Dict[str, Any] = Field(default_factory=dict)
    evidence_gaps: List[Any] = Field(default_factory=list)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class Stage6WorkflowState(BaseModel):
    stage: int = 6
    state: str = "MARKET_INTELLIGENCE_ANALYZED"
    status: str = "complete"  # complete | complete_with_gaps


class Stage6Output(BaseModel):
    schema_version: str = "1.0"
    analysis_id: str
    session_id: str
    workflow: Stage6WorkflowState = Field(default_factory=Stage6WorkflowState)
    business_context: Dict[str, Any] = Field(default_factory=dict)
    location_context: Dict[str, Any] = Field(default_factory=dict)
    market_indicators: MarketIndicators = Field(default_factory=MarketIndicators)
    market_features: MarketFeatures = Field(default_factory=MarketFeatures)
    benchmark_analysis: BenchmarkAnalysis = Field(default_factory=BenchmarkAnalysis)
    evidence_quality: EvidenceQuality = Field(default_factory=EvidenceQuality)
    calculation_provenance: List[CalculationProvenance] = Field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list)
    next_stage: NextStageContract = Field(default_factory=NextStageContract)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
