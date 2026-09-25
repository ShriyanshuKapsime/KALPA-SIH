"""
Pydantic schemas and data contracts for M4 Banking Appraisal & Viability Engine.
Institutional-grade, typed, auditable contracts for DPR generation.
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

from app.services.financial_engine.appraisal.reason_codes import ReasonCode


class AppraisalStatus(str, Enum):
    RESOLVED = "RESOLVED"
    PARTIALLY_DERIVED = "PARTIALLY_DERIVED"
    UNRESOLVED = "UNRESOLVED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ViabilityClassification(str, Enum):
    FINANCIALLY_VIABLE = "FINANCIALLY_VIABLE"
    CONDITIONALLY_VIABLE = "CONDITIONALLY_VIABLE"
    FINANCIALLY_STRESSED = "FINANCIALLY_STRESSED"
    NOT_ASSESSABLE = "NOT_ASSESSABLE"


class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    REPAYMENT = "REPAYMENT"
    LEVERAGE = "LEVERAGE"
    LIQUIDITY = "LIQUIDITY"
    PROFITABILITY = "PROFITABILITY"
    BREAK_EVEN = "BREAK_EVEN"
    CAPITAL_STRUCTURE = "CAPITAL_STRUCTURE"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    STAGE9_RECONCILIATION = "STAGE9_RECONCILIATION"


class ValidationState(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


class MetricSource(str, Enum):
    USER = "USER"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    STAGE9 = "STAGE9"
    SCHEME = "SCHEME"
    BENCHMARK = "BENCHMARK"
    DERIVED = "DERIVED"


class CoverageTrend(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DETERIORATING = "DETERIORATING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# -----------------------------------------------------------------------------
# Metric & Year-wise Models
# -----------------------------------------------------------------------------

class AppraisalMetricValue(BaseModel):
    value: Optional[float] = None
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None
    source: MetricSource = MetricSource.DERIVED
    calculation_method: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)


# 1. Debt Service
class DebtServiceYear(BaseModel):
    year: int
    opening_debt: Optional[float] = None
    principal_repayment: Optional[float] = None
    interest_repayment: Optional[float] = None
    total_debt_service: Optional[float] = None
    closing_debt: Optional[float] = None
    emi_burden_ratio: Optional[float] = None  # Debt service / Revenue
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class DebtServiceAnalysisResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[DebtServiceYear] = Field(default_factory=list)
    total_principal: Optional[float] = None
    total_interest: Optional[float] = None
    total_debt_service: Optional[float] = None
    total_principal_lifetime: Optional[float] = None
    total_interest_lifetime: Optional[float] = None
    average_annual_debt_service: Optional[float] = None
    opening_debt_total: Optional[float] = None
    closing_debt_final: Optional[float] = None
    is_zero_debt: bool = False
    reason_code: Optional[ReasonCode] = None


# 2. Repayment Capacity
class RepaymentCapacityYear(BaseModel):
    year: int
    cash_available_for_debt_service: Optional[float] = None  # CADS
    debt_service_obligation: Optional[float] = None
    surplus_deficit: Optional[float] = None
    capacity_ratio: Optional[float] = None  # CADS / Debt service
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class RepaymentCapacityResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[RepaymentCapacityYear] = Field(default_factory=list)
    total_cads: Optional[float] = None
    total_debt_service: Optional[float] = None
    cumulative_surplus_deficit: Optional[float] = None
    minimum_capacity_ratio: Optional[float] = None
    capacity_assessment: str = "ADEQUATE"
    reason_code: Optional[ReasonCode] = None


# 3. DSCR / ADSCR
class DSCRYear(BaseModel):
    year: int
    dscr: Optional[float] = None
    cads: Optional[float] = None
    debt_service: Optional[float] = None
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    source: MetricSource = MetricSource.DERIVED
    calculation_method: str = "CADS / (Principal + Interest)"
    reason_code: Optional[ReasonCode] = None


class DSCRAnalysisResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[DSCRYear] = Field(default_factory=list)
    minimum_dscr: Optional[float] = None
    average_dscr: Optional[float] = None  # ADSCR
    trend: CoverageTrend = CoverageTrend.STABLE
    stage9_dscr: Optional[float] = None
    reconciliation_status: ValidationState = ValidationState.PASSED
    reconciliation_difference: Optional[float] = None
    reason_code: Optional[ReasonCode] = None


# 4. Break-Even Analysis
class BreakEvenYear(BaseModel):
    year: int
    revenue: Optional[float] = None
    fixed_costs: Optional[float] = None
    variable_costs: Optional[float] = None
    contribution_margin: Optional[float] = None
    contribution_margin_ratio: Optional[float] = None
    break_even_sales: Optional[float] = None
    break_even_utilization_pct: Optional[float] = None
    margin_of_safety_pct: Optional[float] = None
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class BreakEvenAnalysisResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[BreakEvenYear] = Field(default_factory=list)
    year1_break_even_sales: Optional[float] = None
    year1_break_even_utilization_pct: Optional[float] = None
    year1_margin_of_safety_pct: Optional[float] = None
    stage9_break_even_sales: Optional[float] = None
    stage9_break_even_utilization_pct: Optional[float] = None
    reconciliation_status: ValidationState = ValidationState.PASSED
    reconciliation_difference: Optional[float] = None
    reason_code: Optional[ReasonCode] = None


# 5. Liquidity Analysis
class LiquidityYear(BaseModel):
    year: int
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    working_capital: Optional[float] = None
    operating_cash_flow_coverage: Optional[float] = None  # OCF / Current Liabilities
    cash_buffer_months: Optional[float] = None  # Cash / (Monthly OPEX)
    debt_service_liquidity_ratio: Optional[float] = None  # (Cash + OCF) / Debt Service
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class LiquidityAnalysisResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[LiquidityYear] = Field(default_factory=list)
    average_current_ratio: Optional[float] = None
    average_quick_ratio: Optional[float] = None
    minimum_cash_buffer_months: Optional[float] = None
    working_capital_adequacy: str = "ADEQUATE"
    reason_code: Optional[ReasonCode] = None


# 6. Profitability Analysis
class ProfitabilityYear(BaseModel):
    year: int
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    ebitda: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    ebit: Optional[float] = None
    ebit_margin_pct: Optional[float] = None
    pat: Optional[float] = None
    net_profit_margin_pct: Optional[float] = None
    roce_pct: Optional[float] = None  # EBIT / Capital Employed
    roe_pct: Optional[float] = None   # PAT / Net Worth
    roa_pct: Optional[float] = None   # PAT / Total Assets
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class ProfitabilityAnalysisResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[ProfitabilityYear] = Field(default_factory=list)
    average_gross_margin_pct: Optional[float] = None
    average_ebitda_margin_pct: Optional[float] = None
    average_ebit_margin_pct: Optional[float] = None
    average_net_profit_margin_pct: Optional[float] = None
    average_roce_pct: Optional[float] = None
    average_roe_pct: Optional[float] = None
    average_roa_pct: Optional[float] = None
    reason_code: Optional[ReasonCode] = None


# 7. Leverage & Capital Structure
class LeverageYear(BaseModel):
    year: int
    total_debt: Optional[float] = None
    tangible_net_worth: Optional[float] = None
    total_outside_liabilities: Optional[float] = None
    total_assets: Optional[float] = None
    debt_equity_ratio: Optional[float] = None        # DER = Total Debt / TNW
    tol_tnw_ratio: Optional[float] = None            # TOL / TNW
    debt_to_assets_ratio: Optional[float] = None     # Total Debt / Total Assets
    promoter_capital: Optional[float] = None
    promoter_contribution_ratio: Optional[float] = None
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class LeverageAnalysisResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    years: List[LeverageYear] = Field(default_factory=list)
    initial_der: Optional[float] = None
    closing_der: Optional[float] = None
    initial_tol_tnw: Optional[float] = None
    leverage_trend: CoverageTrend = CoverageTrend.STABLE
    debt_proportion_of_financing: Optional[float] = None
    reason_code: Optional[ReasonCode] = None


# 8. Banking Ratios & Investment Returns
class ICRYear(BaseModel):
    year: int
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    icr: Optional[float] = None
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    reason_code: Optional[ReasonCode] = None


class BankingRatiosResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    icr_years: List[ICRYear] = Field(default_factory=list)
    average_icr: Optional[float] = None
    minimum_icr: Optional[float] = None
    irr: Optional[float] = None
    npv: Optional[float] = None
    discount_rate: Optional[float] = None
    payback_period_years: Optional[float] = None
    return_metrics_status: AppraisalStatus = AppraisalStatus.RESOLVED
    return_metrics_notes: Optional[str] = None
    reason_code: Optional[ReasonCode] = None


# 9. Promoter Contribution
class PromoterContributionResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    total_project_cost: Optional[float] = None
    required_promoter_contribution: Optional[float] = None
    actual_promoter_contribution: Optional[float] = None
    contribution_percentage: Optional[float] = None
    required_percentage: Optional[float] = None
    gap_surplus: Optional[float] = None  # Actual - Required (>0 surplus, <0 gap)
    is_adequate: bool = True
    equity_debt_mix: Optional[str] = None  # e.g., "15:85"
    reason_code: Optional[ReasonCode] = None


# 10. Financing Structure
class FinancingStructureResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    total_project_cost: Optional[float] = None
    promoter_contribution: Optional[float] = None
    term_loan: Optional[float] = None
    working_capital_financing: Optional[float] = None
    other_financing: Optional[float] = None
    total_sources: Optional[float] = None
    total_uses: Optional[float] = None
    financing_gap_surplus: Optional[float] = None  # Sources - Uses
    debt_equity_mix: Optional[str] = None
    is_balanced: bool = True
    unresolved_component: Optional[str] = None
    reason_code: Optional[ReasonCode] = None


# 11. Risk Engine Models
class RiskFlag(BaseModel):
    category: RiskCategory
    severity: RiskSeverity
    reason_code: ReasonCode
    trigger: str
    evidence: str
    source: MetricSource
    affected_metric: str
    message: str
    mitigation_if_determinable: Optional[str] = None


class RiskEngineResult(BaseModel):
    total_flags: int = 0
    critical_flags: int = 0
    high_flags: int = 0
    medium_flags: int = 0
    low_flags: int = 0
    flags: List[RiskFlag] = Field(default_factory=list)


# 12. Viability Assessment
class ViabilityAssessmentResult(BaseModel):
    classification: ViabilityClassification
    reason_codes: List[ReasonCode] = Field(default_factory=list)
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    unresolved_dependencies: List[str] = Field(default_factory=list)


# 13. Validation Models
class AppraisalValidationCheck(BaseModel):
    check_id: str
    description: str
    status: ValidationState
    expected: Optional[Union[float, str]] = None
    actual: Optional[Union[float, str]] = None
    difference: Optional[float] = None
    tolerance: float = 0.01
    severity: RiskSeverity = RiskSeverity.CRITICAL
    message: str
    reason_code: Optional[ReasonCode] = None


class AppraisalValidationResult(BaseModel):
    all_passed: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    unresolved_checks: int = 0
    checks: List[AppraisalValidationCheck] = Field(default_factory=list)


# 14. Provenance
class MetricProvenanceRecord(BaseModel):
    metric: str
    period: Optional[Union[int, str]] = None
    value: Optional[Any] = None
    source: MetricSource
    source_reference: Optional[str] = None
    calculation_method: Optional[str] = None
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    dependencies: List[str] = Field(default_factory=list)
    confidence: float = 1.0


# 15. DPR-Ready Appraisal Summary
class AppraisalSummary(BaseModel):
    project_cost: Optional[float] = None
    promoter_contribution: Optional[float] = None
    promoter_contribution_pct: Optional[float] = None
    debt_exposure: Optional[float] = None
    financing_structure: Dict[str, Any] = Field(default_factory=dict)
    revenue_year1: Optional[float] = None
    ebitda_year1: Optional[float] = None
    pat_year1: Optional[float] = None
    average_dscr: Optional[float] = None
    minimum_dscr: Optional[float] = None
    icr_year1: Optional[float] = None
    break_even_sales_year1: Optional[float] = None
    break_even_utilization_pct_year1: Optional[float] = None
    margin_of_safety_pct_year1: Optional[float] = None
    current_ratio_year1: Optional[float] = None
    quick_ratio_year1: Optional[float] = None
    initial_der: Optional[float] = None
    initial_tol_tnw: Optional[float] = None
    roce_year1: Optional[float] = None
    roe_year1: Optional[float] = None
    roa_year1: Optional[float] = None
    irr: Optional[float] = None
    npv: Optional[float] = None
    discount_rate: Optional[float] = None
    payback_period_years: Optional[float] = None
    repayment_capacity: str = "ADEQUATE"
    liquidity_position: str = "ADEQUATE"
    working_capital_adequacy: str = "ADEQUATE"
    financial_viability: ViabilityClassification = ViabilityClassification.FINANCIALLY_VIABLE
    financial_risks_count: int = 0
    critical_risks_count: int = 0
    unresolved_critical_data: List[str] = Field(default_factory=list)
    validation_status: ValidationState = ValidationState.PASSED


# 16. Top-Level Banking Appraisal Result Container
class BankingAppraisalResult(BaseModel):
    status: AppraisalStatus = AppraisalStatus.RESOLVED
    metrics: Dict[str, Any] = Field(default_factory=dict)
    appraisal: AppraisalSummary
    viability: ViabilityAssessmentResult
    risk_flags: RiskEngineResult
    financing: FinancingStructureResult
    promoter_contribution: PromoterContributionResult
    debt_service: DebtServiceAnalysisResult
    repayment_capacity: RepaymentCapacityResult
    dscr: DSCRAnalysisResult
    break_even: BreakEvenAnalysisResult
    liquidity: LiquidityAnalysisResult
    profitability: ProfitabilityAnalysisResult
    leverage: LeverageAnalysisResult
    banking_ratios: BankingRatiosResult
    validation: AppraisalValidationResult
    critical_unknowns: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    provenance: List[MetricProvenanceRecord] = Field(default_factory=list)
    reason_codes: List[ReasonCode] = Field(default_factory=list)
