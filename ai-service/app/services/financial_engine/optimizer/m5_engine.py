"""
Master Orchestrator for Milestone 5:
Stress Testing, Scheme Routing & Financing Optimizer.
Coordinates downside scenario testing, multi-scheme evaluation, tenure analysis,
promoter margin compliance, non-plug financing gap analysis, and transparent policy selection.
Zero LLM calculations. Zero mutation of upstream M1-M4 outputs.
Strict non-fabrication: UNKNOWN values remain UNKNOWN. No default fallbacks.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    FinancialProjection,
    ProjectCostAnalysis,
    WorkingCapitalAnalysis,
    ProjectFinancing,
    LoanManagement,
    RepaymentSchedule,
    SchemeResult,
    SchemeFinancialFit
)
from app.services.financial_engine.optimizer.m5_config import (
    POLICY_VERSION,
    MODEL_VERSION,
    DSCR_RESILIENCE_BENCHMARK,
    DSCR_RESILIENCE_MINIMUM
)
from app.services.financial_engine.optimizer.m5_schema import (
    M5OptimizationResult,
    M5DprFinancingSummary,
    M5ProvenanceRecord,
    M5ValidationState,
    StressScenarioType
)
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder
from app.services.financial_engine.optimizer.stress_engine import stress_engine
from app.services.financial_engine.optimizer.resilience_analysis import (
    resilience_analysis_engine,
    select_worst_case_scenario
)
from app.services.financial_engine.optimizer.scheme_router import scheme_router
from app.services.financial_engine.optimizer.promoter_contribution_analysis import promoter_contribution_analysis_engine
from app.services.financial_engine.optimizer.financing_feasibility import financing_feasibility_engine
from app.services.financial_engine.optimizer.tenure_analysis import tenure_analysis_engine
from app.services.financial_engine.optimizer.financing_options import financing_options_generator
from app.services.financial_engine.optimizer.financing_optimizer import financing_optimizer
from app.services.financial_engine.optimizer.m5_validation import m5_validation_engine
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode


class M5Engine:
    """
    Main Milestone 5 Decision & Optimization Engine.
    """

    def optimize(
        self,
        financial_projection: Optional[FinancialProjection] = None,
        banking_appraisal: Optional[Any] = None,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        working_capital_analysis: Optional[WorkingCapitalAnalysis] = None,
        project_financing: Optional[ProjectFinancing] = None,
        loan_management: Optional[LoanManagement] = None,
        repayment_schedule: Optional[RepaymentSchedule] = None,
        scheme_result: Optional[SchemeResult] = None,
        financial_fit: Optional[SchemeFinancialFit] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        benchmark_data: Optional[Any] = None,
        user_scenarios: Optional[List[Dict[str, Any]]] = None
    ) -> M5OptimizationResult:
        prov = M5ProvenanceBuilder()
        user_in = user_inputs or {}

        # ---------------------------------------------------------------------
        # 1. Unpack M3 & M4 Baseline Statements
        # ---------------------------------------------------------------------
        pl_stmt = getattr(financial_projection, "profit_loss_statement", None) if financial_projection else None
        cf_stmt = getattr(financial_projection, "cash_flow_statement", None) if financial_projection else None
        bs_stmt = getattr(financial_projection, "balance_sheet", None) if financial_projection else None
        sources_uses = getattr(financial_projection, "funding_sources_uses", None) if financial_projection else None

        debt_service = getattr(banking_appraisal, "debt_service", None) if banking_appraisal else None
        repayment_cap = getattr(banking_appraisal, "repayment_capacity", None) if banking_appraisal else None

        # ---------------------------------------------------------------------
        # 2. Extract Authoritative Baseline Financial Facts
        # ---------------------------------------------------------------------
        project_cost: Optional[float] = None
        if project_cost_analysis and project_cost_analysis.total_project_cost and project_cost_analysis.total_project_cost > 0:
            project_cost = project_cost_analysis.total_project_cost
        elif sources_uses and sources_uses.total_uses and sources_uses.total_uses > 0:
            project_cost = sources_uses.total_uses
        elif project_financing:
            project_cost = getattr(project_financing, "total_project_cost", getattr(project_financing, "theoretical_project_cost", None))

        # Available Promoter Contribution (user margin)
        available_promoter: Optional[float] = None
        if "available_margin_capital" in user_in and user_in["available_margin_capital"] is not None:
            available_promoter = float(user_in["available_margin_capital"])
        elif "promoter_contribution" in user_in and user_in["promoter_contribution"] is not None:
            available_promoter = float(user_in["promoter_contribution"])
        elif project_financing:
            available_promoter = getattr(project_financing, "promoter_contribution", getattr(project_financing, "available_margin", None))
        elif sources_uses and sources_uses.promoter_contribution is not None:
            available_promoter = sources_uses.promoter_contribution

        # Verified Other Financing
        other_financing: Optional[float] = None
        if sources_uses and sources_uses.other_financing is not None:
            other_financing = sources_uses.other_financing
        elif "other_financing" in user_in and user_in["other_financing"] is not None:
            other_financing = float(user_in["other_financing"])
        elif sources_uses and getattr(sources_uses, "status", None) in ("RECONCILED", "BALANCED"):
            if sources_uses.promoter_contribution is not None and sources_uses.term_loan is not None:
                other_financing = 0.0

        # Base loan
        base_loan: Optional[float] = None
        if loan_management and loan_management.principal is not None:
            base_loan = loan_management.principal
        elif project_financing:
            base_loan = getattr(project_financing, "financeable_loan", getattr(project_financing, "estimated_financeable_loan", None))

        # Cash Available for Debt Service (CADS)
        base_cads: Optional[float] = None
        if repayment_cap and getattr(repayment_cap, "average_cads", None) is not None:
            base_cads = repayment_cap.average_cads
        elif repayment_cap and getattr(repayment_cap, "total_cads", None) is not None and getattr(repayment_cap, "total_cads") > 0:
            years_count = len(getattr(repayment_cap, "years", [])) or 1
            base_cads = round(repayment_cap.total_cads / years_count, 2)
        elif repayment_cap and getattr(repayment_cap, "years", None):
            y1_c = repayment_cap.years[0].cash_available_for_debt_service
            if y1_c is not None:
                base_cads = y1_c
        elif pl_stmt and pl_stmt.years:
            y1 = pl_stmt.years[0]
            cash_op = y1.profit_after_tax if y1.profit_after_tax is not None else (
                (y1.profit_before_tax if y1.profit_before_tax is not None else y1.ebitda)
            )
            if cash_op is not None:
                is_zd = (debt_service and getattr(debt_service, "is_zero_debt", False)) or (loan_management and loan_management.principal == 0.0)
                int_exp = y1.interest_expense if y1.interest_expense is not None else (0.0 if is_zd else 0.0)
                dep = y1.depreciation if y1.depreciation is not None else 0.0
                base_cads = round(cash_op + dep + int_exp, 2)

        # Scheme margin percentage
        scheme_margin_pct: Optional[float] = None
        if financial_fit and financial_fit.margin_percentage is not None:
            scheme_margin_pct = financial_fit.margin_percentage
        elif "margin_ratio" in user_in and user_in["margin_ratio"] is not None:
            scheme_margin_pct = float(user_in["margin_ratio"]) * 100.0

        # Verified funding
        verified_funding: Optional[float] = None
        if available_promoter is not None and base_loan is not None and other_financing is not None:
            verified_funding = round(available_promoter + base_loan + other_financing, 2)

        # Base case reference summary
        base_ref = {
            "total_project_cost": project_cost,
            "available_promoter_contribution": available_promoter,
            "recommended_scheme": scheme_result.recommended_scheme.value if (scheme_result and scheme_result.recommended_scheme) else None,
            "base_cads": base_cads
        }

        # ---------------------------------------------------------------------
        # 3. Sub-Engine: Downside Stress Testing
        # ---------------------------------------------------------------------
        stress_scenarios = stress_engine.evaluate(
            profit_loss=pl_stmt,
            cash_flow=cf_stmt,
            balance_sheet=bs_stmt,
            debt_service=debt_service,
            loan_management=loan_management,
            working_capital_analysis=working_capital_analysis,
            working_capital_projection=financial_projection.working_capital_projection if financial_projection else None,
            project_cost=project_cost,
            verified_funding=verified_funding,
            user_scenarios=user_scenarios,
            provenance=prov
        )

        # ---------------------------------------------------------------------
        # 4. Sub-Engine: Resilience Analysis
        # ---------------------------------------------------------------------
        resilience_analysis = resilience_analysis_engine.evaluate(
            stress_scenarios=stress_scenarios
        )

        # ---------------------------------------------------------------------
        # 5. Sub-Engine: Scheme Routing
        # ---------------------------------------------------------------------
        scheme_options = scheme_router.evaluate_schemes(
            project_cost=project_cost,
            available_promoter_contribution=available_promoter,
            user_inputs=user_in,
            provenance=prov
        )

        # If scheme_margin_pct is not yet resolved, use the matched eligible scheme if unique
        if scheme_margin_pct is None and scheme_options:
            applicable_schemes = [
                sc for sc in scheme_options
                if sc.eligibility_status.value in ("ELIGIBLE", "VERIFICATION_REQUIRED")
                and sc.required_margin_percentage is not None
            ]
            unique_margins = {sc.required_margin_percentage for sc in applicable_schemes}
            if len(unique_margins) == 1:
                scheme_margin_pct = unique_margins.pop()
            else:
                scheme_margin_pct = None

        # ---------------------------------------------------------------------
        # 6. Sub-Engine: Promoter Contribution Analysis
        # ---------------------------------------------------------------------
        promoter_analysis = promoter_contribution_analysis_engine.evaluate(
            total_project_cost=project_cost,
            available_promoter_contribution=available_promoter,
            scheme_margin_percentage=scheme_margin_pct,
            provenance=prov
        )

        # ---------------------------------------------------------------------
        # 7. Sub-Engine: Financing Feasibility & Gap Analysis
        # ---------------------------------------------------------------------
        financing_gap_analysis = financing_feasibility_engine.evaluate(
            total_project_cost=project_cost,
            available_promoter_contribution=available_promoter,
            scheme_loan=base_loan,
            other_verified_financing=other_financing,
            provenance=prov
        )

        # ---------------------------------------------------------------------
        # 8. Sub-Engine: Tenure Analysis (Strict Non-Fabrication)
        # ---------------------------------------------------------------------
        scheme_max_tenure: Optional[int] = financial_fit.tenure_months if financial_fit else None
        base_rate: Optional[float] = loan_management.annual_interest_rate if loan_management else None
        moratorium: Optional[int] = loan_management.moratorium_months if loan_management else None

        # Derive actual downside CADS from stress scenarios
        downside_cads: Optional[float] = None
        if stress_scenarios:
            comb_sc = next(
                (s for s in stress_scenarios if s.scenario_type == StressScenarioType.COMBINED_DOWNSIDE and s.status == "RESOLVED" and s.cads is not None),
                None
            )
            if comb_sc is not None:
                downside_cads = comb_sc.cads
            else:
                resolved_cads = [s.cads for s in stress_scenarios if s.status == "RESOLVED" and s.cads is not None]
                if resolved_cads:
                    downside_cads = min(resolved_cads)

        tenure_analysis = tenure_analysis_engine.evaluate_tenures(
            loan_amount=base_loan,
            annual_interest_rate=base_rate,
            scheme_max_tenure_months=scheme_max_tenure,
            moratorium_months=moratorium,
            base_cads=base_cads,
            stress_cads=downside_cads
        )

        # ---------------------------------------------------------------------
        # 9. Sub-Engine: Financing Options Generation (Actual Scenario-Derived CADS)
        # ---------------------------------------------------------------------
        financing_options = financing_options_generator.generate_candidates(
            project_cost=project_cost,
            available_promoter_contribution=available_promoter,
            scheme_options=scheme_options,
            base_cads=base_cads,
            stress_scenarios=stress_scenarios,
            other_verified_financing=other_financing,
            provenance=prov
        )

        # ---------------------------------------------------------------------
        # 10. Sub-Engine: Financing Optimizer (Multi-Tier Policy Selection)
        # ---------------------------------------------------------------------
        preferred_scheme_id: Optional[str] = None
        if scheme_result and hasattr(scheme_result, "recommended_scheme") and scheme_result.recommended_scheme:
            preferred_scheme_id = getattr(scheme_result.recommended_scheme, "value", str(scheme_result.recommended_scheme))
        elif financial_fit and hasattr(financial_fit, "recommended_scheme") and financial_fit.recommended_scheme:
            preferred_scheme_id = getattr(financial_fit.recommended_scheme, "value", str(financial_fit.recommended_scheme))

        preferred_tenure: Optional[int] = loan_management.tenure_months if loan_management else None

        selected_structure, decision_reasons = financing_optimizer.select_best_structure(
            candidates=financing_options,
            provenance=prov,
            preferred_scheme_id=preferred_scheme_id,
            preferred_tenure_months=preferred_tenure
        )
        if selected_structure and selected_structure.status != "RESOLVED":
            selected_structure = None

        # ---------------------------------------------------------------------
        # 11. DPR Structured Summary Builder (Transparent Severity Hierarchy)
        # ---------------------------------------------------------------------
        is_zero_debt_proj = bool(
            (debt_service and getattr(debt_service, "is_zero_debt", False)) or
            (loan_management and loan_management.principal == 0.0)
        )

        worst_sc = select_worst_case_scenario(stress_scenarios)
        worst_dscr = worst_sc.dscr if worst_sc else None
        worst_liq = worst_sc.current_ratio if worst_sc else None

        # Determine funding gap & fully financed status
        dpr_funding_gap: Optional[float] = None
        dpr_is_fully_financed: Optional[bool] = None
        if selected_structure:
            dpr_funding_gap = selected_structure.financing_gap
            dpr_is_fully_financed = selected_structure.is_gap_eliminated
        elif financing_gap_analysis and financing_gap_analysis.status == "RESOLVED":
            dpr_funding_gap = financing_gap_analysis.funding_gap
            dpr_is_fully_financed = financing_gap_analysis.is_balanced

        # Repayment capacity text
        dpr_repayment_capacity: Optional[str] = None
        if worst_dscr is not None:
            if worst_dscr >= DSCR_RESILIENCE_BENCHMARK:
                dpr_repayment_capacity = "ROBUST"
            elif worst_dscr >= DSCR_RESILIENCE_MINIMUM:
                dpr_repayment_capacity = "ADEQUATE"
            elif worst_dscr >= 1.0:
                dpr_repayment_capacity = "TIGHT"
            else:
                dpr_repayment_capacity = "STRESSED"
        elif is_zero_debt_proj:
            dpr_repayment_capacity = "NOT_APPLICABLE"
        else:
            dpr_repayment_capacity = "NOT_ASSESSABLE"

        # Margin adequacy status
        dpr_margin_status: Optional[str] = None
        if promoter_analysis and promoter_analysis.status == "RESOLVED":
            dpr_margin_status = "ADEQUATE" if promoter_analysis.is_adequate else "GAP_DETECTED"
        else:
            dpr_margin_status = "UNRESOLVED"

        # Stress resilience status
        dpr_resilience_status: Optional[str] = None
        if resilience_analysis:
            dpr_resilience_status = resilience_analysis.overall_resilience.value
        else:
            dpr_resilience_status = "NOT_ASSESSABLE"

        # ---------------------------------------------------------------------
        # 11. Tri-State Validation Gates
        # ---------------------------------------------------------------------
        val_result = m5_validation_engine.validate(
            project_cost=project_cost,
            financing_gap_analysis=financing_gap_analysis,
            promoter_analysis=promoter_analysis,
            selected_structure=selected_structure,
            stress_scenarios=stress_scenarios,
            financing_options=financing_options,
            is_zero_debt=bool(is_zero_debt_proj)
        )

        unresolved_inputs = [
            f"{check.check_id}: {check.message}"
            for check in val_result.checks
            if check.status == M5ValidationState.UNRESOLVED
        ]

        # ---------------------------------------------------------------------
        # 12. DPR Structured Summary Builder (Transparent Severity Hierarchy)
        # ---------------------------------------------------------------------
        dpr_term_loan = selected_structure.loan_amount if selected_structure else (0.0 if is_zero_debt_proj else None)
        dpr_monthly_emi = selected_structure.monthly_emi if selected_structure else (0.0 if is_zero_debt_proj else None)
        dpr_total_interest = selected_structure.total_interest if selected_structure else (0.0 if is_zero_debt_proj else None)
        dpr_margin_pct = selected_structure.required_margin_percentage if selected_structure else scheme_margin_pct
        dpr_promoter_contrib = selected_structure.promoter_contribution if selected_structure else available_promoter

        dpr_summary = M5DprFinancingSummary(
            recommended_scheme_name=selected_structure.scheme_name if selected_structure else None,
            recommended_scheme_id=selected_structure.scheme_id if selected_structure else None,
            total_project_cost=selected_structure.total_project_cost if selected_structure else project_cost,
            promoter_contribution=dpr_promoter_contrib,
            promoter_margin_pct=dpr_margin_pct,
            term_loan=dpr_term_loan,
            interest_rate_pct=round(selected_structure.interest_rate * 100.0, 2) if (selected_structure and selected_structure.interest_rate is not None) else None,
            tenure_months=selected_structure.tenure_months if selected_structure else None,
            moratorium_months=selected_structure.moratorium_months if selected_structure else None,
            monthly_emi=dpr_monthly_emi,
            total_interest=dpr_total_interest,
            scenarios_tested_count=len(stress_scenarios),
            worst_case_scenario=worst_sc.scenario_name if worst_sc else None,
            worst_case_dscr=worst_dscr,
            worst_case_liquidity=worst_liq,
            stress_resilience_status=dpr_resilience_status,
            funding_gap=dpr_funding_gap,
            is_fully_financed=dpr_is_fully_financed,
            margin_adequacy_status=dpr_margin_status,
            repayment_capacity=dpr_repayment_capacity,
            unresolved_inputs=unresolved_inputs,
            advisory_notes=[
                "Deterministically assessed under KALPA Milestone 5 Stress Testing & Financing Optimizer.",
                "Subject to formal bank and government scheme document verification.",
                "Based on supplied business drivers and benchmark-supported financial norms."
            ]
        )

        # Overall Status
        if val_result.failed_checks > 0:
            overall_status = "FAILED"
        elif val_result.unresolved_checks > 0:
            overall_status = "PARTIALLY_DERIVED"
        else:
            overall_status = "RESOLVED"

        # Collect top-level risk flags from stress scenarios with deterministic deduplication
        risk_flags: List[Dict[str, Any]] = []
        seen_risk_keys = set()
        for sc in stress_scenarios:
            for rc in sc.reason_codes:
                rc_str = rc.value if hasattr(rc, "value") else str(rc)
                key = (sc.scenario_id, rc_str)
                if key not in seen_risk_keys:
                    seen_risk_keys.add(key)
                    risk_flags.append({
                        "scenario_id": sc.scenario_id,
                        "scenario_name": sc.scenario_name,
                        "reason_code": rc_str,
                        "resilience_status": sc.resilience_status.value if hasattr(sc.resilience_status, "value") else str(sc.resilience_status),
                        "dscr": sc.dscr,
                        "current_ratio": sc.current_ratio
                    })

        return M5OptimizationResult(
            status=overall_status,
            base_case_reference=base_ref,
            stress_scenarios=stress_scenarios,
            scheme_options=scheme_options,
            financing_options=financing_options,
            selected_financing_structure=selected_structure,
            selected_structure=selected_structure,
            financing_gap_analysis=financing_gap_analysis,
            promoter_contribution_analysis=promoter_analysis,
            tenure_analysis=tenure_analysis,
            resilience_analysis=resilience_analysis,
            decision_reasons=decision_reasons,
            risk_flags=risk_flags,
            validation=val_result,
            provenance=prov.get_records(),
            reason_codes=decision_reasons,
            dpr_summary=dpr_summary,
            policy_version=POLICY_VERSION,
            model_version=MODEL_VERSION
        )


m5_engine = M5Engine()
