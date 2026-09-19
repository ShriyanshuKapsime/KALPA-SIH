from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------
# 1. Provenance & Data Quality Schema
# ---------------------------------------------------------
class QualityMetadataSchema(BaseModel):
    authority: str = "official"  # official | institutional | industry_reference | derived | estimated | demo_reference
    verification_status: str = "verified"  # verified | source_registered | needs_verification | estimated | demo_data
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    last_verified: Optional[str] = "2026-02-20"


class ProvenanceSchema(BaseModel):
    source_id: str
    source_name: Optional[str] = None
    organization: Optional[str] = None
    document_name: Optional[str] = None
    publication_year: Optional[Union[int, str]] = None
    source_type: str = "OFFICIAL_GOVERNMENT_NOTIFICATION"  # OFFICIAL_GOVERNMENT_NOTIFICATION | OFFICIAL_RESEARCH_REPORT | OFFICIAL_STATISTICS | OFFICIAL_CHALLENGE_SPEC | ACADEMIC_RESEARCH | OPEN_DATA
    source_url: Optional[str] = None
    url: Optional[str] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    last_verified: Optional[str] = None
    notes: Optional[str] = None
    sample_size: Optional[int] = None


class DataSourceMetadataSchema(BaseModel):
    dataset_id: str
    dataset_name: str
    category: str
    official_source: str
    ministry_or_nodal_agency: str
    file_format: str = "JSON / API"
    ingestion_status: str = "AVAILABLE"  # AVAILABLE | PARTIAL | REGISTERED_NOT_LOADED | PENDING_ACQUISITION | MISSING
    records_count: int = 0
    coverage_domain: str = "ALL_INDIA"
    last_sync_date: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    future_consumers: List[str] = []
    reliability_level: Optional[str] = None
    license: Optional[str] = None
    provenance: Optional[ProvenanceSchema] = None
    quality: Optional[QualityMetadataSchema] = None


# ---------------------------------------------------------
# 2. Government Schemes & Baseline Rules Schema
# ---------------------------------------------------------
class SchemeFinancialTermsSchema(BaseModel):
    max_loan_amount: Optional[float] = None
    min_loan_amount: Optional[float] = None
    min_promoter_contribution_pct: Optional[float] = None
    max_funding_pct: Optional[float] = None
    interest_rate_pct: Optional[float] = None
    interest_rate_type: Optional[str] = "FIXED"
    tenure_months: Optional[int] = None
    tenure_years: Optional[float] = None
    moratorium_months: Optional[int] = None
    moratorium_policy: Optional[str] = "principal_only"  # principal_only | full_moratorium | none
    subsidy_pct: Optional[float] = 0.0
    max_subsidy_amount: Optional[float] = 0.0
    collateral_required: bool = False
    processing_fee_waiver: bool = False
    guarantee_coverage_pct: Optional[float] = None
    cgtmse_covered: bool = False
    promoter_contribution_general: Optional[float] = None
    promoter_contribution_special: Optional[float] = None
    subsidy_pct_urban_general: Optional[float] = None
    subsidy_pct_rural_general: Optional[float] = None
    subsidy_pct_urban_special: Optional[float] = None
    subsidy_pct_rural_special: Optional[float] = None
    interest_subvention_pct: Optional[float] = None
    effective_interest_rate_pct: Optional[float] = None


class SchemeEligibilityCriteriaSchema(BaseModel):
    target_beneficiary: Optional[str] = None
    min_project_cost: Optional[float] = None
    max_project_cost: Optional[float] = None
    min_age: Optional[int] = 18
    max_age: Optional[int] = None
    min_education: Optional[str] = None
    gender_preference: Optional[str] = "ALL"  # ALL | FEMALE_OR_SC_ST
    caste_preference: Optional[str] = "ALL"
    rural_only: bool = False
    rural_subsidy_multiplier: Optional[float] = None
    is_greenfield_only: bool = False
    prior_experience_required: bool = False
    odop_aligned_preference: bool = False
    collateral_required: bool = False


class GovernmentSchemeSchema(BaseModel):
    scheme_id: str
    scheme_name: str
    nodal_agency: str
    ministry_or_body: str
    category: str
    scheme_tier: str
    provenance: Optional[ProvenanceSchema] = None
    quality: Optional[QualityMetadataSchema] = None
    eligibility_criteria: SchemeEligibilityCriteriaSchema
    financial_terms: SchemeFinancialTermsSchema
    applicable_sectors: List[str] = []
    documentation_required: List[str] = []
    application_mode: str = "ONLINE_PORTAL"
    validity_status: str = "ACTIVE"
    calculation_formulas: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------
# 3. Financial Benchmarks Schema
# ---------------------------------------------------------
class BenchmarkCapexSchema(BaseModel):
    range_min: float
    typical: float
    range_max: float
    fixed_cost_ratio: Optional[float] = None
    equipment_cost_pct: Optional[float] = None
    site_setup_pct: Optional[float] = None
    pre_operative_pct: Optional[float] = None
    shed_construction_pct: Optional[float] = None
    breakdown_typical: Optional[Dict[str, float]] = None


class BenchmarkWorkingCapitalSchema(BaseModel):
    typical_monthly_requirement: float
    working_capital_months_recommended: float = 2.0
    working_capital_to_capex_ratio: Optional[float] = None
    working_capital_ratio: Optional[float] = None
    inventory_turnover_days: Optional[int] = None
    breakdown_typical: Optional[Dict[str, float]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_wc(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "working_capital_to_capex_ratio" not in data and "working_capital_ratio" in data:
                data["working_capital_to_capex_ratio"] = data["working_capital_ratio"]
            elif "working_capital_ratio" not in data and "working_capital_to_capex_ratio" in data:
                data["working_capital_ratio"] = data["working_capital_to_capex_ratio"]
            elif "working_capital_to_capex_ratio" not in data:
                data["working_capital_to_capex_ratio"] = 0.50
        return data


class BenchmarkMarginsSchema(BaseModel):
    gross_margin_pct_min: float
    gross_margin_pct_typical: float
    gross_margin_pct_max: float
    net_margin_pct_min: float
    net_margin_pct_typical: float
    net_margin_pct_max: float
    operating_cost_ratio: Optional[float] = None


class BenchmarkTimelinesSchema(BaseModel):
    setup_time_days: int = 30
    breakeven_months: int = 4
    payback_period_months: int = 18
    batch_cycle_days: Optional[int] = None
    batches_per_year: Optional[int] = None
    composting_cycle_days: Optional[int] = None


class FinancialBenchmarkSchema(BaseModel):
    business_node_id: str
    business_title: str
    aliases: List[str] = []
    nic_code: Optional[str] = None
    currency: str = "INR"
    provenance: Optional[ProvenanceSchema] = None
    quality: Optional[QualityMetadataSchema] = None
    capex: BenchmarkCapexSchema
    working_capital: BenchmarkWorkingCapitalSchema
    margins: BenchmarkMarginsSchema
    cost_structure_pct: Dict[str, float] = {}
    timelines: BenchmarkTimelinesSchema
    unit_economics: Dict[str, Any] = {}

    @property
    def business_id(self) -> str:
        return self.business_node_id

    @property
    def business_name(self) -> str:
        return self.business_title

    @model_validator(mode="before")
    @classmethod
    def normalize_fin_benchmark(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "business_title" not in data and "business_name" in data:
                data["business_title"] = data["business_name"]
            if "business_node_id" not in data and "business_id" in data:
                data["business_node_id"] = data["business_id"]
        return data


# ---------------------------------------------------------
# 4. Market Benchmarks & Requirements Schema
# ---------------------------------------------------------
class MarketCatchmentSchema(BaseModel):
    primary_radius_km: float
    secondary_radius_km: float
    target_household_count_min: Optional[int] = None
    target_population_min: Optional[int] = None
    target_milch_animals_count_min: Optional[int] = None
    target_cultivable_acres_min: Optional[int] = None
    target_cultivable_paddy_acres_min: Optional[int] = None
    target_solar_installations_min: Optional[int] = None


class MarketCompetitionSchema(BaseModel):
    saturation_threshold_units_per_10k_pop: float
    healthy_competition_ratio: float = 1.0
    direct_competitors: List[str] = []
    indirect_competitors: List[str] = []


class MarketAnalysisRequirements(BaseModel):
    dynamic_data_required: List[str] = []
    dynamic_data_optional: List[str] = []
    static_benchmarks_required: List[str] = []
    analysis_parameters: Dict[str, Any] = {}


class MarketBenchmarkSchema(BaseModel):
    business_node_id: str
    business_title: str
    aliases: List[str] = []
    catchment: MarketCatchmentSchema
    competition_and_saturation: MarketCompetitionSchema
    seasonality_factors: Dict[str, float] = {}
    seasonality_notes: Optional[str] = None
    demand_drivers: List[str] = []
    target_customer_segments: List[str] = []
    market_analysis_requirements: Optional[MarketAnalysisRequirements] = None
    provenance: Optional[ProvenanceSchema] = None
    quality: Optional[QualityMetadataSchema] = None

    @property
    def business_id(self) -> str:
        return self.business_node_id

    @property
    def business_name(self) -> str:
        return self.business_title

    @model_validator(mode="before")
    @classmethod
    def normalize_mkt_benchmark(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "business_title" not in data and "business_name" in data:
                data["business_title"] = data["business_name"]
            if "business_node_id" not in data and "business_id" in data:
                data["business_node_id"] = data["business_id"]
        return data


# ---------------------------------------------------------
# 5. Business Domain Knowledge & Profiles Schema
# ---------------------------------------------------------
class CoreMachineryItemSchema(BaseModel):
    item_name: str
    quantity: int = 1
    estimated_cost_inr: float = 0.0
    maintenance_interval_days: int = 90
    power_rating_hp: float = 0.0


class ComplianceLicenseItemSchema(BaseModel):
    license_name: str
    issuing_authority: str = "Government of India"
    mandatory: bool = True
    approx_fee_inr: float = 0.0
    renewal_years: int = 1


class BusinessProfileSchema(BaseModel):
    business_node_id: str
    business_title: str
    aliases: List[str] = []
    nic_code: Optional[str] = None
    category: str = "General MSME"
    sector: Optional[str] = None
    business_model: Optional[str] = None
    products: List[str] = []
    services: List[str] = []
    operations: Dict[str, Any] = {}
    space_and_infrastructure: Dict[str, Any] = {}
    power_and_utilities: Dict[str, Any] = {}
    core_machinery: List[CoreMachineryItemSchema] = []
    skills_and_manpower: Dict[str, Any] = {}
    supply_chain: Dict[str, Any] = {}
    compliance_and_licensing: List[ComplianceLicenseItemSchema] = []
    risk_factors: List[str] = []
    quality: Optional[QualityMetadataSchema] = None
    provenance: Optional[ProvenanceSchema] = None

    @property
    def business_id(self) -> str:
        return self.business_node_id

    @property
    def business_name(self) -> str:
        return self.business_title

    @model_validator(mode="before")
    @classmethod
    def normalize_profile(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "business_node_id" not in data and "business_id" in data:
                data["business_node_id"] = data["business_id"]
            if "business_title" not in data and "business_name" in data:
                data["business_title"] = data["business_name"]
            if "category" not in data and "classification" in data:
                data["category"] = data["classification"].get("category", "General MSME")
                if "sector" not in data:
                    data["sector"] = data["classification"].get("sector")
                if "nic_code" not in data and data["classification"].get("nic_codes"):
                    data["nic_code"] = data["classification"]["nic_codes"][0]
            if "space_and_infrastructure" not in data and "infrastructure_requirements" in data:
                data["space_and_infrastructure"] = data["infrastructure_requirements"]
                data["power_and_utilities"] = {
                    "power_connection_type": data["infrastructure_requirements"].get("power_connection_type", "Commercial"),
                    "power_load_hp": data["infrastructure_requirements"].get("power_load_hp", 5.0),
                }
            if "skills_and_manpower" not in data and "resource_requirements" in data:
                data["skills_and_manpower"] = data["resource_requirements"]
            if "core_machinery" not in data and "machinery_requirements" in data:
                data["core_machinery"] = [
                    {
                        "item_name": m.get("name") or m.get("item_name", "Machinery"),
                        "quantity": m.get("quantity", 1),
                        "estimated_cost_inr": m.get("estimated_cost_inr", 0.0),
                        "maintenance_interval_days": m.get("maintenance_interval_days", 90),
                    }
                    for m in data["machinery_requirements"]
                ]
            if "compliance_and_licensing" not in data and "licenses_and_compliance" in data:
                data["compliance_and_licensing"] = [
                    {
                        "license_name": lic.get("name") or lic.get("license_name", "License"),
                        "issuing_authority": lic.get("authority") or lic.get("issuing_authority", "Authority"),
                        "mandatory": lic.get("mandatory", True),
                    }
                    for lic in data["licenses_and_compliance"]
                ]
            if "risk_factors" not in data and "risks_and_challenges" in data:
                data["risk_factors"] = data["risks_and_challenges"]
        return data


class BusinessRequirementSchema(BaseModel):
    business_node_id: str
    business_title: str
    space_and_infrastructure: Dict[str, Any] = {}
    power_and_utilities: Dict[str, Any] = {}
    core_machinery: List[CoreMachineryItemSchema] = []
    skills_and_manpower: Dict[str, Any] = {}
    supply_chain: Dict[str, Any] = {}
    compliance_and_licensing: List[ComplianceLicenseItemSchema] = []

    @property
    def business_id(self) -> str:
        return self.business_node_id

    @property
    def business_name(self) -> str:
        return self.business_title


# ---------------------------------------------------------
# 6. Risk Library Schema
# ---------------------------------------------------------
class RiskItemSchema(BaseModel):
    risk_id: str
    risk_name: str
    category: str  # OPERATIONAL | FINANCIAL | REGULATORY | MARKET | CLIMATE_AND_ENVIRONMENTAL
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    probability: str = "MEDIUM"  # LOW | MEDIUM | HIGH
    applicable_business_nodes: List[str] = []
    trigger_events: List[str] = []
    impact_description: str
    mitigation_strategies: List[str] = []
    monitoring_indicators: List[str] = []
    provenance: Optional[ProvenanceSchema] = None
    quality: Optional[QualityMetadataSchema] = None


# ---------------------------------------------------------
# 7. Institutional Documents Schema
# ---------------------------------------------------------
class InstitutionalDocumentSchema(BaseModel):
    document_id: str
    title: str
    institution: str
    publication_year: int
    category: str
    document_url: str
    file_format: str = "PDF"
    ingestion_status: str = "REGISTERED"  # REGISTERED | PENDING_EXTRACTION | EXTRACTED | INDEXED | FAILED
    extracted_at: Optional[str] = None
    key_insights: Dict[str, Any] = {}
    applicable_business_nodes: List[str] = []
    summary: str
    provenance: Optional[ProvenanceSchema] = None
    quality: Optional[QualityMetadataSchema] = None


# ---------------------------------------------------------
# 8. Dynamic Data Requirements Schema
# ---------------------------------------------------------
class CandidateSourceSchema(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    reliability_score: float = 0.9


class DynamicDataRequirementSchema(BaseModel):
    requirement_id: str
    requirement_name: str
    domain: str
    target_parameters: List[str] = []
    refresh_frequency: str  # DAILY | WEEKLY | MONTHLY | SEASONAL | QUARTERLY
    ingestion_method: str
    candidate_sources: List[CandidateSourceSchema] = []
    consuming_engines: List[str] = []
    fallback_strategy: str
    priority: str = "HIGH"  # HIGH | MEDIUM | LOW


# ---------------------------------------------------------
# 9. Engine-Ready Packs & Calculation Models (Stage 4.5 Core)
# ---------------------------------------------------------
class MarketKnowledgePack(BaseModel):
    business_node_id: str
    business_title: str
    available: bool = True
    status: str = "ready"  # ready | data_missing | estimated
    recommended_action: Optional[str] = None  # fetch_dynamic_data | verify_locally
    catchment: Optional[MarketCatchmentSchema] = None
    competition_and_saturation: Optional[MarketCompetitionSchema] = None
    seasonality_factors: Dict[str, float] = {}
    seasonality_notes: Optional[str] = None
    demand_drivers: List[str] = []
    target_customer_segments: List[str] = []
    market_analysis_requirements: Optional[MarketAnalysisRequirements] = None
    quality: Optional[QualityMetadataSchema] = None
    provenance: Optional[ProvenanceSchema] = None


class AmortizationRowSchema(BaseModel):
    month: int
    opening_balance: float
    principal_payment: float
    interest_payment: float
    total_installment: float
    closing_balance: float


class FinancialCalculationRules(BaseModel):
    baseline_rule_applied: str  # SIH_BASELINE_MICRO_FINANCE | SIH_BASELINE_TERM_LOAN | CUSTOM
    is_micro_enterprise: bool
    project_cost: float
    promoter_contribution_amount: float
    promoter_contribution_pct: float
    loan_amount: float
    interest_rate_pct: float
    tenure_months: int
    moratorium_months: int
    moratorium_policy: str = "principal_only"
    monthly_emi: float
    total_interest_payable: float
    total_payment: float
    first_year_schedule: List[AmortizationRowSchema] = []


class FinancialKnowledgePack(BaseModel):
    business_node_id: str
    business_title: str
    available: bool = True
    status: str = "ready"  # ready | data_missing | estimated
    recommended_action: Optional[str] = None
    benchmark_capex: Optional[BenchmarkCapexSchema] = None
    benchmark_working_capital: Optional[BenchmarkWorkingCapitalSchema] = None
    benchmark_margins: Optional[BenchmarkMarginsSchema] = None
    cost_structure_pct: Dict[str, float] = {}
    timelines: Optional[BenchmarkTimelinesSchema] = None
    unit_economics: Dict[str, Any] = {}
    applicable_schemes: List[GovernmentSchemeSchema] = []
    recommended_scheme: Optional[GovernmentSchemeSchema] = None
    calculation_rules: Optional[FinancialCalculationRules] = None
    quality: Optional[QualityMetadataSchema] = None
    provenance: Optional[ProvenanceSchema] = None


class FinancialFeasibilityResult(BaseModel):
    business_node_id: str
    project_cost: float
    promoter_contribution: float
    loan_amount: float
    monthly_emi: float
    estimated_monthly_revenue: float
    estimated_monthly_net_profit: float
    dscr_ratio: float
    breakeven_months: int
    payback_period_months: int
    feasibility_status: str  # FEASIBLE | CONDITIONAL | HIGH_RISK | INSUFFICIENT_MARGIN
    risk_notes: List[str] = []
    baseline_rule_applied: str


class ExplainableQualityScore(BaseModel):
    overall_confidence: float = 0.90
    authority_tier: str = "official"  # official | mixed | estimated
    verified_fields_count: int = 0
    total_fields_count: int = 0
    official_sources_count: int = 0
    audit_notes: List[str] = []


class ComprehensiveBusinessKnowledgePack(BaseModel):
    business_node_id: str
    business_title: str
    nic_code: Optional[str] = None
    available: bool = True
    status: str = "ready"
    quality_score: ExplainableQualityScore
    layer1_rules_and_schemes: Dict[str, Any]
    layer2_domain_knowledge: Optional[BusinessProfileSchema] = None
    layer3_financial_benchmarks: Optional[FinancialBenchmarkSchema] = None
    layer3_market_benchmarks: Optional[MarketBenchmarkSchema] = None
    layer4_institutional_evidence: List[InstitutionalDocumentSchema] = []
    layer5_dynamic_data_requirements: List[DynamicDataRequirementSchema] = []
    layer5_candidate_sources: List[DataSourceMetadataSchema] = []
    missing_data_signals: List[Dict[str, str]] = []


# ---------------------------------------------------------
# 10. Aggregated Coverage & Query Schemas
# ---------------------------------------------------------
class CoverageReportSchema(BaseModel):
    total_curated_datasets: int
    total_schemes: int
    total_financial_benchmarks: int
    total_market_benchmarks: int
    total_business_profiles: int
    total_business_requirements: int
    total_risk_items: int
    total_institutional_documents: int
    total_dynamic_requirements: int
    priority_businesses_coverage: Dict[str, Any] = {}
    dataset_coverage_summary: Dict[str, int]
    status_breakdown: Dict[str, int]
    completeness_score_pct: float
    provenance_distribution: Dict[str, int]
    quality_distribution: Dict[str, int] = {}
    timestamp: str


class SchemeEligibilityQuery(BaseModel):
    project_cost: float
    available_margin: Optional[float] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    gender: Optional[str] = "ALL"
    caste: Optional[str] = "ALL"
    is_rural: bool = True
    business_node_id: Optional[str] = None


class SchemeEligibilityResult(BaseModel):
    matched_schemes: List[GovernmentSchemeSchema]
    challenge_baseline_applied: Optional[GovernmentSchemeSchema] = None
    recommended_scheme_id: Optional[str] = None
    estimated_subsidy_pct: float = 0.0
    estimated_interest_rate_pct: float = 8.0
    total_matched: int = 0
