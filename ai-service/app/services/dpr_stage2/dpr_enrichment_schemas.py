"""
Stage 14.2: DPR Enrichment & Deterministic Inference Schemas.
Defines canonical data contracts for Stage 14.2 enrichment packages,
assumption review models, source provenance, module/section summaries, and validation gates.
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EnrichmentSourceType(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    USER_OVERRIDE = "USER_OVERRIDE"
    VERIFIED_DOCUMENT = "VERIFIED_DOCUMENT"
    BENCHMARK_DERIVED = "BENCHMARK_DERIVED"
    MARKET_DERIVED = "MARKET_DERIVED"
    POLICY_DERIVED = "POLICY_DERIVED"
    ENGINE_CALCULATED = "ENGINE_CALCULATED"
    UPSTREAM_RESOLVED = "UPSTREAM_RESOLVED"
    DERIVED = "DERIVED"
    DOCUMENT_PENDING = "DOCUMENT_PENDING"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SOURCE_MAPPING_ERROR = "SOURCE_MAPPING_ERROR"


class DerivationMethod(str, Enum):
    DIRECT_INPUT = "DIRECT_INPUT"
    DOCUMENT_EXTRACTION = "DOCUMENT_EXTRACTION"
    INDUSTRY_BENCHMARK = "INDUSTRY_BENCHMARK"
    MARKET_SIGNAL = "MARKET_SIGNAL"
    STATUTORY_POLICY = "STATUTORY_POLICY"
    FINANCIAL_ENGINE_M1_M6 = "FINANCIAL_ENGINE_M1_M6"
    FORMULAIC_CALCULATION = "FORMULAIC_CALCULATION"
    UNRESOLVED = "UNRESOLVED"


AUTHORITATIVE_FINANCIAL_FIELDS = {
    "total_project_cost",
    "cost_of_project",
    "promoter_equity_amount",
    "promoter_contribution",
    "bank_term_loan_amount",
    "term_loan",
    "working_capital_loan",
    "working_capital_bank_facility",
    "cost_plant_machinery",
    "cost_civil_works_shed",
    "cost_land_building",
    "cost_working_capital_margin",
    "cost_pre_operative_expenses",
    "cost_preliminary_preoperative",
    "cost_contingency_provision",
    "cost_contingencies",
    "monthly_emi",
    "interest_rate_pct",
    "loan_tenure_years",
    "moratorium_period_months",
    "glance_average_dscr",
    "dscr_analysis_multi_year",
    "glance_break_even_utilization",
    "break_even_metrics",
    "break_even_sales_amount",
    "break_even_capacity_percentage",
    "projected_pnl_statements",
    "projected_balance_sheet",
    "projected_cash_flow",
    "depreciation_schedule_summary",
    "loan_amortization_schedule",
    "banking_ratios_summary",
    "stress_scenarios_appraisal",
    "cma_statement_summary",
    "glance_ebitda_margin",
    "operating_ebitda_margin_pct",
    "working_capital_requirement",
    "debt_equity_ratio",
    "return_on_capital_employed_pct",
    "current_ratio_year1",
    "means_of_finance",
    "means_of_finance_reconciliation",
    "glance_total_project_cost",
    "glance_promoter_contribution",
    "glance_term_loan",
}


class EnrichmentField(BaseModel):
    field_id: str
    section_id: str
    module_id: str
    label: str
    value: Optional[Any] = None
    formatted_value: Optional[str] = None
    unit: Optional[str] = None
    status: str = "RESOLVED"  # RESOLVED, UNRESOLVED, UNKNOWN, NOT_APPLICABLE
    source_type: EnrichmentSourceType = EnrichmentSourceType.UNKNOWN
    source_id: Optional[str] = None
    source_reference: Optional[str] = None
    confidence: float = 0.0
    resolved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    derivation_method: DerivationMethod = DerivationMethod.UNRESOLVED
    upstream_dependencies: List[str] = Field(default_factory=list)
    editable: bool = True
    materiality: str = "MEDIUM"
    why_material: str = ""
    baseline_benchmark_value: Optional[Any] = None
    is_overridden: bool = False


class AssumptionReviewAction(str, Enum):
    USE_OR_CHANGE = "USE_OR_CHANGE"
    INFORMATIONAL = "INFORMATIONAL"
    DOCUMENT_REQUIRED = "DOCUMENT_REQUIRED"


class AssumptionReviewItem(BaseModel):
    field_id: str
    label: str
    module_id: str
    section_id: str
    value: Optional[Any] = None
    formatted_value: str
    unit: Optional[str] = None
    source_type: EnrichmentSourceType
    source_reference: str
    confidence: float
    editable: bool
    action: AssumptionReviewAction
    why_material: str
    baseline_benchmark_value: Optional[Any] = None
    benchmark_id: Optional[str] = None
    is_overridden: bool = False
    downstream_impact: str = ""


class AssumptionReviewPackage(BaseModel):
    business_id: str
    scenario_id: str
    version: int
    total_assumptions: int
    user_confirmed_count: int = 0
    user_overridden_count: int = 0
    assumptions_requiring_review: List[AssumptionReviewItem] = Field(default_factory=list)
    informational_assumptions: List[AssumptionReviewItem] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SectionEnrichmentSummary(BaseModel):
    section_id: str
    section_number: str
    module_id: str
    title: str
    total_fields: int
    resolved_fields: int
    unresolved_fields: int
    completeness_status: str  # COMPLETE, PARTIALLY_COMPLETE, INCOMPLETE
    source_breakdown: Dict[str, int] = Field(default_factory=dict)
    fields: Dict[str, EnrichmentField] = Field(default_factory=dict)


class ModuleEnrichmentSummary(BaseModel):
    module_id: str
    module_number: str
    title: str
    description: str
    total_sections: int
    completed_sections: int
    total_fields: int
    resolved_fields: int
    is_module_ready: bool
    sections: Dict[str, SectionEnrichmentSummary] = Field(default_factory=dict)


class FinancialAuthorityCheckResult(BaseModel):
    field_id: str
    status: str  # "PASS" | "FAIL"
    dpr_value: Optional[Any] = None
    financial_package_value: Optional[Any] = None
    source_type: str
    reason: str


class ValidationCheckResult(BaseModel):
    check_id: str
    rule_name: str
    passed: bool
    severity: str = "CRITICAL"  # CRITICAL, WARNING, INFO
    details: str
    affected_fields: List[str] = Field(default_factory=list)


class EnrichmentValidationSummary(BaseModel):
    overall_valid: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings_count: int
    checks: List[ValidationCheckResult] = Field(default_factory=list)
    financial_authority_checks: List[FinancialAuthorityCheckResult] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


class DPREnrichmentPackage(BaseModel):
    """
    Authoritative Stage 14.2 DPR Enrichment & Deterministic Inference Package.
    Houses the full 8-module / 39-section enriched project appraisal,
    provenance traces, baseline benchmarks, financial engine schedules, and assumption review.
    """
    metadata: Dict[str, Any] = Field(default_factory=dict)
    business_id: str
    scenario_id: str
    version: int = 1
    intake_package_snapshot: Dict[str, Any] = Field(default_factory=dict)
    business_profile: Dict[str, Any] = Field(default_factory=dict)
    entrepreneur_profile: Dict[str, Any] = Field(default_factory=dict)
    location_profile: Dict[str, Any] = Field(default_factory=dict)
    market: Dict[str, Any] = Field(default_factory=dict)
    market_intelligence: Dict[str, Any] = Field(default_factory=dict)
    opportunity: Dict[str, Any] = Field(default_factory=dict)
    financials: Dict[str, Any] = Field(default_factory=dict)
    financial_package: Dict[str, Any] = Field(default_factory=dict)
    benchmarks: Dict[str, Any] = Field(default_factory=dict)
    schemes: Dict[str, Any] = Field(default_factory=dict)
    scheme_policy_context: Dict[str, Any] = Field(default_factory=dict)
    risk: Dict[str, Any] = Field(default_factory=dict)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    feasibility: Dict[str, Any] = Field(default_factory=dict)
    feasibility_synthesis: Dict[str, Any] = Field(default_factory=dict)
    swot: Dict[str, Any] = Field(default_factory=dict)
    swot_matrix: Dict[str, Any] = Field(default_factory=dict)
    documents: Dict[str, Any] = Field(default_factory=dict)
    dpr_fields: Dict[str, Any] = Field(default_factory=dict)
    modules: Dict[str, ModuleEnrichmentSummary] = Field(default_factory=dict)
    sections: Dict[str, SectionEnrichmentSummary] = Field(default_factory=dict)
    section_completeness: Dict[str, Any] = Field(default_factory=dict)
    fields: Dict[str, EnrichmentField] = Field(default_factory=dict)
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    assumption_review: AssumptionReviewPackage
    validation: EnrichmentValidationSummary
    readiness: Dict[str, Any] = Field(default_factory=dict)
    is_enrichment_complete: bool = False
    can_proceed_to_validation: bool = False
    ready_for_stage_14_3: bool = False
    enriched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stage: str = "STAGE_14_2_DPR_ENRICHMENT_INFERENCE"
