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
    EligibilityStatusEnum,
    ProjectCostAnalysis,
    WorkingCapitalAnalysis
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
from app.services.financial_engine.compatibility.legacy_adapter import (
    legacy_adapter,
    LegacyAdapter
)
from app.services.financial_engine.projection import (
    projection_engine,
    ProjectionEngine
)
from app.services.financial_engine.appraisal import (
    appraisal_engine,
    AppraisalEngine
)
from app.services.financial_engine.optimizer import (
    m5_engine,
    M5Engine
)
from app.services.financial_engine.dpr_packager import (
    dpr_packager,
    DPRPackager,
    DPRFinancialPackage
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
        self.legacy_adapter = legacy_adapter
        self.projection_engine = projection_engine
        self.appraisal_engine = appraisal_engine
        self.m5_engine = m5_engine
        self.dpr_packager = dpr_packager

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
        # 2d. Accurate Project-Cost Provenance Basis & Driver Input Preparation
        # -------------------------------------------------------------------------
        if fin_prof.preferred_project_cost is not None and fin_prof.preferred_project_cost > 0:
            cost_basis = "USER_SPECIFIED"
        elif project_financing.theoretical_loan_requirement > project_financing.scheme_limited_loan:
            cost_basis = "SCHEME_CAPPED"
        else:
            cost_basis = "MARGIN_DERIVED"

        user_inputs = {
            "available_margin_capital": fin_prof.available_margin_capital,
            "preferred_project_cost": fin_prof.preferred_project_cost,
            "existing_monthly_income": fin_prof.existing_monthly_income,
            "existing_monthly_debt": fin_prof.existing_monthly_debt_obligations,
            "annual_family_income": fin_prof.annual_family_income or ben_prof.annual_family_income,
            "expected_revenue": proj_assumptions.expected_monthly_revenue,
            "expected_monthly_revenue": proj_assumptions.expected_monthly_revenue,
            "monthly_revenue": proj_assumptions.expected_monthly_revenue,
            "expected_monthly_units": proj_assumptions.expected_monthly_units,
            "expected_unit_price": proj_assumptions.expected_unit_price,
            "selling_price": proj_assumptions.expected_unit_price,
            "monthly_units": proj_assumptions.expected_monthly_units,
            "capex_override": proj_assumptions.capex_override,
            "working_capital_override": proj_assumptions.working_capital_override,
            "business_id": biz_prof.business_id,
            "specific_business": biz_prof.specific_business,
            "sector": biz_prof.sector,
            "category": biz_prof.category,
            "subcategory": biz_prof.subcategory,
            "nic_code": biz_prof.nic_code,
            "business_constitution": (
                getattr(biz_prof, "business_constitution", None)
                or getattr(biz_prof, "constitution", None)
                or getattr(biz_prof, "entity_type", None)
                or getattr(biz_prof, "registration_type", None)
                or (req.user_driver_inputs.get("business_constitution") if getattr(req, "user_driver_inputs", None) else None)
            ),
            "district": loc_prof.district,
            "state": loc_prof.state,
            "area_type": loc_prof.area_type,
            "gender": ben_prof.gender,
            "beneficiary_category": ben_prof.beneficiary_category,
        }
        if hasattr(req, "user_driver_inputs") and req.user_driver_inputs:
            user_inputs.update(req.user_driver_inputs)
        if isinstance(request, dict):
            extra_drivers = request.get("user_driver_inputs") or request.get("driver_inputs") or {}
            user_inputs.update(extra_drivers)
            if request.get("business_constitution"):
                user_inputs["business_constitution"] = request.get("business_constitution")

        scheme_rules = SCHEME_RULES.get(scheme_result.recommended_scheme.value, SCHEME_RULES["TERM_LOAN_SCHEME"])
        scheme_margin_ratio = float(scheme_rules.get("margin_ratio", 0.10))

        scheme_data = {
            "scheme_id": scheme_result.recommended_scheme.value,
            "recommended_scheme": scheme_result.recommended_scheme.value,
            "scheme_name": financial_fit.scheme_name,
            "annual_interest_rate": financial_fit.annual_interest_rate,
            "interest_rate": financial_fit.annual_interest_rate,
            "tenure_months": financial_fit.tenure_months,
            "moratorium_months": financial_fit.moratorium_months,
            "maximum_loan": project_financing.estimated_financeable_loan,
            "maximum_financeable_project_cost": project_financing.maximum_financeable_project_cost,
            "margin_ratio": scheme_margin_ratio,
        }

        market_data = (
            getattr(req, "market_data", None)
            or (request.get("market_data") if isinstance(request, dict) else None)
            or {}
        )
        user_lang = (
            getattr(req, "language", None)
            or (request.get("language") if isinstance(request, dict) else None)
            or "en"
        )

        # -------------------------------------------------------------------------
        # 2e. Financial Intelligence Foundation (M1) & Project Cost Engine (M2)
        # Runs BEFORE capital allocation, profitability, cash flow, and viability.
        # -------------------------------------------------------------------------
        foundation_enrichment = self.legacy_adapter.enrich_financial_analysis(
            existing_response_dict={"financial_analysis": {}},
            business_profile=biz_prof.model_dump() if hasattr(biz_prof, "model_dump") else (biz_prof if isinstance(biz_prof, dict) else {}),
            user_inputs=user_inputs,
            benchmark_data_dict=benchmark_data.model_dump() if hasattr(benchmark_data, "model_dump") else (benchmark_data if isinstance(benchmark_data, dict) else {}),
            market_data=market_data,
            scheme_data=scheme_data,
            analysis_id=analysis_id,
            project_cost_basis=cost_basis,
            language=user_lang,
        )
        fa_enriched = foundation_enrichment.get("financial_analysis", {})
        pc_analysis_dict = fa_enriched.get("project_cost_analysis") or {}
        wc_analysis_dict = fa_enriched.get("working_capital_analysis") or {}

        # -------------------------------------------------------------------------
        # 3. Capital Allocation Engine (Consumes M2 Normalized Project Cost, CapEx & Working Capital)
        # -------------------------------------------------------------------------
        m2_total_cost = pc_analysis_dict.get("total_project_cost")
        if (
            m2_total_cost is not None
            and float(m2_total_cost) > 0
            and pc_analysis_dict.get("status") in ("RESOLVED", "PARTIALLY_DERIVED")
        ):
            normalized_project_cost = round(float(m2_total_cost), 2)
            # Reconcile loan requirement for this normalized economic project cost
            normalized_margin = round(min(fin_prof.available_margin_capital, normalized_project_cost * scheme_margin_ratio), 2)
            theoretical_loan = round(max(0.0, normalized_project_cost - normalized_margin), 2)
            scheme_max_loan = project_financing.scheme_maximum_loan
            effective_loan = min(theoretical_loan, scheme_max_loan)
            excess_margin = max(0.0, round(fin_prof.available_margin_capital - normalized_margin, 2))
            effective_project_financing = project_financing.model_copy(update={
                "total_project_cost": normalized_project_cost,
                "required_margin": normalized_margin,
                "theoretical_loan_requirement": theoretical_loan,
                "estimated_financeable_loan": effective_loan,
                "maximum_financeable_project_cost": normalized_project_cost,
                "excess_margin": excess_margin,
            })
        else:
            normalized_project_cost = effective_project_cost
            effective_loan = project_financing.estimated_financeable_loan
            effective_project_financing = project_financing.model_copy(update={
                "total_project_cost": normalized_project_cost,
            })

        effective_capex_override = proj_assumptions.capex_override
        effective_wc_override = proj_assumptions.working_capital_override

        # Feed M2 normalized values if user did not specify explicit overrides
        if effective_capex_override is None and pc_analysis_dict.get("capex") is not None:
            effective_capex_override = float(pc_analysis_dict["capex"])

        if effective_wc_override is None:
            m2_op_inv = pc_analysis_dict.get("opening_inventory")
            m2_wc_buf = pc_analysis_dict.get("working_capital")
            if m2_op_inv is not None or m2_wc_buf is not None:
                m2_total_wc = (float(m2_op_inv) if m2_op_inv is not None else 0.0) + (float(m2_wc_buf) if m2_wc_buf is not None else 0.0)
                if m2_total_wc > 0:
                    effective_wc_override = m2_total_wc

        capital_structure = self.cap_alloc_engine.allocate_capital(
            total_project_cost=normalized_project_cost,
            project_financing=effective_project_financing,
            benchmark_data=benchmark_data,
            capex_override=effective_capex_override,
            working_capital_override=effective_wc_override
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
        # 6. Profitability Projection Engine (Consumes M2 Derived Revenue)
        # -------------------------------------------------------------------------
        effective_proj_assumptions = proj_assumptions
        if effective_proj_assumptions.expected_monthly_revenue is None or effective_proj_assumptions.expected_monthly_revenue <= 0:
            derived_rev = None
            for asm in fa_enriched.get("assumptions", []):
                if asm.get("driver_id") == "monthly_revenue" and asm.get("value") is not None and float(asm["value"]) > 0:
                    derived_rev = float(asm["value"])
                    break
            if derived_rev is not None:
                effective_proj_assumptions = proj_assumptions.model_copy(update={"expected_monthly_revenue": derived_rev})

        profitability = self.profit_engine.calculate_profitability(
            project_assumptions=effective_proj_assumptions,
            loan_management=loan_management,
            benchmark_data=benchmark_data,
            user_inputs=user_inputs,
        )

        # -------------------------------------------------------------------------
        # 7. Cash Flow Projection Engine
        # -------------------------------------------------------------------------
        cash_flow = self.cf_engine.project_cash_flows(
            project_financing=effective_project_financing,
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
            project_financing=effective_project_financing,
            capital_structure=capital_structure,
            loan_management=loan_management,
            profitability=profitability,
            break_even=break_even,
            debt_service=debt_service
        )

        # -------------------------------------------------------------------------
        # 9b. Financial Projection & Statement Engine (Milestone 3)
        # -------------------------------------------------------------------------
        m2_pc = None
        raw_pc = fa_enriched.get("project_cost_analysis")
        if raw_pc is not None:
            if isinstance(raw_pc, ProjectCostAnalysis):
                m2_pc = raw_pc
            elif isinstance(raw_pc, dict):
                try:
                    m2_pc = ProjectCostAnalysis(**raw_pc)
                except Exception:
                    m2_pc = None

        m2_wc = None
        raw_wc = fa_enriched.get("working_capital_analysis")
        if raw_wc is not None:
            if isinstance(raw_wc, WorkingCapitalAnalysis):
                m2_wc = raw_wc
            elif isinstance(raw_wc, dict):
                try:
                    m2_wc = WorkingCapitalAnalysis(**raw_wc)
                except Exception:
                    m2_wc = None

        raw_asms = fa_enriched.get("assumptions", [])
        asms_map = {a.get("driver_id"): a for a in raw_asms if isinstance(a, dict)}

        fin_proj = self.projection_engine.project(
            projection_years=5,
            project_cost_analysis=m2_pc,
            working_capital_analysis=m2_wc,
            capital_structure=capital_structure,
            project_financing=effective_project_financing,
            loan_management=loan_management,
            repayment_schedule=repayment_schedule,
            profitability=profitability,
            project_assumptions=effective_proj_assumptions,
            benchmark_data=benchmark_data,
            user_inputs=user_inputs,
            assumptions_map=asms_map,
            business_profile=biz_prof,
            market_data=market_data,
        )

        # -------------------------------------------------------------------------
        # 9c. Banking Appraisal & Viability Engine (Milestone 4)
        # -------------------------------------------------------------------------
        banking_appraisal = self.appraisal_engine.appraise(
            financial_projection=fin_proj,
            project_cost_analysis=m2_pc,
            working_capital_analysis=m2_wc,
            capital_structure=capital_structure,
            project_financing=effective_project_financing,
            loan_management=loan_management,
            repayment_schedule=repayment_schedule,
            stage9_profitability=profitability,
            stage9_cash_flow=cash_flow,
            stage9_break_even=break_even,
            stage9_debt_service=debt_service,
            stage9_viability=viability,
            user_inputs=user_inputs,
            discount_rate=float(user_inputs["discount_rate"]) if ("discount_rate" in user_inputs and user_inputs["discount_rate"] is not None) else None,
            scheme_margin_ratio=scheme_margin_ratio,
            fixed_cost_ratio=float(user_inputs["fixed_cost_ratio"]) if ("fixed_cost_ratio" in user_inputs and user_inputs["fixed_cost_ratio"] is not None) else None,
            benchmark_data=benchmark_data,
            projection_years=5,
        )

        # -------------------------------------------------------------------------
        # 9d. Stress Testing, Scheme Routing & Financing Optimizer (Milestone 5)
        # -------------------------------------------------------------------------
        financing_optimizer_res = self.m5_engine.optimize(
            financial_projection=fin_proj,
            banking_appraisal=banking_appraisal,
            project_cost_analysis=m2_pc,
            working_capital_analysis=m2_wc,
            project_financing=effective_project_financing,
            loan_management=loan_management,
            repayment_schedule=repayment_schedule,
            scheme_result=scheme_result,
            financial_fit=financial_fit,
            user_inputs=user_inputs,
            benchmark_data=benchmark_data
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

        if capital_structure.source == "USER_INPUT":
            split_source = "user-provided allocation"
        elif "BENCHMARK" in capital_structure.source:
            split_source = "benchmark-derived industry data"
        elif "VERIFIED" in capital_structure.source:
            split_source = "evidence-derived parameters"
        elif "CALCULATED" in capital_structure.source or "DERIVED" in capital_structure.source:
            split_source = "deterministically derived project cost model"
        else:
            split_source = "unresolved baseline allocation"

        margin_pct = (scheme_margin_ratio * 100.0) if scheme_margin_ratio is not None else 10.0
        max_debt_pct = round(100.0 - margin_pct, 1)
        tot_cost = getattr(capital_structure, "total_project_cost", getattr(effective_project_financing, "theoretical_project_cost", 0.0))
        if tot_cost > 0:
            act_margin = getattr(effective_project_financing, "available_margin", getattr(effective_project_financing, "required_margin", 0.0))
            act_loan = getattr(effective_project_financing, "estimated_financeable_loan", getattr(loan_management, "principal", 0.0))
            act_margin_pct = round((act_margin / tot_cost) * 100.0, 1)
            act_debt_pct = round((act_loan / tot_cost) * 100.0, 1)
            margin_text = f"Promoter Margin Requirement: {margin_pct:.1f}% required by scheme rules ({act_margin_pct:.1f}% effective contribution)."
            debt_text = f"Debt Financing: {act_debt_pct:.1f}% of total project cost (capped by scheme rules at {max_debt_pct:.1f}%)."
        else:
            margin_text = f"Promoter Margin Requirement: {margin_pct:.1f}% of total project cost based on scheme rules."
            debt_text = f"Debt Financing: {max_debt_pct:.1f}% (capped by scheme rules)."

        assumptions_list = [
            f"Scheme: {financial_fit.scheme_name} ({financial_fit.annual_interest_rate*100:.1f}% p.a., {financial_fit.tenure_months} mo tenure, {financial_fit.moratorium_months} mo moratorium).",
            f"Beneficiary Eligibility Status: {beneficiary_eligibility.status.value} ({beneficiary_eligibility.advisory_notice}).",
            margin_text,
            debt_text,
            "Moratorium Interest Mode: Interest-Only monthly servicing during moratorium period.",
            f"CapEx / Working Capital Split: {capital_structure.capex_percentage:.0f}% / {capital_structure.working_capital_percentage:.0f}% based on {split_source}.",
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
            project_financing=effective_project_financing,
            capital_structure=capital_structure,
            loan_management=loan_management,
            repayment=repayment_schedule,
            profitability=profitability,
            cash_flow=cash_flow,
            break_even=break_even,
            debt_service=debt_service,
            financial_viability=viability,
            project_cost_basis=fa_enriched.get("project_cost_basis", cost_basis),
            financial_archetype=fa_enriched.get("financial_archetype"),
            assumption_status=fa_enriched.get("assumption_status", "PARTIAL"),
            assumptions=fa_enriched.get("assumptions", []),
            required_user_inputs=fa_enriched.get("required_user_inputs", []),
            assumption_confidence=fa_enriched.get("assumption_confidence"),
            provenance=fa_enriched.get("provenance", []),
            model_version=fa_enriched.get("model_version", "finance-foundation-v1"),
            project_cost_analysis=fa_enriched.get("project_cost_analysis"),
            working_capital_analysis=fa_enriched.get("working_capital_analysis"),
            financial_projection=fin_proj,
            profit_loss_statement=fin_proj.profit_loss_statement,
            cash_flow_statement=fin_proj.cash_flow_statement,
            balance_sheet=fin_proj.balance_sheet,
            working_capital_projection=fin_proj.working_capital_projection,
            financial_ratios=fin_proj.financial_ratios,
            funding_sources_uses=fin_proj.funding_sources_uses,
            projection_validation=fin_proj.validation,
            projection_provenance=fin_proj.provenance,
            projection_scenarios=fin_proj.scenarios,
            banking_appraisal=banking_appraisal,
            financing_optimizer=financing_optimizer_res,
        )

        # -------------------------------------------------------------------------
        # 10b. Bankable DPR Financial Packager (Milestone 6)
        # -------------------------------------------------------------------------
        try:
            dpr_pkg = self.dpr_packager.package(
                analysis_response_or_container=container,
                business_profile=biz_prof.model_dump() if hasattr(biz_prof, "model_dump") else (biz_prof if isinstance(biz_prof, dict) else {}),
                beneficiary_profile=ben_prof.model_dump() if hasattr(ben_prof, "model_dump") else (ben_prof if isinstance(ben_prof, dict) else {}),
                location_profile=loc_prof.model_dump() if hasattr(loc_prof, "model_dump") else (loc_prof if isinstance(loc_prof, dict) else {}),
                user_inputs=user_inputs,
                package_id=f"dpr_pkg_{analysis_id}"
            )
            container.dpr_financial_package = dpr_pkg
        except Exception as e:
            logger.warning(f"[FINANCIAL ENGINE] DPR packager encountered non-fatal error: {e}", exc_info=True)
            container.dpr_financial_package = {
                "status": "ERROR",
                "error": str(e),
                "is_dpr_eligible": False,
                "draft_only": True
            }

        # -------------------------------------------------------------------------
        # 10c. Canonical Downstream Financial Context (financial_context)
        # -------------------------------------------------------------------------
        try:
            from app.services.financial_engine.financial_context import build_financial_context
            fin_ctx = build_financial_context(
                dpr_package=container.dpr_financial_package,
                container=container,
                business_profile=biz_prof.model_dump() if hasattr(biz_prof, "model_dump") else (biz_prof if isinstance(biz_prof, dict) else {}),
                beneficiary_profile=ben_prof.model_dump() if hasattr(ben_prof, "model_dump") else (ben_prof if isinstance(ben_prof, dict) else {}),
                location_profile=loc_prof.model_dump() if hasattr(loc_prof, "model_dump") else (loc_prof if isinstance(loc_prof, dict) else {}),
                user_inputs=user_inputs
            )
            container.financial_context = fin_ctx
        except Exception as e:
            logger.warning(f"[FINANCIAL ENGINE] Failed to build canonical financial_context: {e}", exc_info=True)

        return FinancialAnalysisResponse(
            schema_version="1.0",
            analysis_id=analysis_id,
            session_id=session_id,
            workflow=Stage9WorkflowState(stage=9, state="FINANCIAL_VIABILITY_EVALUATED", status="complete"),
            financial_analysis=container,
            audit=audit_meta,
            financial_context=container.financial_context
        )

    def get_dpr_package(
        self,
        analysis_response_or_container: Any,
        business_profile: Optional[Dict[str, Any]] = None,
        beneficiary_profile: Optional[Dict[str, Any]] = None,
        location_profile: Optional[Dict[str, Any]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        package_id: Optional[str] = None,
    ) -> DPRFinancialPackage:
        """
        Direct accessor to pack authoritative M1–M5 outputs into canonical DPR financial package.
        """
        return self.dpr_packager.package(
            analysis_response_or_container=analysis_response_or_container,
            business_profile=business_profile,
            beneficiary_profile=beneficiary_profile,
            location_profile=location_profile,
            user_inputs=user_inputs,
            package_id=package_id,
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
            "alternative_financing_router": True,
            "financial_intelligence_foundation": True,
            "financial_archetype_registry": True,
            "deterministic_calculation_registry": True
        }


# Global singleton instance
financial_engine = FinancialEngine()
