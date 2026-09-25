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
    total_project_cost: Optional[float] = None


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
    itemized_opex: Dict[str, float] = Field(default_factory=dict)
    monthly_operating_profit: Optional[float] = None  # EBITDA
    annual_operating_profit: Optional[float] = None   # EBITDA
    monthly_ebitda: Optional[float] = None
    annual_ebitda: Optional[float] = None
    operating_margin_percentage: Optional[float] = None
    monthly_depreciation: Optional[float] = None
    annual_depreciation: Optional[float] = None
    monthly_interest: Optional[float] = None
    annual_interest: Optional[float] = None
    monthly_pbt: Optional[float] = None
    annual_pbt: Optional[float] = None
    monthly_pat: Optional[float] = None
    annual_pat: Optional[float] = None
    calculated_net_margin_pct: Optional[float] = None
    benchmark_net_margin_pct: Optional[float] = None
    tax_status: str = "UNRESOLVED"
    tax_rate_pct: Optional[float] = None
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


class FoundationConfidenceSummary(BaseModel):
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    resolved: int = 0
    total: int = 0
    user_required: int = 0
    unknown: int = 0


# -----------------------------------------------------------------------------
# Milestone 2: Automated Project Cost & Working Capital Engine Schemas
# -----------------------------------------------------------------------------

class ProjectCostComponent(BaseModel):
    """Component breakdown of project cost with full auditable provenance."""
    component_id: str
    name: str
    amount: Optional[float] = None
    unit: str = "INR"
    source_type: str = "CALCULATED"
    source_id: Optional[str] = None
    confidence: float = 0.0
    calculation_method: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None
    status: str = "RESOLVED"  # RESOLVED, BENCHMARKED, CALCULATED, USER_SPECIFIED, UNKNOWN
    explanation: str = ""


class CapExDecomposition(BaseModel):
    """Detailed category decomposition of fixed capital / CapEx."""
    premises_setup: Optional[float] = None
    machinery_equipment: Optional[float] = None
    furniture_fixtures: Optional[float] = None
    tools_workwear: Optional[float] = None
    technology_pos: Optional[float] = None
    vehicles: Optional[float] = None
    other_fixed_assets: Optional[float] = None
    total_capex: Optional[float] = None
    source: str = "BENCHMARK_DERIVED"
    confidence: float = 0.80


class ProjectCostReconciliation(BaseModel):
    """Reconciliation comparing bottom-up cost with scheme financeable cost."""
    calculated_project_cost: Optional[float] = None
    scheme_financeable_project_cost: Optional[float] = None
    user_requested_project_cost: Optional[float] = None
    variance: Optional[float] = None
    reconciliation_status: str = "FULLY_RECONCILED"  # FULLY_RECONCILED, FINANCING_CONSTRAINED, PARTIALLY_DERIVED, INSUFFICIENT_DATA
    reconciliation_explanation: str = ""
    promoter_margin: Optional[float] = None
    debt_component: Optional[float] = None
    unexplained_amount: float = 0.0


class WorkingCapitalAnalysis(BaseModel):
    """Deterministic Working Capital assessment by financial archetype."""
    status: str = "RESOLVED"
    inventory_requirement: Optional[float] = None
    receivable_requirement: Optional[float] = None
    payable_credit: Optional[float] = None
    operating_cash_buffer: Optional[float] = None
    operating_cycle_days: Optional[float] = None
    total_working_capital: Optional[float] = None
    operating_working_capital: Optional[float] = None
    methodology: str = "OPERATING_CYCLE"
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    notes: Optional[str] = None


class ProjectCostAnalysis(BaseModel):
    """Institutional-grade project cost decomposition and reconciliation."""
    status: str = "RESOLVED"
    total_project_cost: Optional[float] = None
    capex: Optional[float] = None
    opening_inventory: Optional[float] = None
    working_capital: Optional[float] = None
    pre_operating_cost: Optional[float] = None
    contingency: Optional[float] = None
    promoter_margin: Optional[float] = None
    debt_component: Optional[float] = None
    unexplained_amount: float = 0.0
    capex_decomposition: Optional[CapExDecomposition] = None
    reconciliation: Optional[ProjectCostReconciliation] = None
    components: List[ProjectCostComponent] = Field(default_factory=list)
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0


# -----------------------------------------------------------------------------
# Milestone 3: Financial Projection & Statement Engine Schemas
# -----------------------------------------------------------------------------

class ProjectionYear(BaseModel):
    year: int
    label: str


class RevenueProjectionLine(BaseModel):
    year: int
    volume: Optional[float] = None
    price_per_unit: Optional[float] = None
    utilization_percentage: Optional[float] = None
    revenue: Optional[float] = None
    growth_rate: Optional[float] = None
    growth_source: Optional[str] = None
    growth_method: Optional[str] = None
    status: str = "RESOLVED"
    confidence: float = 0.0


class RevenueProjection(BaseModel):
    status: str = "RESOLVED"
    methodology: str = "DRIVER_BASED"
    base_annual_revenue: Optional[float] = None
    years: List[RevenueProjectionLine] = Field(default_factory=list)
    confidence: float = 0.0
    notes: Optional[str] = None


class CostProjectionLine(BaseModel):
    year: int
    cogs: Optional[float] = None
    raw_material: Optional[float] = None
    direct_labor: Optional[float] = None
    salaries_wages: Optional[float] = None
    rent: Optional[float] = None
    utilities_electricity: Optional[float] = None
    marketing: Optional[float] = None
    repairs_maintenance: Optional[float] = None
    admin_expenses: Optional[float] = None
    transport: Optional[float] = None
    technology_software: Optional[float] = None
    other_operating_expenses: Optional[float] = None
    total_operating_expenses: Optional[float] = None
    status: str = "RESOLVED"
    confidence: float = 0.0

    @property
    def salaries(self) -> Optional[float]:
        return self.salaries_wages

    @property
    def salary(self) -> Optional[float]:
        return self.salaries_wages

    @property
    def operating_expenses(self) -> Optional[float]:
        return self.total_operating_expenses

    @property
    def opex(self) -> Optional[float]:
        return self.total_operating_expenses


class CostProjection(BaseModel):
    status: str = "RESOLVED"
    years: List[CostProjectionLine] = Field(default_factory=list)
    confidence: float = 0.0
    notes: Optional[str] = None


class ProfitLossYear(BaseModel):
    year: int
    revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    gross_margin_percentage: Optional[float] = None
    operating_expenses: Optional[float] = None
    ebitda: Optional[float] = None
    ebitda_margin_percentage: Optional[float] = None
    depreciation: Optional[float] = None
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    profit_before_tax: Optional[float] = None
    tax_expense: Optional[float] = None
    tax_status: str = "NOT_MODELED"
    profit_after_tax: Optional[float] = None
    net_margin_percentage: Optional[float] = None
    status: str = "RESOLVED"


class ProfitLossStatement(BaseModel):
    status: str = "RESOLVED"
    years: List[ProfitLossYear] = Field(default_factory=list)
    notes: Optional[str] = None


class CashFlowYear(BaseModel):
    year: int
    profit_after_tax: Optional[float] = None
    depreciation: Optional[float] = None
    change_in_working_capital: Optional[float] = None
    cash_from_operations: Optional[float] = None
    capex_outflow: Optional[float] = None
    cash_from_investing: Optional[float] = None
    equity_inflow: Optional[float] = None
    loan_disbursement: Optional[float] = None
    principal_repayment: Optional[float] = None
    cash_from_financing: Optional[float] = None
    net_change_in_cash: Optional[float] = None
    opening_cash_balance: Optional[float] = None
    closing_cash_balance: Optional[float] = None
    status: str = "RESOLVED"


class CashFlowStatement(BaseModel):
    status: str = "RESOLVED"
    year_0_deployment: Optional[Dict[str, Any]] = None
    years: List[CashFlowYear] = Field(default_factory=list)
    notes: Optional[str] = None


class BalanceSheetYear(BaseModel):
    year: int
    gross_fixed_assets: Optional[float] = None
    accumulated_depreciation: Optional[float] = None
    net_fixed_assets: Optional[float] = None
    inventory: Optional[float] = None
    trade_receivables: Optional[float] = None
    cash_and_bank: Optional[float] = None
    other_current_assets: Optional[float] = None
    total_current_assets: Optional[float] = None
    total_assets: Optional[float] = None
    term_loan_outstanding: Optional[float] = None
    trade_payables: Optional[float] = None
    other_current_liabilities: Optional[float] = None
    total_liabilities: Optional[float] = None
    promoter_capital: Optional[float] = None
    retained_earnings: Optional[float] = None
    total_equity: Optional[float] = None
    total_liabilities_and_equity: Optional[float] = None
    reconciliation_difference: Optional[float] = None
    is_balanced: bool = False
    status: str = "RESOLVED"


class BalanceSheet(BaseModel):
    status: str = "BALANCED"
    years: List[BalanceSheetYear] = Field(default_factory=list)
    reconciliation_diagnostics: Optional[str] = None


class WorkingCapitalYear(BaseModel):
    year: int
    inventory: Optional[float] = None
    receivables: Optional[float] = None
    payables: Optional[float] = None
    operating_cash_buffer: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    net_working_capital: Optional[float] = None
    change_in_working_capital: Optional[float] = None
    operating_cycle_days: Optional[float] = None
    status: str = "RESOLVED"


class WorkingCapitalProjection(BaseModel):
    status: str = "RESOLVED"
    years: List[WorkingCapitalYear] = Field(default_factory=list)
    methodology: str = "TURNOVER_DAYS"
    notes: Optional[str] = None


class DepreciationScheduleYear(BaseModel):
    year: int
    gross_block: Optional[float] = None
    depreciation_amount: Optional[float] = None
    accumulated_depreciation: Optional[float] = None
    net_block: Optional[float] = None
    status: str = "RESOLVED"
    notes: str = ""


class FinancialRatioYear(BaseModel):
    year: int
    gross_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    ebit_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    working_capital_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    dscr: Optional[float] = None
    inventory_days: Optional[float] = None
    receivable_days: Optional[float] = None
    payable_days: Optional[float] = None
    cash_conversion_cycle: Optional[float] = None
    asset_turnover: Optional[float] = None


class FinancialRatioSet(BaseModel):
    status: str = "RESOLVED"
    years: List[FinancialRatioYear] = Field(default_factory=list)
    notes: Optional[str] = None


class FundingSourcesUses(BaseModel):
    status: str = "RECONCILED"
    capex: Optional[float] = None
    opening_inventory: Optional[float] = None
    working_capital_buffer: Optional[float] = None
    pre_operating_cost: Optional[float] = None
    contingency: Optional[float] = None
    total_uses: Optional[float] = None
    promoter_contribution: Optional[float] = None
    term_loan: Optional[float] = None
    other_financing: Optional[float] = None
    total_sources: Optional[float] = None
    difference: Optional[float] = None
    allocation_status: Optional[str] = "FULLY_ALLOCATED"
    notes: Optional[str] = None


class ProjectionValidationCheck(BaseModel):
    check_id: str
    status: str
    expected: Optional[Union[float, str]] = None
    actual: Optional[Union[float, str]] = None
    difference: Optional[float] = None
    tolerance: float = 0.01
    severity: str = "CRITICAL"
    message: str


class ProjectionValidation(BaseModel):
    all_passed: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    unresolved_checks: int = 0
    checks: List[ProjectionValidationCheck] = Field(default_factory=list)


class ProjectionProvenance(BaseModel):
    metric: str
    year: int
    value: Optional[Any] = None
    source_type: str = "CALCULATED"
    source_ids: List[str] = Field(default_factory=list)
    formula: Optional[str] = None
    driver_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.90
    status: str = "RESOLVED"


class ProjectionScenario(BaseModel):
    scenario_name: str
    revenue_growth_adjustment: float = 0.0
    cost_adjustment: float = 0.0
    description: str


class FinancialProjection(BaseModel):
    status: str = "RESOLVED"
    projection_years: int = 5
    revenue_projection: RevenueProjection
    cost_projection: CostProjection
    profit_loss_statement: ProfitLossStatement
    cash_flow_statement: CashFlowStatement
    balance_sheet: BalanceSheet
    working_capital_projection: WorkingCapitalProjection
    financial_ratios: FinancialRatioSet
    funding_sources_uses: FundingSourcesUses
    validation: ProjectionValidation
    scenarios: Dict[str, Any] = Field(default_factory=dict)
    provenance: List[ProjectionProvenance] = Field(default_factory=list)
    confidence: float = 0.85
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
    # Milestone 1: Financial Intelligence Foundation optional fields
    project_cost_basis: Optional[str] = "MARGIN_DERIVED"
    financial_archetype: Optional[str] = None
    assumption_status: Optional[str] = None
    assumptions: List[Dict[str, Any]] = Field(default_factory=list)
    required_user_inputs: List[Dict[str, Any]] = Field(default_factory=list)
    assumption_confidence: Optional[Union[FoundationConfidenceSummary, Dict[str, Any]]] = None
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    model_version: Optional[str] = None
    # Milestone 2: Project Cost & Working Capital Engine optional fields
    project_cost_analysis: Optional[ProjectCostAnalysis] = None
    working_capital_analysis: Optional[WorkingCapitalAnalysis] = None
    # Milestone 3: Financial Projection & Statement Engine optional fields
    financial_projection: Optional[FinancialProjection] = None
    profit_loss_statement: Optional[ProfitLossStatement] = None
    cash_flow_statement: Optional[CashFlowStatement] = None
    balance_sheet: Optional[BalanceSheet] = None
    working_capital_projection: Optional[WorkingCapitalProjection] = None
    financial_ratios: Optional[FinancialRatioSet] = None
    funding_sources_uses: Optional[FundingSourcesUses] = None
    projection_validation: Optional[ProjectionValidation] = None
    projection_provenance: Optional[List[ProjectionProvenance]] = None
    projection_scenarios: Optional[Dict[str, Any]] = None
    # Milestone 4: Banking Appraisal & Viability Engine optional fields
    banking_appraisal: Optional[Any] = None
    # Milestone 5: Stress Testing, Scheme Routing & Financing Optimizer optional fields
    financing_optimizer: Optional[Any] = None
    # Milestone 6: Bankable DPR Financial Packager optional fields
    dpr_financial_package: Optional[Any] = None
    # Canonical Downstream Financial Context
    financial_context: Optional[Any] = None


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
    nic_code: Optional[Union[str, int]] = None
    business_constitution: Optional[str] = None
    constitution: Optional[str] = None
    entity_type: Optional[str] = None
    registration_type: Optional[str] = None


class BeneficiaryProfileInput(BaseModel):
    beneficiary_category: Optional[str] = None  # General, OBC, SC, ST, Minority, Women
    gender: Optional[str] = None
    annual_family_income: Optional[float] = None
    identity_proof_provided: Optional[bool] = None
    aadhaar_verified: Optional[bool] = None
    udyam_registration: Optional[Union[str, bool]] = None
    no_prior_defaults: Optional[bool] = None
    is_greenfield: Optional[bool] = True
    is_shg_member: Optional[bool] = False


class LocationProfileInput(BaseModel):
    village: Optional[str] = None
    block: Optional[str] = None
    district: Optional[Union[str, Dict[str, Any]]] = None
    state: Optional[Union[str, Dict[str, Any]]] = None
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
    market_data: Optional[Dict[str, Any]] = None
    user_driver_inputs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    language: Optional[str] = "en"


class FinancialAnalysisResponse(BaseModel):
    schema_version: str = "1.0"
    analysis_id: str
    session_id: str
    workflow: Stage9WorkflowState = Field(default_factory=Stage9WorkflowState)
    financial_analysis: FinancialAnalysisContainer
    audit: FinancialAuditMetadata
    financial_context: Optional[Any] = None


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
