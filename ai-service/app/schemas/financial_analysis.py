"""
Pydantic Schemas for Stage 9: Institution-Grade Deterministic Financial Engine.
Defines strict data models for project financing, scheme routing, loan management,
amortization schedules, profitability projections, cash flows, break-even, DSCR,
financial viability, beneficiary eligibility assessment, alternative financing router,
and standalone interactive calculator endpoints.
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class FinancialViabilityLevel(str, Enum):
    FINANCIALLY_STRONG = "FINANCIALLY_STRONG"
    FINANCIALLY_VIABLE = "FINANCIALLY_VIABLE"
    FINANCIALLY_CAUTION = "FINANCIALLY_CAUTION"
    FINANCIALLY_STRESSED = "FINANCIALLY_STRESSED"
    INSUFFICIENT_FINANCIAL_DATA = "INSUFFICIENT_FINANCIAL_DATA"


class SchemeType(str, Enum):
    MICRO_FINANCE_SCHEME = "MICRO_FINANCE_SCHEME"
    TERM_LOAN_SCHEME = "TERM_LOAN_SCHEME"
    NO_SUPPORTED_SCHEME = "NO_SUPPORTED_SCHEME"


class EligibilityStatusEnum(str, Enum):
    ELIGIBLE_BASED_ON_PROVIDED_DATA = "ELIGIBLE_BASED_ON_PROVIDED_DATA"
    NOT_ELIGIBLE_BASED_ON_PROVIDED_DATA = "NOT_ELIGIBLE_BASED_ON_PROVIDED_DATA"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MoratoriumInterestMode(str, Enum):
    INTEREST_ONLY = "INTEREST_ONLY"
    INTEREST_CAPITALIZED = "INTEREST_CAPITALIZED"
    FULL_PAYMENT_HOLIDAY = "FULL_PAYMENT_HOLIDAY"


class DSCRStatus(str, Enum):
    STRONG = "STRONG"
    ADEQUATE = "ADEQUATE"
    WEAK = "WEAK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class CalculationStatus(str, Enum):
    CALCULATED = "CALCULATED"
    BENCHMARK_DERIVED = "BENCHMARK_DERIVED"
    USER_PROVIDED = "USER_PROVIDED"
    BENCHMARK_DATA_UNAVAILABLE = "BENCHMARK_DATA_UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# -----------------------------------------------------------------------------
# Scheme & Eligibility Models (Separated Financial Fit vs Beneficiary Eligibility)
# -----------------------------------------------------------------------------

class SchemeFinancialFit(BaseModel):
    recommended_scheme: str
    scheme_name: str
    administering_institution: str = "Scheduled Commercial Banks / MSME Finance"
    reason: str
    min_project_cost: float = 0.0
    max_project_cost: float = 5000000.0
    margin_percentage: float = 10.0
    max_financing_percentage: float = 90.0
    maximum_loan_limit: float = 4500000.0
    annual_interest_rate: float = 0.08
    tenure_months: int = 84
    moratorium_months: int = 6
    moratorium_interest_mode: str = "INTEREST_ONLY"
    source_provenance: Optional[Dict[str, Any]] = None


class BeneficiaryEligibilityAssessment(BaseModel):
    status: EligibilityStatusEnum = EligibilityStatusEnum.VERIFICATION_REQUIRED
    verification_required: bool = True
    criteria_checked: List[str] = Field(default_factory=list)
    criteria_missing: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    required_verification_fields: List[str] = Field(default_factory=list)
    target_beneficiary_description: str = ""
    advisory_notice: str = "Scheme eligibility requires formal verification by the administering agency or lending bank before sanction."


class AlternativeSchemeRecommendation(BaseModel):
    scheme_id: str
    scheme_name: str
    administering_institution: str
    relevance_status: str  # HIGHLY_RELEVANT | POTENTIALLY_APPLICABLE | EXPLORATORY
    why_relevant: str
    key_project_fit: str
    max_financing_limit: float
    target_beneficiary: str
    eligibility_information_required: List[str] = Field(default_factory=list)
    verification_required: bool = True
    official_source_reference: Optional[Dict[str, Any]] = None


# Backward-compatible SchemeResult wrapper
class SchemeResult(BaseModel):
    status: str = "MATCHED"  # MATCHED | NO_SUPPORTED_SCHEME | EXCEEDS_LIMIT
    recommended_scheme: SchemeType = SchemeType.TERM_LOAN_SCHEME
    scheme_name: str
    scheme_id: str
    eligibility_status: str = "VERIFICATION_REQUIRED"
    eligibility_notes: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Component Models
# -----------------------------------------------------------------------------

class ProjectFinancing(BaseModel):
    available_margin: float = Field(..., ge=0.0)
    theoretical_project_cost: float = Field(..., ge=0.0)
    required_margin: float = Field(..., ge=0.0)
    theoretical_loan_requirement: float = Field(..., ge=0.0)
    scheme_maximum_loan: float = Field(..., ge=0.0)
    scheme_limited_loan: float = Field(..., ge=0.0)
    estimated_financeable_loan: float = Field(..., ge=0.0)
    maximum_financeable_project_cost: float = Field(..., ge=0.0)
    excess_margin: float = Field(default=0.0, ge=0.0)


class CapitalStructure(BaseModel):
    total_project_cost: float = Field(..., ge=0.0)
    fixed_capital_capex: float = Field(..., ge=0.0)
    working_capital: float = Field(..., ge=0.0)
    capex_percentage: float = Field(default=70.0, ge=0.0, le=100.0)
    working_capital_percentage: float = Field(default=30.0, ge=0.0, le=100.0)
    margin_contribution: float = Field(..., ge=0.0)
    loan_component: float = Field(..., ge=0.0)
    source: str = "BENCHMARK_DATABASE"


class LoanManagement(BaseModel):
    principal: float = Field(..., ge=0.0)
    annual_interest_rate: float = Field(..., ge=0.0)
    monthly_interest_rate: float = Field(..., ge=0.0)
    tenure_months: int = Field(..., ge=1)
    moratorium_months: int = Field(default=0, ge=0)
    moratorium_interest_mode: MoratoriumInterestMode = MoratoriumInterestMode.INTEREST_ONLY
    moratorium_interest_total: float = Field(default=0.0, ge=0.0)
    monthly_emi: float = Field(..., ge=0.0)
    total_interest: float = Field(..., ge=0.0)
    total_repayment: float = Field(..., ge=0.0)
    assumption_statement: str = "Moratorium calculation assumption: Interest serviced monthly during moratorium."


class AmortizationRow(BaseModel):
    period: int
    phase: str  # MORATORIUM | REPAYMENT
    opening_balance: float
    payment: float
    principal_component: float
    interest_component: float
    closing_balance: float


class QuarterlyRepaymentRow(BaseModel):
    quarter: int
    months: List[int]
    opening_balance: float
    total_payment: float
    principal_paid: float
    interest_paid: float
    closing_balance: float


class RepaymentSchedule(BaseModel):
    monthly_schedule: List[AmortizationRow] = Field(default_factory=list)
    quarterly_schedule: List[QuarterlyRepaymentRow] = Field(default_factory=list)
    first_repayment_month: int = 1
    total_periods: int = 84


class ProfitabilityProjection(BaseModel):
    status: CalculationStatus = CalculationStatus.CALCULATED
    monthly_revenue: Optional[float] = None
    annual_revenue: Optional[float] = None
    monthly_cogs: Optional[float] = None
    annual_cogs: Optional[float] = None
    monthly_gross_profit: Optional[float] = None
    annual_gross_profit: Optional[float] = None
    gross_margin_percentage: Optional[float] = None
    monthly_operating_expenses: Optional[float] = None
    annual_operating_expenses: Optional[float] = None
    monthly_operating_profit: Optional[float] = None
    annual_operating_profit: Optional[float] = None
    operating_margin_percentage: Optional[float] = None
    monthly_debt_service: Optional[float] = None
    annual_debt_service: Optional[float] = None
    monthly_net_cash_after_debt: Optional[float] = None
    annual_net_cash_after_debt: Optional[float] = None
    source: str = "BENCHMARK_DATABASE"
    notes: Optional[str] = None


class Month0Deployment(BaseModel):
    margin_injection: float
    loan_inflow: float
    capex_outflow: float
    working_capital_allocation: float
    closing_cash_balance: float


class MonthlyCashFlowRow(BaseModel):
    month: int
    opening_cash: float
    revenue_inflow: float
    cogs_outflow: float
    opex_outflow: float
    debt_service_outflow: float
    total_outflows: float
    net_cash_flow: float
    closing_cash: float


class AnnualCashFlowSummary(BaseModel):
    year: int
    annual_revenue: float
    annual_expenses: float
    annual_debt_service: float
    annual_net_cash_flow: float
    closing_cash_balance: float


class CashFlowAnalysis(BaseModel):
    status: CalculationStatus = CalculationStatus.CALCULATED
    month_0_deployment: Optional[Month0Deployment] = None
    monthly_projection: List[MonthlyCashFlowRow] = Field(default_factory=list)
    annual_summary: List[AnnualCashFlowSummary] = Field(default_factory=list)
    notes: Optional[str] = None


class BreakEvenAnalysis(BaseModel):
    status: CalculationStatus = CalculationStatus.CALCULATED
    monthly_fixed_costs: Optional[float] = None
    contribution_margin: Optional[float] = None
    contribution_margin_ratio: Optional[float] = None
    monthly_break_even_revenue: Optional[float] = None
    annual_break_even_revenue: Optional[float] = None
    break_even_utilization_pct: Optional[float] = None
    break_even_units: Optional[float] = None
    months_to_break_even: Optional[int] = None
    notes: Optional[str] = None


class DebtServiceAnalysis(BaseModel):
    dscr: Optional[float] = None
    status: DSCRStatus = DSCRStatus.INSUFFICIENT_DATA
    operating_cash_flow_basis: Optional[float] = None
    debt_service_basis: Optional[float] = None
    evaluation_notes: str = ""


class FinancialViabilityResult(BaseModel):
    level: FinancialViabilityLevel = FinancialViabilityLevel.FINANCIALLY_VIABLE
    financial_health_score: float = Field(default=75.0, ge=0.0, le=100.0)
    component_scores: Dict[str, float] = Field(default_factory=dict)
    positive_factors: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class FinancialAuditMetadata(BaseModel):
    calculation_version: str = "stage9_v1"
    engine: str = "deterministic_financial_engine"
    engine_version: str = "1.0.0"
    llm_used: bool = False
    scheme_rules_applied: Dict[str, Any] = Field(default_factory=dict)
    benchmark_sources: List[Dict[str, Any]] = Field(default_factory=list)
    user_inputs: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)


class FinancialAnalysisContainer(BaseModel):
    scheme_result: SchemeResult
    financial_fit: SchemeFinancialFit
    beneficiary_eligibility: BeneficiaryEligibilityAssessment
    alternative_financing_options: List[AlternativeSchemeRecommendation] = Field(default_factory=list)
    project_financing: ProjectFinancing
    capital_structure: CapitalStructure
    loan_management: LoanManagement
    repayment: RepaymentSchedule
    profitability: ProfitabilityProjection
    cash_flow: CashFlowAnalysis
    break_even: BreakEvenAnalysis
    debt_service: DebtServiceAnalysis
    financial_viability: FinancialViabilityResult


class Stage9WorkflowState(BaseModel):
    stage: int = 9
    state: str = "FINANCIAL_VIABILITY_EVALUATED"
    status: str = "complete"


# -----------------------------------------------------------------------------
# Top-Level Request & Response Models
# -----------------------------------------------------------------------------

class FinancialProfileInput(BaseModel):
    available_margin_capital: float = Field(default=100000.0, ge=0.0)
    preferred_project_cost: Optional[float] = None
    existing_monthly_income: Optional[float] = None
    existing_monthly_debt_obligations: Optional[float] = None
    annual_family_income: Optional[float] = None


class BusinessProfileInput(BaseModel):
    business_id: Optional[str] = None
    specific_business: Optional[str] = None
    sector: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    nic_code: Optional[str] = None


class BeneficiaryProfileInput(BaseModel):
    beneficiary_category: Optional[str] = None  # General, OBC, SC, ST, Minority, Women
    gender: Optional[str] = None
    annual_family_income: Optional[float] = None
    identity_proof_provided: Optional[bool] = None
    aadhaar_verified: Optional[bool] = None
    udyam_registration: Optional[str] = None
    no_prior_defaults: Optional[bool] = None
    is_greenfield: Optional[bool] = True
    is_shg_member: Optional[bool] = False


class LocationProfileInput(BaseModel):
    village: Optional[str] = None
    block: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    area_type: Optional[str] = None  # Rural / Urban


class ProjectAssumptionsInput(BaseModel):
    expected_monthly_revenue: Optional[float] = None
    expected_monthly_units: Optional[float] = None
    expected_unit_price: Optional[float] = None
    capex_override: Optional[float] = None
    working_capital_override: Optional[float] = None


class FinancialAnalysisRequest(BaseModel):
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    financial_profile: FinancialProfileInput = Field(default_factory=FinancialProfileInput)
    business_profile: BusinessProfileInput = Field(default_factory=BusinessProfileInput)
    beneficiary_profile: Optional[BeneficiaryProfileInput] = Field(default_factory=BeneficiaryProfileInput)
    location_profile: LocationProfileInput = Field(default_factory=LocationProfileInput)
    project_assumptions: ProjectAssumptionsInput = Field(default_factory=ProjectAssumptionsInput)


class FinancialAnalysisResponse(BaseModel):
    schema_version: str = "1.0"
    analysis_id: str
    session_id: str
    workflow: Stage9WorkflowState = Field(default_factory=Stage9WorkflowState)
    financial_analysis: FinancialAnalysisContainer
    audit: FinancialAuditMetadata


# -----------------------------------------------------------------------------
# Standalone Calculator Models
# -----------------------------------------------------------------------------

class FinancialCalculatorRequest(BaseModel):
    available_margin_capital: Optional[float] = None
    project_cost: Optional[float] = None
    loan_amount: Optional[float] = None
    scheme_id: Optional[str] = None
    interest_rate_override: Optional[float] = None
    tenure_months_override: Optional[int] = None
    moratorium_months_override: Optional[int] = None
    beneficiary_category: Optional[str] = None
    annual_family_income: Optional[float] = None


class FinancialCalculatorResult(BaseModel):
    available_margin_capital: float
    theoretical_project_cost: float
    required_margin: float
    estimated_loan_requirement: float
    recommended_scheme: str
    scheme_name: str
    annual_interest_rate: float
    tenure_months: int
    moratorium_months: int
    monthly_emi: float
    estimated_quarterly_obligation: float
    total_interest: float
    total_repayment: float
    financial_fit: SchemeFinancialFit
    beneficiary_eligibility: BeneficiaryEligibilityAssessment
    eligibility_status: str = "VERIFICATION_REQUIRED"
    verification_required: bool = True
    alternative_financing_options: List[AlternativeSchemeRecommendation] = Field(default_factory=list)
    monthly_schedule: List[AmortizationRow] = Field(default_factory=list)
    quarterly_schedule: List[QuarterlyRepaymentRow] = Field(default_factory=list)
    label: str = "ESTIMATE / CALCULATION — Not a guaranteed loan approval."


class FinancialCalculatorResponse(BaseModel):
    schema_version: str = "1.0"
    status: str = "SUCCESS"
    calculator_result: FinancialCalculatorResult
    audit_notes: List[str] = Field(default_factory=list)
