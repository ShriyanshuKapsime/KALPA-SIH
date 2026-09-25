"""
Milestone 6: DPR Financial Packager Schema.
Defines canonical Pydantic models for the institutional-grade Bankable DPR / CMA package.
Enforces UNKNOWN != ZERO: missing upstream values remain None / UNKNOWN.
"""
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class CompletenessStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class FinancialEngineStatus(str, Enum):
    READY_FOR_DPR = "READY_FOR_DPR"
    READY_WITH_DISCLOSED_UNKNOWNS = "READY_WITH_DISCLOSED_UNKNOWNS"
    BLOCKED_PENDING_USER_INPUT = "BLOCKED_PENDING_USER_INPUT"
    ERROR = "ERROR"


class MetricDiagnostic(BaseModel):
    metric_name: str
    display_name: str
    status: str  # USER_PROVIDED, BENCHMARK, CALCULATED, NOT_AVAILABLE, DISCLOSED_UNKNOWN
    value: Optional[Union[float, int, str, bool]] = None
    formatted_value: Optional[str] = None
    source: Optional[str] = None
    reason_code: Optional[str] = None
    explanation: Optional[str] = None
    is_blocking: bool = False


class ProvenanceTag(str, Enum):
    PACKAGED_FROM_M1 = "PACKAGED_FROM_M1"
    PACKAGED_FROM_M2 = "PACKAGED_FROM_M2"
    PACKAGED_FROM_M3 = "PACKAGED_FROM_M3"
    PACKAGED_FROM_M4 = "PACKAGED_FROM_M4"
    PACKAGED_FROM_M5 = "PACKAGED_FROM_M5"
    PACKAGED_FROM_STAGE9_CORE = "PACKAGED_FROM_STAGE9_CORE"
    PACKAGED_FROM_UPSTREAM_PROFILE = "PACKAGED_FROM_UPSTREAM_PROFILE"


# -------------------------------------------------------------------------
# A. Project Identity
# -------------------------------------------------------------------------
class ProjectIdentityPackage(BaseModel):
    project_name: Optional[str] = None
    business_id: Optional[str] = None
    analysis_id: Optional[str] = None
    session_id: Optional[str] = None
    archetype: Optional[str] = None
    sector: Optional[str] = None
    category: Optional[str] = None
    nic_code: Optional[Union[str, int]] = None
    district: Optional[Union[str, Dict[str, Any]]] = None
    state: Optional[Union[str, Dict[str, Any]]] = None
    area_type: Optional[str] = None
    package_id: str
    generation_timestamp: str
    engine_version: str = "1.0.0"
    calculation_version: str = "2.0.0"
    is_authoritative: bool = True


# -------------------------------------------------------------------------
# B. Promoter Profile
# -------------------------------------------------------------------------
class PromoterProfilePackage(BaseModel):
    promoter_name: Optional[str] = None
    gender: Optional[str] = None
    category: Optional[str] = None  # General / SC / ST / OBC / Women
    experience_years: Optional[float] = None
    experience_description: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    available_margin_capital: Optional[float] = None
    effective_promoter_contribution: Optional[float] = None
    promoter_equity_ratio: Optional[float] = None
    existing_annual_income: Optional[float] = None
    existing_monthly_debt: Optional[float] = None
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_UPSTREAM_PROFILE.value


# -------------------------------------------------------------------------
# C. Project Cost
# -------------------------------------------------------------------------
class ProjectCostItem(BaseModel):
    item_id: str
    name: str
    amount: Optional[float] = None
    percentage_of_total: Optional[float] = None
    source: Optional[str] = None
    status: str = "RESOLVED"


class ProjectCostPackage(BaseModel):
    total_project_cost: Optional[float] = None
    land_and_building: Optional[float] = None
    plant_and_machinery: Optional[float] = None
    equipment_and_tools: Optional[float] = None
    furniture_and_fixtures: Optional[float] = None
    preliminary_and_preoperative: Optional[float] = None
    working_capital_margin: Optional[float] = None
    contingency_and_others: Optional[float] = None
    capex_subtotal: Optional[float] = None
    working_capital_subtotal: Optional[float] = None
    cost_basis: Optional[str] = None
    line_items: List[ProjectCostItem] = Field(default_factory=list)
    status: str = "RESOLVED"
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M2.value


# -------------------------------------------------------------------------
# D. Means of Finance / Sources & Uses
# -------------------------------------------------------------------------
class MeansOfFinanceItem(BaseModel):
    source_name: str
    amount: Optional[float] = None
    percentage: Optional[float] = None
    verified: bool = True
    status: str = "RESOLVED"


class MeansOfFinancePackage(BaseModel):
    promoter_contribution: Optional[float] = None
    term_loan: Optional[float] = None
    working_capital_loan: Optional[float] = None
    subsidy_grant: Optional[float] = None
    other_verified_financing: Optional[float] = None
    total_funding: Optional[float] = None
    total_project_cost: Optional[float] = None
    funding_gap: Optional[float] = None
    funding_surplus: Optional[float] = None
    is_gap_eliminated: bool = True
    promoter_margin_pct: Optional[float] = None
    debt_pct: Optional[float] = None
    scheme_name: Optional[str] = None
    reconciliation_status: str = "BALANCED"
    funding_sources: List[MeansOfFinanceItem] = Field(default_factory=list)
    uses_of_funds: List[ProjectCostItem] = Field(default_factory=list)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M3.value


# -------------------------------------------------------------------------
# E. Working Capital
# -------------------------------------------------------------------------
class WorkingCapitalYearPackage(BaseModel):
    year: int
    current_assets: Optional[float] = None
    raw_material_inventory: Optional[float] = None
    stock_in_process: Optional[float] = None
    finished_goods_inventory: Optional[float] = None
    receivables_debtors: Optional[float] = None
    cash_and_bank_balance: Optional[float] = None
    current_liabilities: Optional[float] = None
    trade_creditors: Optional[float] = None
    other_current_liabilities: Optional[float] = None
    working_capital_gap: Optional[float] = None
    margin_money_for_wc: Optional[float] = None
    bank_finance_wc: Optional[float] = None
    working_capital_movement: Optional[float] = None


class WorkingCapitalPackage(BaseModel):
    working_capital_requirement: Optional[float] = None
    operating_cycle_days: Optional[float] = None
    inventory_holding_days: Optional[float] = None
    debtor_collection_days: Optional[float] = None
    creditor_payment_days: Optional[float] = None
    cash_buffer_months: Optional[float] = None
    yearly_projections: List[WorkingCapitalYearPackage] = Field(default_factory=list)
    status: str = "RESOLVED"
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M2.value


# -------------------------------------------------------------------------
# F. Revenue & Operating Assumptions
# -------------------------------------------------------------------------
class MaterialAssumptionItem(BaseModel):
    driver_id: str
    name: str
    value: Optional[Union[float, int, str]] = None
    unit: Optional[str] = None
    source_type: Optional[str] = None  # USER_PROVIDED, BENCHMARK_DERIVED, VERIFIED, CALCULATED, SCHEME_DERIVED
    source_reference: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "RESOLVED"
    derivation_method: Optional[str] = None
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M1.value


class RevenueOperatingAssumptionsPackage(BaseModel):
    monthly_revenue_base: Optional[float] = None
    annual_revenue_base: Optional[float] = None
    units_per_month: Optional[float] = None
    unit_selling_price: Optional[float] = None
    capacity_utilization_y1: Optional[float] = None
    annual_revenue_growth_pct: Optional[float] = None
    cogs_ratio: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    fixed_operating_costs_annual: Optional[float] = None
    salaries_wages_annual: Optional[float] = None
    rent_utilities_annual: Optional[float] = None
    other_opex_annual: Optional[float] = None
    assumptions_list: List[MaterialAssumptionItem] = Field(default_factory=list)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M1.value


# -------------------------------------------------------------------------
# G. Projected Financial Statements (Year 1 to 5)
# -------------------------------------------------------------------------
class ProfitLossYearPackage(BaseModel):
    year: int
    gross_revenue: Optional[float] = None
    cogs: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    ebitda: Optional[float] = None
    depreciation: Optional[float] = None
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    pbt: Optional[float] = None
    tax_expense: Optional[float] = None
    pat: Optional[float] = None
    tax_status: Optional[str] = None
    tax_regime: Optional[str] = None
    ebitda_margin_pct: Optional[float] = None
    pat_margin_pct: Optional[float] = None
    net_profit_margin_pct: Optional[float] = None


class CashFlowYearPackage(BaseModel):
    year: int
    operating_cash_flow: Optional[float] = None
    cash_from_operations: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    cash_from_investing: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    cash_from_financing: Optional[float] = None
    net_cash_flow: Optional[float] = None
    net_change_in_cash: Optional[float] = None
    opening_cash_balance: Optional[float] = None
    closing_cash_balance: Optional[float] = None


class BalanceSheetYearPackage(BaseModel):
    year: int
    fixed_assets_gross: Optional[float] = None
    gross_fixed_assets: Optional[float] = None
    accumulated_depreciation: Optional[float] = None
    net_fixed_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_bank: Optional[float] = None
    total_assets: Optional[float] = None
    share_capital_promoter_equity: Optional[float] = None
    reserves_and_surplus: Optional[float] = None
    term_loan_outstanding: Optional[float] = None
    current_liabilities: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_liabilities_and_equity: Optional[float] = None
    is_balanced: bool = True


class DepreciationYearPackage(BaseModel):
    year: int
    opening_gross_block: Optional[float] = None
    additions: Optional[float] = None
    depreciation_rate_pct: Optional[float] = None
    depreciation_charge: Optional[float] = None
    closing_net_block: Optional[float] = None


class ProjectedFinancialStatementsPackage(BaseModel):
    projection_years: int = 5
    profit_and_loss: List[ProfitLossYearPackage] = Field(default_factory=list)
    balance_sheet: List[BalanceSheetYearPackage] = Field(default_factory=list)
    cash_flow_statement: List[CashFlowYearPackage] = Field(default_factory=list)
    cash_flow: List[CashFlowYearPackage] = Field(default_factory=list)
    depreciation_schedule: List[DepreciationYearPackage] = Field(default_factory=list)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M3.value


# -------------------------------------------------------------------------
# H. Profitability & Banking Metrics
# -------------------------------------------------------------------------
class BankingMetricsPackage(BaseModel):
    gross_margin_pct: Optional[float] = None
    ebitda_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    first_year_pat: Optional[float] = None
    first_year_pbt: Optional[float] = None
    first_year_tax: Optional[float] = None
    tax_status: Optional[str] = None
    current_ratio_y1: Optional[float] = None
    current_ratio_y2: Optional[float] = None
    current_ratio_y3: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_equity_ratio_initial: Optional[float] = None
    dscr_y1: Optional[float] = None
    dscr_y2: Optional[float] = None
    dscr_y3: Optional[float] = None
    dscr_y4: Optional[float] = None
    dscr_y5: Optional[float] = None
    average_dscr: Optional[float] = None
    minimum_dscr: Optional[float] = None
    interest_coverage_ratio: Optional[float] = None
    break_even_sales_amount: Optional[float] = None
    break_even_capacity_pct: Optional[float] = None
    return_on_capital_employed_pct: Optional[float] = None
    return_on_equity_pct: Optional[float] = None
    payback_period_years: Optional[float] = None
    npv: Optional[float] = None
    irr_pct: Optional[float] = None
    financial_health_score: Optional[float] = None
    viability_status: Optional[str] = None
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M4.value


# -------------------------------------------------------------------------
# I. Loan Structure & Repayment
# -------------------------------------------------------------------------
class RepaymentInstallment(BaseModel):
    period: int  # Month or Quarter number
    period_label: str
    opening_balance: Optional[float] = None
    principal_component: Optional[float] = None
    interest_component: Optional[float] = None
    total_payment: Optional[float] = None
    closing_balance: Optional[float] = None
    is_moratorium: bool = False

    @property
    def payment(self) -> Optional[float]:
        return self.total_payment


class LoanStructurePackage(BaseModel):
    scheme_code: Optional[str] = None
    scheme_name: Optional[str] = None
    sanctioned_loan_amount: Optional[float] = None
    annual_interest_rate_pct: Optional[float] = None
    tenure_months: Optional[int] = None
    moratorium_months: Optional[int] = None
    monthly_emi: Optional[float] = None
    total_interest_payable: Optional[float] = None
    total_repayment_obligation: Optional[float] = None
    moratorium_interest_total: Optional[float] = None
    annual_debt_service: Optional[float] = None
    monthly_schedule: List[RepaymentInstallment] = Field(default_factory=list)
    quarterly_schedule: List[RepaymentInstallment] = Field(default_factory=list)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_STAGE9_CORE.value

    @property
    def repayment_schedule(self) -> List[RepaymentInstallment]:
        return self.monthly_schedule


# -------------------------------------------------------------------------
# J. M5 Stress & Appraisal
# -------------------------------------------------------------------------
class StressScenarioPackage(BaseModel):
    scenario_type: str
    scenario_name: str
    revenue_shock_pct: Optional[float] = None
    cost_shock_pct: Optional[float] = None
    interest_shock_bps: Optional[float] = None
    stressed_dscr: Optional[float] = None
    stressed_pat: Optional[float] = None
    stressed_liquidity: Optional[float] = None
    is_resilient: Optional[bool] = None
    notes: Optional[str] = None


class M5StressAppraisalPackage(BaseModel):
    scenarios_tested: List[StressScenarioPackage] = Field(default_factory=list)
    worst_case_scenario: Optional[str] = None
    downside_dscr: Optional[float] = None
    downside_liquidity_months: Optional[float] = None
    financing_resilience_status: Optional[str] = None
    recommended_structure_id: Optional[str] = None
    recommended_scheme: Optional[str] = None
    recommended_loan_amount: Optional[float] = None
    recommended_tenure_months: Optional[int] = None
    funding_gap: Optional[float] = None
    margin_adequacy_status: Optional[str] = None
    decision_reasons: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    validation_status: Optional[str] = None
    financing_options: List[Dict[str, Any]] = Field(default_factory=list)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M5.value


# -------------------------------------------------------------------------
# K. Assumptions & Evidence Register
# -------------------------------------------------------------------------
class AssumptionsEvidencePackage(BaseModel):
    total_assumptions: int = 0
    resolved_count: int = 0
    unresolved_count: int = 0
    evidence_backed_count: int = 0
    benchmark_backed_count: int = 0
    user_provided_count: int = 0
    assumptions: List[MaterialAssumptionItem] = Field(default_factory=list)
    provenance_records: List[Dict[str, Any]] = Field(default_factory=list)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M1.value


# -------------------------------------------------------------------------
# L. Data Completeness & Validation
# -------------------------------------------------------------------------
class ValidationFailureDetail(BaseModel):
    module: str
    check_id: str
    severity: str  # ERROR, WARNING, INFO
    message: str
    unresolved_fields: List[str] = Field(default_factory=list)


class DataCompletenessPackage(BaseModel):
    status: CompletenessStatus = CompletenessStatus.COMPLETE
    financial_engine_status: FinancialEngineStatus = FinancialEngineStatus.READY_FOR_DPR
    required_fields_total: int
    resolved_fields: int
    unresolved_fields: List[str] = Field(default_factory=list)
    metric_diagnostics: List[MetricDiagnostic] = Field(default_factory=list)
    blocking_questions: List[Dict[str, Any]] = Field(default_factory=list)
    m3_validation_status: Optional[str] = None
    m4_validation_status: Optional[str] = None
    m5_validation_status: Optional[str] = None
    is_dpr_eligible: bool = True
    dpr_gate_reasons: List[str] = Field(default_factory=list)
    validation_failures: List[ValidationFailureDetail] = Field(default_factory=list)


# -------------------------------------------------------------------------
# M. Standardized 18 DPR Section Model
# -------------------------------------------------------------------------
class DPRSection(BaseModel):
    section_number: int
    section_code: str
    title: str
    summary_text: str
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    notes_and_disclosures: List[str] = Field(default_factory=list)
    status: str = "RESOLVED"
    provenance_tag: str


# -------------------------------------------------------------------------
# N. CMA-Style Package
# -------------------------------------------------------------------------
class CMAStatementPackage(BaseModel):
    cma_form_1_project_cost_means_of_finance: Dict[str, Any] = Field(default_factory=dict)
    cma_form_2_operating_statement: List[Dict[str, Any]] = Field(default_factory=list)
    cma_form_3_balance_sheet_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    cma_form_4_cash_flow_statement: List[Dict[str, Any]] = Field(default_factory=list)
    cma_form_5_working_capital_assessment: Dict[str, Any] = Field(default_factory=dict)
    cma_form_6_ratio_analysis: Dict[str, Any] = Field(default_factory=dict)
    provenance_tag: str = ProvenanceTag.PACKAGED_FROM_M3.value


# -------------------------------------------------------------------------
# Master Canonical DPR Financial Package
# -------------------------------------------------------------------------
class DPRFinancialPackage(BaseModel):
    schema_version: str = "1.0.0"
    package_id: str
    generation_timestamp: str
    financial_engine_status: FinancialEngineStatus = FinancialEngineStatus.READY_FOR_DPR
    project_identity: ProjectIdentityPackage
    promoter_profile: PromoterProfilePackage
    project_cost: ProjectCostPackage
    means_of_finance: MeansOfFinancePackage
    working_capital: WorkingCapitalPackage
    revenue_operating_assumptions: RevenueOperatingAssumptionsPackage
    projected_financial_statements: ProjectedFinancialStatementsPackage
    banking_metrics: BankingMetricsPackage
    loan_structure: LoanStructurePackage
    m5_stress_appraisal: M5StressAppraisalPackage
    assumptions_evidence: AssumptionsEvidencePackage
    data_completeness: DataCompletenessPackage
    metric_diagnostics: List[MetricDiagnostic] = Field(default_factory=list)
    cma_statements: CMAStatementPackage
    sections: List[DPRSection] = Field(default_factory=list)
    is_dpr_eligible: bool = True
    draft_only: bool = False
