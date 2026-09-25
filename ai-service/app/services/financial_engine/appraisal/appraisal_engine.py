"""
Master Banking Appraisal & Viability Engine for KALPA (Milestone 4).
Orchestrates institutional-grade deterministic evaluations of debt service,
repayment capacity, DSCR, break-even, liquidity, profitability, leverage,
banking ratios, promoter contribution, financing structure, tri-state validation,
risk flags, executive summary, and viability assessment.
100% deterministic Python mathematics. Zero LLM reliance.
"""
from typing import Dict, Any, List, Optional
import datetime

from app.services.financial_engine.appraisal.appraisal_schema import (
    BankingAppraisalResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.services.financial_engine.appraisal.debt_service import debt_service_engine
from app.services.financial_engine.appraisal.repayment_capacity import repayment_capacity_engine
from app.services.financial_engine.appraisal.dscr_analysis import dscr_analysis_engine
from app.services.financial_engine.appraisal.break_even_analysis import break_even_analysis_engine
from app.services.financial_engine.appraisal.liquidity_analysis import liquidity_analysis_engine
from app.services.financial_engine.appraisal.profitability_analysis import profitability_analysis_engine
from app.services.financial_engine.appraisal.leverage_analysis import leverage_analysis_engine
from app.services.financial_engine.appraisal.banking_ratios import banking_ratios_engine
from app.services.financial_engine.appraisal.promoter_contribution import promoter_contribution_engine
from app.services.financial_engine.appraisal.financing_structure import financing_structure_engine
from app.services.financial_engine.appraisal.risk_engine import risk_engine
from app.services.financial_engine.appraisal.viability_engine import viability_engine
from app.services.financial_engine.appraisal.appraisal_summary import appraisal_summary_builder
from app.services.financial_engine.appraisal.validation import appraisal_validation_engine

from app.schemas.financial_analysis import (
    FinancialProjection,
    ProjectCostAnalysis,
    WorkingCapitalAnalysis,
    CapitalStructure,
    ProjectFinancing,
    LoanManagement,
    RepaymentSchedule,
    ProfitabilityProjection,
    CashFlowAnalysis,
    BreakEvenAnalysis,
    DebtServiceAnalysis,
    FinancialViabilityResult,
    FundingSourcesUses
)


class AppraisalEngine:
    """
    Master coordinator for Milestone 4 Banking Appraisal & Viability Engine.
    """

    def appraise(
        self,
        financial_projection: Optional[FinancialProjection] = None,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        working_capital_analysis: Optional[WorkingCapitalAnalysis] = None,
        capital_structure: Optional[CapitalStructure] = None,
        project_financing: Optional[ProjectFinancing] = None,
        loan_management: Optional[LoanManagement] = None,
        repayment_schedule: Optional[RepaymentSchedule] = None,
        stage9_profitability: Optional[ProfitabilityProjection] = None,
        stage9_cash_flow: Optional[CashFlowAnalysis] = None,
        stage9_break_even: Optional[BreakEvenAnalysis] = None,
        stage9_debt_service: Optional[DebtServiceAnalysis] = None,
        stage9_viability: Optional[FinancialViabilityResult] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        discount_rate: Optional[float] = None,
        scheme_margin_ratio: Optional[float] = None,
        fixed_cost_ratio: Optional[float] = None,
        benchmark_data: Optional[Any] = None,
        projection_years: int = 5,
    ) -> BankingAppraisalResult:
        prov = ProvenanceBuilder()
        user_in = user_inputs or {}

        # 1. Unpack M3 Statements if available
        pl_stmt = getattr(financial_projection, "profit_loss_statement", None) if financial_projection else None
        bs_stmt = getattr(financial_projection, "balance_sheet", None) if financial_projection else None
        cf_stmt = getattr(financial_projection, "cash_flow_statement", None) if financial_projection else None
        wc_proj = getattr(financial_projection, "working_capital_projection", None) if financial_projection else None
        sources_uses = getattr(financial_projection, "funding_sources_uses", None) if financial_projection else None
        rev_proj = getattr(financial_projection, "revenue_projection", None) if financial_projection else None
        cost_proj = getattr(financial_projection, "cost_projection", None) if financial_projection else None

        # 2. Identify Critical Unknowns
        critical_unknowns: List[str] = []
        if not rev_proj or rev_proj.status == "INSUFFICIENT_DATA" or not rev_proj.years or rev_proj.years[0].revenue is None:
            critical_unknowns.append("revenue")
        if not cost_proj or cost_proj.status == "INSUFFICIENT_DATA" or not cost_proj.years or cost_proj.years[0].total_operating_expenses is None:
            critical_unknowns.append("operating_expenses")
        if loan_management and loan_management.principal > 0 and (not repayment_schedule or not repayment_schedule.monthly_schedule):
            critical_unknowns.append("debt_service_schedule")
        if not project_cost_analysis and not capital_structure and not sources_uses:
            critical_unknowns.append("project_cost")

        # 3. Sub-Engine: Debt Service
        ds_result = debt_service_engine.evaluate(
            projection_years=projection_years,
            loan_management=loan_management,
            repayment_schedule=repayment_schedule,
            profit_loss=pl_stmt,
            balance_sheet=bs_stmt,
            revenue_projection=rev_proj,
            provenance=prov
        )

        # 4. Sub-Engine: Repayment Capacity
        rc_result = repayment_capacity_engine.evaluate(
            debt_service=ds_result,
            profit_loss=pl_stmt,
            cash_flow=cf_stmt,
            provenance=prov
        )

        # 5. Sub-Engine: DSCR & ADSCR
        dscr_result = dscr_analysis_engine.evaluate(
            repayment_capacity=rc_result,
            debt_service=ds_result,
            stage9_debt_service=stage9_debt_service,
            provenance=prov
        )

        # 6. Sub-Engine: Break-Even (Explicit cost split only; never invents ratio)
        # Resolution order: explicit argument/user input -> benchmark_data.fixed_cost_ratio
        fc_ratio = fixed_cost_ratio
        if fc_ratio is None and "fixed_cost_ratio" in user_in and user_in["fixed_cost_ratio"] is not None:
            fc_ratio = float(user_in["fixed_cost_ratio"])
        elif fc_ratio is None and benchmark_data is not None:
            if isinstance(benchmark_data, dict):
                fc_val = benchmark_data.get("fixed_cost_ratio")
                if fc_val is not None:
                    fc_ratio = float(fc_val)
            elif getattr(benchmark_data, "fixed_cost_ratio", None) is not None:
                fc_ratio = float(benchmark_data.fixed_cost_ratio)

        be_result = break_even_analysis_engine.evaluate(
            profit_loss=pl_stmt,
            cost_projection=cost_proj,
            stage9_break_even=stage9_break_even,
            fixed_cost_ratio=fc_ratio,
            provenance=prov
        )

        # 7. Sub-Engine: Liquidity
        liq_result = liquidity_analysis_engine.evaluate(
            balance_sheet=bs_stmt,
            working_capital_proj=wc_proj,
            cash_flow=cf_stmt,
            profit_loss=pl_stmt,
            debt_service=ds_result,
            provenance=prov
        )

        # 8. Sub-Engine: Profitability
        prof_result = profitability_analysis_engine.evaluate(
            profit_loss=pl_stmt,
            balance_sheet=bs_stmt,
            provenance=prov
        )

        # 9. Sub-Engine: Leverage & Capital Structure
        lev_result = leverage_analysis_engine.evaluate(
            balance_sheet=bs_stmt,
            sources_uses=sources_uses,
            provenance=prov
        )

        # 10. Sub-Engine: Banking Ratios & Return Metrics
        # Look for explicit discount rate in user_in if not provided as argument
        explicit_discount = discount_rate
        if explicit_discount is None and "discount_rate" in user_in:
            try:
                explicit_discount = float(user_in["discount_rate"])
            except (ValueError, TypeError):
                explicit_discount = None

        br_result = banking_ratios_engine.evaluate(
            profit_loss=pl_stmt,
            cash_flow=cf_stmt,
            sources_uses=sources_uses,
            project_cost_analysis=project_cost_analysis,
            discount_rate=explicit_discount,
            provenance=prov
        )

        # 11. Sub-Engine: Promoter Contribution
        prom_result = promoter_contribution_engine.evaluate(
            project_financing=project_financing,
            capital_structure=capital_structure,
            sources_uses=sources_uses,
            project_cost_analysis=project_cost_analysis,
            scheme_margin_ratio=scheme_margin_ratio,
            provenance=prov
        )

        # 12. Sub-Engine: Financing Structure
        fin_result = financing_structure_engine.evaluate(
            sources_uses=sources_uses,
            project_cost_analysis=project_cost_analysis,
            capital_structure=capital_structure,
            project_financing=project_financing,
            provenance=prov
        )

        # 13. Sub-Engine: Tri-State Validation
        val_result = appraisal_validation_engine.validate(
            project_cost_analysis=project_cost_analysis,
            sources_uses=sources_uses,
            loan_management=loan_management,
            stage9_debt_service=stage9_debt_service,
            stage9_break_even=stage9_break_even,
            debt_service=ds_result,
            dscr=dscr_result,
            break_even=be_result,
            promoter_contribution=prom_result,
            financing=fin_result,
            banking_ratios=br_result,
            profitability=prof_result,
            liquidity=liq_result,
            leverage=lev_result,
            critical_unknowns=critical_unknowns
        )

        # 14. Sub-Engine: Risk Engine
        risk_res = risk_engine.evaluate(
            debt_service=ds_result,
            repayment_capacity=rc_result,
            dscr=dscr_result,
            break_even=be_result,
            liquidity=liq_result,
            profitability=prof_result,
            leverage=lev_result,
            promoter_contribution=prom_result,
            financing=fin_result,
            validation=val_result,
            critical_unknowns=critical_unknowns
        )

        # 15. Sub-Engine: Viability Assessment
        viab_res = viability_engine.evaluate(
            risk_result=risk_res,
            debt_service=ds_result,
            repayment_capacity=rc_result,
            dscr=dscr_result,
            break_even=be_result,
            liquidity=liq_result,
            profitability=prof_result,
            leverage=lev_result,
            promoter_contribution=prom_result,
            financing=fin_result,
            critical_unknowns=critical_unknowns
        )

        # 16. Sub-Engine: Executive Appraisal Summary
        summary = appraisal_summary_builder.build(
            debt_service=ds_result,
            repayment_capacity=rc_result,
            dscr=dscr_result,
            break_even=be_result,
            liquidity=liq_result,
            profitability=prof_result,
            leverage=lev_result,
            banking_ratios=br_result,
            promoter_contribution=prom_result,
            financing=fin_result,
            risk_result=risk_res,
            viability=viab_res,
            validation=val_result,
            critical_unknowns=critical_unknowns
        )

        # 17. Overall Status Determination
        if critical_unknowns or not val_result.all_passed:
            if val_result.failed_checks > 0:
                overall_status = AppraisalStatus.UNRESOLVED
            elif val_result.unresolved_checks > 0 or critical_unknowns:
                overall_status = AppraisalStatus.PARTIALLY_DERIVED
            else:
                overall_status = AppraisalStatus.RESOLVED
        else:
            overall_status = AppraisalStatus.RESOLVED

        # Consolidated machine-readable reason codes
        active_codes: List[ReasonCode] = []
        for f in risk_res.flags:
            if f.reason_code not in active_codes:
                active_codes.append(f.reason_code)
        for rc in viab_res.reason_codes:
            if rc not in active_codes:
                active_codes.append(rc)

        # Summary Assumptions
        assumptions = [
            "Appraisal calculations executed deterministically without large language model arithmetic.",
            f"Stage 9 authoritative loan principal: ₹{loan_management.principal:,.2f}" if loan_management else "Zero loan financing.",
            f"Underwriting horizon evaluated across {projection_years} financial operating years.",
            "All accounting invariants validated under tri-state validation gates."
        ]

        metrics_map: Dict[str, Any] = {
            "total_project_cost": summary.project_cost,
            "term_loan": summary.debt_exposure,
            "promoter_contribution": summary.promoter_contribution,
            "promoter_contribution_pct": summary.promoter_contribution_pct,
            "average_dscr": summary.average_dscr,
            "minimum_dscr": summary.minimum_dscr,
            "icr_year1": summary.icr_year1,
            "year1_break_even_utilization_pct": summary.break_even_utilization_pct_year1,
            "average_current_ratio": liq_result.average_current_ratio,
            "initial_der": summary.initial_der,
            "irr": summary.irr,
            "npv": summary.npv,
            "payback_period_years": summary.payback_period_years,
            "viability_classification": viab_res.classification.value,
        }

        return BankingAppraisalResult(
            status=overall_status,
            metrics=metrics_map,
            appraisal=summary,
            viability=viab_res,
            risk_flags=risk_res,
            financing=fin_result,
            promoter_contribution=prom_result,
            debt_service=ds_result,
            repayment_capacity=rc_result,
            dscr=dscr_result,
            break_even=be_result,
            liquidity=liq_result,
            profitability=prof_result,
            leverage=lev_result,
            banking_ratios=br_result,
            validation=val_result,
            critical_unknowns=critical_unknowns,
            assumptions=assumptions,
            provenance=prov.get_records(),
            reason_codes=active_codes
        )


appraisal_engine = AppraisalEngine()
