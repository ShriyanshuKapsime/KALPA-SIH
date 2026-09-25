"""
Appraisal Summary Engine for M4 Banking Appraisal.
Compiles a structured, DPR-ready executive banking appraisal summary
directly consumable by downstream DPR generation pipelines.
"""
from typing import Optional, List, Dict, Any
from app.services.financial_engine.appraisal.appraisal_schema import (
    AppraisalSummary,
    DebtServiceAnalysisResult,
    RepaymentCapacityResult,
    DSCRAnalysisResult,
    BreakEvenAnalysisResult,
    LiquidityAnalysisResult,
    ProfitabilityAnalysisResult,
    LeverageAnalysisResult,
    BankingRatiosResult,
    PromoterContributionResult,
    FinancingStructureResult,
    RiskEngineResult,
    ViabilityAssessmentResult,
    AppraisalValidationResult,
    ValidationState,
    ViabilityClassification
)
from app.services.financial_engine.appraisal.constants import (
    LIQUIDITY_CURRENT_RATIO_ADEQUATE,
    LIQUIDITY_CURRENT_RATIO_TIGHT
)


class AppraisalSummaryBuilder:
    """
    Builds the executive banking appraisal summary for DPR.
    """

    def build(
        self,
        debt_service: Optional[DebtServiceAnalysisResult] = None,
        repayment_capacity: Optional[RepaymentCapacityResult] = None,
        dscr: Optional[DSCRAnalysisResult] = None,
        break_even: Optional[BreakEvenAnalysisResult] = None,
        liquidity: Optional[LiquidityAnalysisResult] = None,
        profitability: Optional[ProfitabilityAnalysisResult] = None,
        leverage: Optional[LeverageAnalysisResult] = None,
        banking_ratios: Optional[BankingRatiosResult] = None,
        promoter_contribution: Optional[PromoterContributionResult] = None,
        financing: Optional[FinancingStructureResult] = None,
        risk_result: Optional[RiskEngineResult] = None,
        viability: Optional[ViabilityAssessmentResult] = None,
        validation: Optional[AppraisalValidationResult] = None,
        critical_unknowns: Optional[List[str]] = None
    ) -> AppraisalSummary:
        # 1. Project Cost & Financing
        proj_cost = financing.total_project_cost if financing else None
        prom_contrib = promoter_contribution.actual_promoter_contribution if promoter_contribution else None
        prom_pct = promoter_contribution.contribution_percentage if promoter_contribution else None
        debt_exp = financing.term_loan if financing else None

        fin_struct_dict = {
            "total_project_cost": proj_cost,
            "promoter_contribution": prom_contrib,
            "term_loan": debt_exp,
            "working_capital_financing": financing.working_capital_financing if financing else None,
            "total_sources": financing.total_sources if financing else None,
            "total_uses": financing.total_uses if financing else None,
            "financing_gap_surplus": financing.financing_gap_surplus if financing else None,
            "debt_equity_mix": financing.debt_equity_mix if financing else None,
        }

        # 2. Profitability Snapshot
        y1_prof = profitability.years[0] if (profitability and profitability.years) else None
        rev_y1 = y1_prof.revenue if y1_prof else None
        ebitda_y1 = y1_prof.ebitda if y1_prof else None
        pat_y1 = y1_prof.pat if y1_prof else None
        roce_y1 = y1_prof.roce_pct if y1_prof else None
        roe_y1 = y1_prof.roe_pct if y1_prof else None
        roa_y1 = y1_prof.roa_pct if y1_prof else None

        # 3. Coverage & Break-even
        avg_dscr = dscr.average_dscr if dscr else None
        min_dscr = dscr.minimum_dscr if dscr else None
        icr_y1 = banking_ratios.icr_years[0].icr if (banking_ratios and banking_ratios.icr_years) else None

        be_sales_y1 = break_even.year1_break_even_sales if break_even else None
        be_util_y1 = break_even.year1_break_even_utilization_pct if break_even else None
        mos_y1 = break_even.year1_margin_of_safety_pct if break_even else None

        # 4. Liquidity & Leverage
        y1_liq = liquidity.years[0] if (liquidity and liquidity.years) else None
        cr_y1 = y1_liq.current_ratio if y1_liq else None
        qr_y1 = y1_liq.quick_ratio if y1_liq else None

        init_der = leverage.initial_der if leverage else None
        init_tol_tnw = leverage.initial_tol_tnw if leverage else None

        # 5. Returns
        irr_val = banking_ratios.irr if banking_ratios else None
        npv_val = banking_ratios.npv if banking_ratios else None
        disc_rate = banking_ratios.discount_rate if banking_ratios else None
        payback_val = banking_ratios.payback_period_years if banking_ratios else None

        # 6. Overall Assessments
        repay_assess = repayment_capacity.capacity_assessment if repayment_capacity else "UNRESOLVED"
        wc_assess = liquidity.working_capital_adequacy if liquidity else "UNRESOLVED"
        viab_class = viability.classification if viability else ViabilityClassification.NOT_ASSESSABLE
        val_status = ValidationState.PASSED if (validation and validation.all_passed) else (
            ValidationState.FAILED if (validation and validation.failed_checks > 0) else ValidationState.UNRESOLVED
        )

        tot_risks = risk_result.total_flags if risk_result else 0
        crit_risks = risk_result.critical_flags if risk_result else 0

        # Consistent liquidity position using centralized thresholds
        if cr_y1 is None:
            liq_pos = "UNRESOLVED"
        elif cr_y1 >= LIQUIDITY_CURRENT_RATIO_ADEQUATE:
            liq_pos = "ADEQUATE"
        elif cr_y1 >= LIQUIDITY_CURRENT_RATIO_TIGHT:
            liq_pos = "TIGHT"
        else:
            liq_pos = "CONSTRAINED"

        return AppraisalSummary(
            project_cost=proj_cost,
            promoter_contribution=prom_contrib,
            promoter_contribution_pct=prom_pct,
            debt_exposure=debt_exp,
            financing_structure=fin_struct_dict,
            revenue_year1=rev_y1,
            ebitda_year1=ebitda_y1,
            pat_year1=pat_y1,
            average_dscr=avg_dscr,
            minimum_dscr=min_dscr,
            icr_year1=icr_y1,
            break_even_sales_year1=be_sales_y1,
            break_even_utilization_pct_year1=be_util_y1,
            margin_of_safety_pct_year1=mos_y1,
            current_ratio_year1=cr_y1,
            quick_ratio_year1=qr_y1,
            initial_der=init_der,
            initial_tol_tnw=init_tol_tnw,
            roce_year1=roce_y1,
            roe_year1=roe_y1,
            roa_year1=roa_y1,
            irr=irr_val,
            npv=npv_val,
            discount_rate=disc_rate,
            payback_period_years=payback_val,
            repayment_capacity=repay_assess,
            liquidity_position=liq_pos,
            working_capital_adequacy=wc_assess,
            financial_viability=viab_class,
            financial_risks_count=tot_risks,
            critical_risks_count=crit_risks,
            unresolved_critical_data=list(critical_unknowns or []),
            validation_status=val_status
        )


appraisal_summary_builder = AppraisalSummaryBuilder()
