"""
Pydantic schemas and typed data contracts for Milestone 5:
Stress Testing, Scheme Routing & Financing Optimizer.
Zero reliance on LLMs. Strictly typed, auditable, and DPR-ready.
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class StressScenarioType(str, Enum):
    BASE_CASE = "BASE_CASE"
    REVENUE_DOWNSIDE = "REVENUE_DOWNSIDE"
    SELLING_PRICE_DOWNSIDE = "SELLING_PRICE_DOWNSIDE"
    VOLUME_DOWNSIDE = "VOLUME_DOWNSIDE"
    VARIABLE_COST_INCREASE = "VARIABLE_COST_INCREASE"
    FIXED_COST_INCREASE = "FIXED_COST_INCREASE"
    WORKING_CAPITAL_PRESSURE = "WORKING_CAPITAL_PRESSURE"
    INTEREST_RATE_STRESS = "INTEREST_RATE_STRESS"
    COMBINED_DOWNSIDE = "COMBINED_DOWNSIDE"
    USER_SCENARIO = "USER_SCENARIO"


class ScenarioSource(str, Enum):
    BASE_CASE = "BASE_CASE"
    POLICY_SCENARIO = "POLICY_SCENARIO"
    USER_SCENARIO = "USER_SCENARIO"


class ResilienceStatus(str, Enum):
    RESILIENT = "RESILIENT"
    STRESSED = "STRESSED"
    CRITICAL = "CRITICAL"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"
    UNRESOLVED = "UNRESOLVED"


class SchemeEligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class M5ValidationState(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


# -----------------------------------------------------------------------------
# Provenance & Validation Models
# -----------------------------------------------------------------------------

class M5ProvenanceRecord(BaseModel):
    metric: str
    value: Any
    source: str
    source_reference: Optional[str] = None
    calculation_method: Optional[str] = None
    input_dependencies: List[str] = Field(default_factory=list)
    status: str = "RESOLVED"
    confidence: float = 1.0
    scenario_id: Optional[str] = None


class M5ValidationCheck(BaseModel):
    check_id: str
    description: str
    status: M5ValidationState = M5ValidationState.PASSED
    severity: str = "HIGH"
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    difference: Optional[float] = None
    tolerance: Optional[float] = None
    message: str = ""
    reason_code: Optional[M5ReasonCode] = None


class M5ValidationResult(BaseModel):
    all_passed: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    unresolved_checks: int = 0
    checks: List[M5ValidationCheck] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Stress Testing Models
# -----------------------------------------------------------------------------

class StressScenarioResult(BaseModel):
    scenario_id: str
    scenario_name: str
    scenario_type: StressScenarioType
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    affected_drivers: List[str] = Field(default_factory=list)
    base_value: Optional[float] = None
    stressed_value: Optional[float] = None
    change_pct: Optional[float] = None
    source: ScenarioSource = ScenarioSource.POLICY_SCENARIO
    confidence: float = 0.85
    status: str = "RESOLVED"

    # Financial Performance Under Stress
    revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    ebitda: Optional[float] = None
    depreciation: Optional[float] = None
    interest_expense: Optional[float] = None
    profit_before_tax: Optional[float] = None
    tax_expense: Optional[float] = None
    pat: Optional[float] = None
    working_capital_movement: Optional[float] = None
    operating_cash_flow: Optional[float] = None

    # Debt Service & Ratios Under Stress
    debt_service: Optional[float] = None
    cads: Optional[float] = None
    dscr: Optional[float] = None
    minimum_dscr: Optional[float] = None
    break_even_sales: Optional[float] = None
    break_even_utilization_pct: Optional[float] = None
    current_ratio: Optional[float] = None
    cash_buffer_months: Optional[float] = None
    debt_equity_ratio: Optional[float] = None
    financing_gap: Optional[float] = None

    # Qualitative Assessments
    repayment_capacity_assessment: Optional[str] = None
    viability_status: Optional[str] = None
    resilience_status: ResilienceStatus = ResilienceStatus.RESILIENT
    reason_codes: List[M5ReasonCode] = Field(default_factory=list)
    provenance: List[M5ProvenanceRecord] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Scheme Routing Models
# -----------------------------------------------------------------------------

class SchemeRoutingOption(BaseModel):
    scheme_id: str
    scheme_name: str
    eligibility_status: SchemeEligibilityStatus
    eligibility_reasons: List[str] = Field(default_factory=list)
    min_project_cost: Optional[float] = None
    max_project_cost: Optional[float] = None
    max_supported_project_cost: Optional[float] = None
    maximum_loan_limit: Optional[float] = None
    max_loan: Optional[float] = None
    max_financing_percentage: Optional[float] = None
    required_margin_percentage: Optional[float] = None
    required_promoter_contribution: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    financing_gap: Optional[float] = None
    financing_surplus: Optional[float] = None
    status: str = "RESOLVED"
    rejection_reasons: List[str] = Field(default_factory=list)
    provenance: Optional[M5ProvenanceRecord] = None


# -----------------------------------------------------------------------------
# Financing Feasibility & Promoter Contribution Models
# -----------------------------------------------------------------------------

class PromoterContributionAnalysisResult(BaseModel):
    total_project_cost: Optional[float] = None
    available_promoter_contribution: Optional[float] = None
    required_promoter_contribution: Optional[float] = None
    required_percentage: Optional[float] = None
    actual_percentage: Optional[float] = None
    gap_surplus: Optional[float] = None  # >0 surplus, <0 gap
    is_adequate: Optional[bool] = None
    status: str = "RESOLVED"
    reason_code: Optional[M5ReasonCode] = None
    provenance: List[M5ProvenanceRecord] = Field(default_factory=list)


class FinancingGapAnalysisResult(BaseModel):
    total_project_cost: Optional[float] = None
    available_promoter_contribution: Optional[float] = None
    scheme_loan: Optional[float] = None
    other_verified_financing: Optional[float] = None
    total_funding: Optional[float] = None
    funding_gap: Optional[float] = None     # >0 shortfall / gap
    funding_surplus: Optional[float] = None # >0 excess funding
    is_balanced: bool = False
    status: str = "RESOLVED"
    reason_code: Optional[M5ReasonCode] = None
    provenance: List[M5ProvenanceRecord] = Field(default_factory=list)


class TenureOptionResult(BaseModel):
    tenure_months: int
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    moratorium_months: Optional[int] = None
    monthly_emi: Optional[float] = None
    total_interest: Optional[float] = None
    annual_debt_service: Optional[float] = None
    base_dscr: Optional[float] = None
    stress_dscr: Optional[float] = None
    repayment_capacity_assessment: Optional[str] = None
    is_scheme_compliant: bool = True
    status: str = "RESOLVED"
    reason_code: Optional[M5ReasonCode] = None


# -----------------------------------------------------------------------------
# Financing Options & Optimization Candidates
# -----------------------------------------------------------------------------

class FinancingStructureCandidate(BaseModel):
    candidate_id: str
    scheme_id: str
    scheme_name: str
    total_project_cost: Optional[float] = None
    promoter_contribution: Optional[float] = None
    loan_amount: Optional[float] = None
    other_financing: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    monthly_emi: Optional[float] = None
    total_interest: Optional[float] = None
    annual_debt_service: Optional[float] = None

    # Gap and Margin Analysis
    financing_gap: Optional[float] = None
    financing_surplus: Optional[float] = None
    required_margin_percentage: Optional[float] = None
    required_margin_amount: Optional[float] = None
    margin_surplus_or_gap: Optional[float] = None

    # Compliance & Viability Gates
    is_scheme_compliant: bool = False
    is_gap_eliminated: bool = False
    is_margin_met: bool = False
    base_case_dscr: Optional[float] = None
    revenue_downside_dscr: Optional[float] = None
    cost_downside_dscr: Optional[float] = None
    working_capital_stress_dscr: Optional[float] = None
    interest_rate_stress_dscr: Optional[float] = None
    combined_downside_dscr: Optional[float] = None
    stress_case_dscr: Optional[float] = None
    feasibility_status: str = "FEASIBLE"
    decision_rank: int = 999
    selection_reasons: List[M5ReasonCode] = Field(default_factory=list)
    status: str = "RESOLVED"
    provenance: List[M5ProvenanceRecord] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Resilience Comparison Matrix
# -----------------------------------------------------------------------------

class ResilienceComparisonRow(BaseModel):
    scenario_id: str
    scenario_name: str
    revenue: Optional[float] = None
    profitability_margin_pct: Optional[float] = None
    cash_from_ops: Optional[float] = None
    dscr: Optional[float] = None
    current_ratio: Optional[float] = None
    break_even_utilization_pct: Optional[float] = None
    funding_gap: Optional[float] = None
    resilience_status: ResilienceStatus = ResilienceStatus.RESILIENT
    reason_codes: List[M5ReasonCode] = Field(default_factory=list)


class ResilienceAnalysisResult(BaseModel):
    status: str = "RESOLVED"
    comparison_matrix: List[ResilienceComparisonRow] = Field(default_factory=list)
    overall_resilience: ResilienceStatus = ResilienceStatus.RESILIENT
    key_vulnerabilities: List[str] = Field(default_factory=list)
    reason_codes: List[M5ReasonCode] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# DPR-Ready Summary
# -----------------------------------------------------------------------------

class M5DprFinancingSummary(BaseModel):
    # Recommended Structure
    recommended_scheme_name: Optional[str] = None
    recommended_scheme_id: Optional[str] = None
    total_project_cost: Optional[float] = None
    promoter_contribution: Optional[float] = None
    promoter_margin_pct: Optional[float] = None
    term_loan: Optional[float] = None
    interest_rate_pct: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    monthly_emi: Optional[float] = None
    total_interest: Optional[float] = None

    # Stress Metrics
    scenarios_tested_count: int = 0
    worst_case_scenario: Optional[str] = None
    worst_case_dscr: Optional[float] = None
    worst_case_liquidity: Optional[float] = None
    stress_resilience_status: Optional[str] = None

    # Assessment & Compliance
    funding_gap: Optional[float] = None
    is_fully_financed: Optional[bool] = None
    margin_adequacy_status: Optional[str] = None
    repayment_capacity: Optional[str] = None
    unresolved_inputs: List[str] = Field(default_factory=list)
    advisory_notes: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Top-Level M5 Optimization Result Container
# -----------------------------------------------------------------------------

class M5OptimizationResult(BaseModel):
    status: str = "RESOLVED"
    base_case_reference: Dict[str, Any] = Field(default_factory=dict)
    stress_scenarios: List[StressScenarioResult] = Field(default_factory=list)
    scheme_options: List[SchemeRoutingOption] = Field(default_factory=list)
    financing_options: List[FinancingStructureCandidate] = Field(default_factory=list)
    selected_financing_structure: Optional[FinancingStructureCandidate] = None
    selected_structure: Optional[FinancingStructureCandidate] = None
    financing_gap_analysis: Optional[FinancingGapAnalysisResult] = None
    promoter_contribution_analysis: Optional[PromoterContributionAnalysisResult] = None
    tenure_analysis: List[TenureOptionResult] = Field(default_factory=list)
    resilience_analysis: Optional[ResilienceAnalysisResult] = None
    decision_reasons: List[M5ReasonCode] = Field(default_factory=list)
    risk_flags: List[Dict[str, Any]] = Field(default_factory=list)
    validation: Optional[M5ValidationResult] = None
    provenance: List[M5ProvenanceRecord] = Field(default_factory=list)
    reason_codes: List[M5ReasonCode] = Field(default_factory=list)
    dpr_summary: Optional[M5DprFinancingSummary] = None
    policy_version: str = "1.0.0"
    model_version: str = "M5-1.0.0"
