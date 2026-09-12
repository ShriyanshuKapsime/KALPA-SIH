"""
Stage 9: Institution-Grade Deterministic Financial Engine.
Coordinates deterministic financial calculations, scheme routing, loan structuring,
amortization schedules, profitability projections, cash flows, break-even, DSCR,
financial viability, beneficiary eligibility assessment, and alternative scheme routing
without using any Large Language Models.
"""
import uuid
import logging
from typing import Dict, Any, Optional, Union, List

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    FinancialAnalysisContainer,
    FinancialCalculatorRequest,
    FinancialCalculatorResponse,
    FinancialCalculatorResult,
    FinancialAuditMetadata,
    Stage9WorkflowState,
    FinancialProfileInput,
    BusinessProfileInput,
    BeneficiaryProfileInput,
    LocationProfileInput,
    ProjectAssumptionsInput,
    MoratoriumInterestMode,
    SchemeType,
    SchemeFinancialFit,
    BeneficiaryEligibilityAssessment,
    AlternativeSchemeRecommendation,
    EligibilityStatusEnum
)
from app.services.financial_engine.constants import (
    SCHEME_RULES,
    CALCULATION_VERSION,
    ENGINE_NAME,
    MORATORIUM_MODES,
    DEFAULT_MORATORIUM_MODE
)
from app.services.financial_engine.government_financing_schemes import (
    GOVERNMENT_SCHEMES_DATABASE,
    EligibilityStatus
)
from app.services.financial_engine.eligibility_router import (
    scheme_eligibility_router,
    SchemeEligibilityRouter
)
from app.services.financial_engine.benchmark_adapter import (
    financial_benchmark_adapter,
    FinancialBenchmarkAdapter
)
from app.services.financial_engine.loan_calculator import (
    loan_calculator,
    LoanCalculator
)
from app.services.financial_engine.amortization import (
    amortization_engine,
    AmortizationEngine
)
from app.services.financial_engine.capital_allocation import (
    capital_allocation_engine,
    CapitalAllocationEngine
)
from app.services.financial_engine.profitability import (
    profitability_engine,
    ProfitabilityEngine
)
from app.services.financial_engine.cash_flow import (
    cash_flow_engine,
    CashFlowEngine
)
from app.services.financial_engine.break_even import (
    break_even_engine,
    BreakEvenEngine
)
from app.services.financial_engine.viability import (
    viability_engine,
    ViabilityEngine
)

logger = logging.getLogger(__name__)


class FinancialEngine:
    """
    Main deterministic engine for Stage 9 Financial Analysis.
    Zero LLMs used for calculations. Auditable, reproducible Python financial math.
    """

    def __init__(self, benchmark_adapter: Optional[FinancialBenchmarkAdapter] = None):
        self.benchmark_adapter = benchmark_adapter or financial_benchmark_adapter
        self.eligibility_router = scheme_eligibility_router
        self.loan_calc = loan_calculator
        self.amort_engine = amortization_engine
        self.cap_alloc_engine = capital_allocation_engine
        self.profit_engine = profitability_engine
        self.cf_engine = cash_flow_engine
        self.be_engine = break_even_engine
        self.viability_engine = viability_engine

    def analyze(self, request: Union[FinancialAnalysisRequest, Dict[str, Any]]) -> FinancialAnalysisResponse:
        """
        Executes end-to-end deterministic financial evaluation for a business profile.
        """
        if isinstance(request, dict):
            req = FinancialAnalysisRequest(**request)
        else:
            req = request

        analysis_id = req.analysis_id or f"fin_{uuid.uuid4().hex[:12]}"
        session_id = req.session_id or f"sess_{uuid.uuid4().hex[:12]}"

        fin_prof = req.financial_profile
        biz_prof = req.business_profile
        ben_prof = req.beneficiary_profile or BeneficiaryProfileInput()
        loc_prof = req.location_profile
        proj_assumptions = req.project_assumptions

        logger.info(
            f"[FINANCIAL ENGINE] Starting deterministic evaluation for analysis_id={analysis_id}, "
            f"business_id={biz_prof.business_id}, available_margin={fin_prof.available_margin_capital}"
        )

        # -------------------------------------------------------------------------
        # 1. Benchmark Adapter Query
        # -------------------------------------------------------------------------
        benchmark_data = self.benchmark_adapter.get_benchmark_data(
            business_id=biz_prof.business_id,
            specific_business=biz_prof.specific_business,
            category=biz_prof.category,
            nic_code=biz_prof.nic_code
        )

        # -------------------------------------------------------------------------
        # 2. Scheme Routing & Project Financing
        # -------------------------------------------------------------------------
        scheme_result, project_financing, scheme_cfg = self.loan_calc.calculate_project_financing(
            available_margin_capital=fin_prof.available_margin_capital,
            preferred_project_cost=fin_prof.preferred_project_cost
        )

        effective_project_cost = project_financing.maximum_financeable_project_cost
        effective_loan = project_financing.estimated_financeable_loan
        effective_margin = project_financing.required_margin

        # -------------------------------------------------------------------------
        # 2b. Separated Financial Fit & Beneficiary Eligibility Evaluation
        # -------------------------------------------------------------------------
        financial_fit_dict = self.eligibility_router.evaluate_financial_fit(effective_project_cost)
        financial_fit = SchemeFinancialFit(**financial_fit_dict)

        beneficiary_eligibility_dict = self.eligibility_router.evaluate_beneficiary_eligibility(
            scheme_id=financial_fit.recommended_scheme,
            beneficiary_profile=ben_prof.model_dump() if hasattr(ben_prof, "model_dump") else dict(ben_prof),
            financial_profile=fin_prof.model_dump() if hasattr(fin_prof, "model_dump") else dict(fin_prof)
        )
        beneficiary_eligibility = BeneficiaryEligibilityAssessment(**beneficiary_eligibility_dict)

        # -------------------------------------------------------------------------
        # 2c. Deterministic Alternative Financing Recommendation Layer
        # -------------------------------------------------------------------------
        alt_options_list = self.eligibility_router.route_alternative_financing(
            project_cost=effective_project_cost,
            business_profile=biz_prof.model_dump() if hasattr(biz_prof, "model_dump") else dict(biz_prof),
            beneficiary_profile=ben_prof.model_dump() if hasattr(ben_prof, "model_dump") else dict(ben_prof),
            location_profile=loc_prof.model_dump() if hasattr(loc_prof, "model_dump") else dict(loc_prof)
        )
        alternative_financing_options = [
            AlternativeSchemeRecommendation(**opt) for opt in alt_options_list
        ]

        # -------------------------------------------------------------------------
        # 3. Capital Allocation Engine
        # -------------------------------------------------------------------------
        capital_structure = self.cap_alloc_engine.allocate_capital(
            total_project_cost=effective_project_cost,
            project_financing=project_financing,
            benchmark_data=benchmark_data,
            capex_override=proj_assumptions.capex_override,
            working_capital_override=proj_assumptions.working_capital_override
        )

        # -------------------------------------------------------------------------
        # 4. Loan Management & EMI Engine
        # -------------------------------------------------------------------------
        scheme_rules = SCHEME_RULES.get(scheme_result.recommended_scheme.value, SCHEME_RULES["TERM_LOAN_SCHEME"])
        loan_management = self.loan_calc.calculate_emi(
            principal=effective_loan,
            annual_rate=scheme_rules["annual_interest_rate"],
            tenure_months=scheme_rules["tenure_months"],
            moratorium_months=scheme_rules["moratorium_months"],
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )

        # -------------------------------------------------------------------------
        # 5. Amortization Schedule Generator
        # -------------------------------------------------------------------------
        repayment_schedule = self.amort_engine.generate_schedule(
            principal=loan_management.principal,
            annual_rate=loan_management.annual_interest_rate,
            tenure_months=loan_management.tenure_months,
            moratorium_months=loan_management.moratorium_months,
            monthly_emi=loan_management.monthly_emi,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )

        # -------------------------------------------------------------------------
        # 6. Profitability Projection Engine
        # -------------------------------------------------------------------------
        profitability = self.profit_engine.calculate_profitability(
            project_assumptions=proj_assumptions,
            loan_management=loan_management,
            benchmark_data=benchmark_data
        )

        # -------------------------------------------------------------------------
        # 7. Cash Flow Projection Engine
        # -------------------------------------------------------------------------
        cash_flow = self.cf_engine.project_cash_flows(
            project_financing=project_financing,
            capital_structure=capital_structure,
            loan_management=loan_management,
            profitability=profitability,
            repayment_schedule=repayment_schedule
        )

        # -------------------------------------------------------------------------
        # 8. Break-Even Analysis Engine
        # -------------------------------------------------------------------------
        break_even = self.be_engine.calculate_break_even(
            profitability=profitability,
            project_assumptions=proj_assumptions,
            benchmark_data=benchmark_data
        )

        # -------------------------------------------------------------------------
        # 9. DSCR & Financial Viability Assessment
        # -------------------------------------------------------------------------
        debt_service = self.viability_engine.evaluate_debt_service(
            profitability=profitability,
            loan_management=loan_management,
            repayment_schedule=repayment_schedule
        )
        viability = self.viability_engine.evaluate_viability(
            project_financing=project_financing,
            capital_structure=capital_structure,
            loan_management=loan_management,
            profitability=profitability,
            break_even=break_even,
            debt_service=debt_service
        )

        # -------------------------------------------------------------------------
        # 10. Audit Metadata
        # -------------------------------------------------------------------------
        benchmark_sources = []
        if benchmark_data:
            benchmark_sources.append({
                "source_id": benchmark_data.source_id,
                "organization": benchmark_data.organization,
                "document_name": benchmark_data.document_name,
                "publication_year": benchmark_data.publication_year,
                "confidence": benchmark_data.confidence
            })

        user_inputs = {
            "available_margin_capital": fin_prof.available_margin_capital,
            "preferred_project_cost": fin_prof.preferred_project_cost,
            "existing_monthly_income": fin_prof.existing_monthly_income,
            "existing_monthly_debt": fin_prof.existing_monthly_debt_obligations,
            "expected_revenue": proj_assumptions.expected_monthly_revenue,
            "business_id": biz_prof.business_id,
            "specific_business": biz_prof.specific_business
        }

        assumptions_list = [
            f"Scheme: {financial_fit.scheme_name} ({financial_fit.annual_interest_rate*100:.1f}% p.a., {financial_fit.tenure_months} mo tenure, {financial_fit.moratorium_months} mo moratorium).",
            f"Beneficiary Eligibility Status: {beneficiary_eligibility.status.value} ({beneficiary_eligibility.advisory_notice}).",
            "Promoter Margin Requirement: 10.0% of total project cost.",
            "Debt Financing: 90.0% (capped by scheme rules).",
            "Moratorium Interest Mode: Interest-Only monthly servicing during moratorium period.",
            f"CapEx / Working Capital Split: {capital_structure.capex_percentage:.0f}% / {capital_structure.working_capital_percentage:.0f}% based on verified industry benchmarks.",
            "Calculations executed strictly using deterministic Python financial mathematics (Zero LLM reliance)."
        ]

        audit_meta = FinancialAuditMetadata(
            calculation_version=CALCULATION_VERSION,
            engine=ENGINE_NAME,
            engine_version="1.0.0",
            llm_used=False,
            scheme_rules_applied=SCHEME_RULES.get(scheme_result.recommended_scheme.value, {}),
            benchmark_sources=benchmark_sources,
            user_inputs=user_inputs,
            assumptions=assumptions_list
        )

        container = FinancialAnalysisContainer(
            scheme_result=scheme_result,
            financial_fit=financial_fit,
            beneficiary_eligibility=beneficiary_eligibility,
            alternative_financing_options=alternative_financing_options,
            project_financing=project_financing,
            capital_structure=capital_structure,
            loan_management=loan_management,
            repayment=repayment_schedule,
            profitability=profitability,
            cash_flow=cash_flow,
            break_even=break_even,
            debt_service=debt_service,
            financial_viability=viability
        )

        return FinancialAnalysisResponse(
            schema_version="1.0",
            analysis_id=analysis_id,
            session_id=session_id,
            workflow=Stage9WorkflowState(stage=9, state="FINANCIAL_VIABILITY_EVALUATED", status="complete"),
            financial_analysis=container,
            audit=audit_meta
        )

    def calculate(self, request: Union[FinancialCalculatorRequest, Dict[str, Any]]) -> FinancialCalculatorResponse:
        """
        Standalone loan and margin calculator supporting 4 distinct calculation modes.
        Separates Financial Fit from Beneficiary Eligibility.
        """
        if isinstance(request, dict):
            req = FinancialCalculatorRequest(**request)
        else:
            req = request

        avail_margin = req.available_margin_capital
        proj_cost = req.project_cost
        loan_amt = req.loan_amount

        audit_notes = []

        if loan_amt is not None and loan_amt > 0:
            # Mode 3: Direct Loan Amount Calculation
            theoretical_loan = float(loan_amt)
            theoretical_cost = round(theoretical_loan / 0.90, 2)
            required_margin = round(theoretical_cost * 0.10, 2)
            margin_input = avail_margin if avail_margin is not None else required_margin
            audit_notes.append(f"Calculated from specified loan amount ₹{theoretical_loan:,.0f}.")
        elif proj_cost is not None and proj_cost > 0:
            # Mode 2: Project Cost -> Required Margin
            theoretical_cost = float(proj_cost)
            required_margin = round(theoretical_cost * 0.10, 2)
            theoretical_loan = round(theoretical_cost * 0.90, 2)
            margin_input = avail_margin if avail_margin is not None else required_margin
            audit_notes.append(f"Calculated from specified project cost ₹{theoretical_cost:,.0f}.")
        else:
            # Mode 1: Available Margin -> Project Cost
            margin_input = float(avail_margin or 100000.0)
            theoretical_cost = round(margin_input / 0.10, 2)
            required_margin = margin_input
            theoretical_loan = round(theoretical_cost * 0.90, 2)
            audit_notes.append(f"Calculated from available promoter margin ₹{margin_input:,.0f}.")

        # Scheme Financial Fit
        financial_fit_dict = self.eligibility_router.evaluate_financial_fit(theoretical_cost)
        financial_fit = SchemeFinancialFit(**financial_fit_dict)

        # Beneficiary Eligibility Assessment (Default: VERIFICATION_REQUIRED unless verified profile provided)
        beneficiary_dict = self.eligibility_router.evaluate_beneficiary_eligibility(
            scheme_id=financial_fit.recommended_scheme,
            beneficiary_profile={"beneficiary_category": req.beneficiary_category} if req.beneficiary_category else {},
            financial_profile={"annual_family_income": req.annual_family_income} if req.annual_family_income else {}
        )
        beneficiary_eligibility = BeneficiaryEligibilityAssessment(**beneficiary_dict)

        # Alternative Options
        alt_options_list = self.eligibility_router.route_alternative_financing(
            project_cost=theoretical_cost
        )
        alternative_financing_options = [
            AlternativeSchemeRecommendation(**opt) for opt in alt_options_list
        ]

        scheme_cfg = GOVERNMENT_SCHEMES_DATABASE.get(req.scheme_id or financial_fit.recommended_scheme, GOVERNMENT_SCHEMES_DATABASE["TERM_LOAN_SCHEME"])

        rate = req.interest_rate_override if req.interest_rate_override is not None else float(scheme_cfg["annual_interest_rate"])
        tenure = req.tenure_months_override if req.tenure_months_override is not None else int(scheme_cfg["repayment_tenure_months"])
        moratorium = req.moratorium_months_override if req.moratorium_months_override is not None else int(scheme_cfg["moratorium_months"])

        # Loan capping
        capped_loan = min(theoretical_loan, scheme_cfg["maximum_loan_limit"])
        if capped_loan < theoretical_loan:
            audit_notes.append(f"Loan capped at scheme maximum ₹{scheme_cfg['maximum_loan_limit']:,.0f}.")

        # Calculate Loan Management & Schedules
        loan_mgmt = self.loan_calc.calculate_emi(
            principal=capped_loan,
            annual_rate=rate,
            tenure_months=tenure,
            moratorium_months=moratorium,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )

        schedule = self.amort_engine.generate_schedule(
            principal=loan_mgmt.principal,
            annual_rate=loan_mgmt.annual_interest_rate,
            tenure_months=loan_mgmt.tenure_months,
            moratorium_months=loan_mgmt.moratorium_months,
            monthly_emi=loan_mgmt.monthly_emi,
            moratorium_interest_mode=MoratoriumInterestMode.INTEREST_ONLY
        )

        q_obligation = round(loan_mgmt.monthly_emi * 3.0, 2)

        calc_result = FinancialCalculatorResult(
            available_margin_capital=float(margin_input),
            theoretical_project_cost=theoretical_cost,
            required_margin=required_margin,
            estimated_loan_requirement=capped_loan,
            recommended_scheme=scheme_cfg["scheme_id"],
            scheme_name=scheme_cfg["scheme_name"],
            annual_interest_rate=round(rate, 4),
            tenure_months=tenure,
            moratorium_months=moratorium,
            monthly_emi=loan_mgmt.monthly_emi,
            estimated_quarterly_obligation=q_obligation,
            total_interest=loan_mgmt.total_interest,
            total_repayment=loan_mgmt.total_repayment,
            financial_fit=financial_fit,
            beneficiary_eligibility=beneficiary_eligibility,
            eligibility_status=beneficiary_eligibility.status.value,
            verification_required=beneficiary_eligibility.verification_required,
            alternative_financing_options=alternative_financing_options,
            monthly_schedule=schedule.monthly_schedule,
            quarterly_schedule=schedule.quarterly_schedule,
            label="ESTIMATE / CALCULATION — Not a guaranteed loan approval. Eligibility requires verification."
        )

        return FinancialCalculatorResponse(
            schema_version="1.0",
            status="SUCCESS",
            calculator_result=calc_result,
            audit_notes=audit_notes
        )

    def health(self) -> Dict[str, Any]:
        """
        Returns financial engine health and capabilities.
        """
        return {
            "status": "healthy",
            "stage": 9,
            "engine": ENGINE_NAME,
            "version": CALCULATION_VERSION,
            "llm_used": False,
            "calculation_nature": "deterministic_python_financial_math",
            "schemes_supported": list(GOVERNMENT_SCHEMES_DATABASE.keys()),
            "moratorium_modes_supported": list(MORATORIUM_MODES.keys()),
            "dscr_benchmarking": True,
            "audit_grade_provenance": True,
            "beneficiary_eligibility_layer": True,
            "alternative_financing_router": True
        }


# Global singleton instance
financial_engine = FinancialEngine()
