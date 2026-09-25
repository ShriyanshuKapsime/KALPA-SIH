"""
Viability Assessment Engine for M4 Banking Appraisal.
Deterministically classifies enterprise bankability into four transparent states:
FINANCIALLY_VIABLE, CONDITIONALLY_VIABLE, FINANCIALLY_STRESSED, NOT_ASSESSABLE.
Strict rule: Zero arbitrary 0-100 scoring. Transparent, auditable rule-based conclusions.
"""
from typing import List, Optional, Dict, Any
from app.services.financial_engine.appraisal.appraisal_schema import (
    ViabilityClassification,
    ViabilityAssessmentResult,
    RiskEngineResult,
    DebtServiceAnalysisResult,
    RepaymentCapacityResult,
    DSCRAnalysisResult,
    BreakEvenAnalysisResult,
    LiquidityAnalysisResult,
    ProfitabilityAnalysisResult,
    LeverageAnalysisResult,
    PromoterContributionResult,
    FinancingStructureResult,
    AppraisalStatus,
    RiskSeverity
)
from app.services.financial_engine.appraisal.constants import (
    DSCR_BENCHMARK,
    DSCR_MINIMUM,
    LIQUIDITY_CURRENT_RATIO_ADEQUATE,
    LIQUIDITY_CURRENT_RATIO_TIGHT,
    LEVERAGE_DER_HIGH,
    LEVERAGE_DER_ELEVATED,
    BREAK_EVEN_UTILIZATION_HIGH,
    BREAK_EVEN_UTILIZATION_MODERATE
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode


class ViabilityEngine:
    """
    Deterministic financial viability evaluation engine.
    """

    def evaluate(
        self,
        risk_result: RiskEngineResult,
        debt_service: Optional[DebtServiceAnalysisResult] = None,
        repayment_capacity: Optional[RepaymentCapacityResult] = None,
        dscr: Optional[DSCRAnalysisResult] = None,
        break_even: Optional[BreakEvenAnalysisResult] = None,
        liquidity: Optional[LiquidityAnalysisResult] = None,
        profitability: Optional[ProfitabilityAnalysisResult] = None,
        leverage: Optional[LeverageAnalysisResult] = None,
        promoter_contribution: Optional[PromoterContributionResult] = None,
        financing: Optional[FinancingStructureResult] = None,
        critical_unknowns: Optional[List[str]] = None
    ) -> ViabilityAssessmentResult:
        reason_codes: List[ReasonCode] = []
        evidence: List[str] = []
        unresolved_deps = list(critical_unknowns or [])

        # Supporting metrics snapshot
        metrics: Dict[str, Any] = {
            "is_zero_debt": debt_service.is_zero_debt if debt_service else False,
            "average_dscr": dscr.average_dscr if dscr else None,
            "minimum_dscr": dscr.minimum_dscr if dscr else None,
            "average_current_ratio": liquidity.average_current_ratio if liquidity else None,
            "initial_der": leverage.initial_der if leverage else None,
            "net_profit_margin_pct": profitability.average_net_profit_margin_pct if profitability else None,
            "break_even_utilization_pct": break_even.year1_break_even_utilization_pct if break_even else None,
            "financing_gap_surplus": financing.financing_gap_surplus if financing else None,
            "promoter_gap_surplus": promoter_contribution.gap_surplus if promoter_contribution else None,
        }

        # ---------------------------------------------------------------------
        # Condition 1: NOT_ASSESSABLE (Critical information missing / unresolved)
        # ---------------------------------------------------------------------
        is_zero_debt = debt_service.is_zero_debt if debt_service else False

        if not profitability or profitability.status == AppraisalStatus.UNRESOLVED or profitability.average_net_profit_margin_pct is None:
            unresolved_deps.append("profitability")
        if not financing or financing.status == AppraisalStatus.UNRESOLVED or financing.total_sources is None or financing.total_uses is None:
            unresolved_deps.append("financing_structure")
        if not repayment_capacity or repayment_capacity.status == AppraisalStatus.UNRESOLVED:
            unresolved_deps.append("repayment_capacity")
        if not is_zero_debt and (not dscr or dscr.status == AppraisalStatus.UNRESOLVED or dscr.average_dscr is None):
            unresolved_deps.append("dscr")
        if not liquidity or liquidity.status == AppraisalStatus.UNRESOLVED or liquidity.average_current_ratio is None:
            unresolved_deps.append("liquidity")
        if not promoter_contribution or promoter_contribution.status == AppraisalStatus.UNRESOLVED:
            unresolved_deps.append("promoter_contribution")

        # Deduplicate while preserving order
        deduped_unresolved: List[str] = []
        for d in unresolved_deps:
            if d not in deduped_unresolved:
                deduped_unresolved.append(d)

        if deduped_unresolved:
            reason_codes.append(ReasonCode.INSUFFICIENT_DATA)
            evidence.append(f"Critical inputs unresolved: {', '.join(deduped_unresolved)}")
            return ViabilityAssessmentResult(
                classification=ViabilityClassification.NOT_ASSESSABLE,
                reason_codes=reason_codes,
                supporting_metrics=metrics,
                evidence=evidence,
                unresolved_dependencies=deduped_unresolved
            )

        # ---------------------------------------------------------------------
        # Condition 2: FINANCIALLY_STRESSED (Severe distress or shortfall)
        # ---------------------------------------------------------------------
        is_stressed = False

        # A. Financing Gap
        if financing and financing.financing_gap_surplus is not None and financing.financing_gap_surplus < -1.0:
            is_stressed = True
            reason_codes.append(ReasonCode.FINANCING_GAP)
            evidence.append(f"Financing gap of ₹{abs(financing.financing_gap_surplus):,.2f} leaves project unfunded.")

        # B. Repayment Capacity Insufficiency
        if repayment_capacity and repayment_capacity.capacity_assessment == "INSUFFICIENT":
            is_stressed = True
            reason_codes.append(ReasonCode.WEAK_REPAYMENT_CAPACITY)
            deficit_str = f"₹{abs(repayment_capacity.cumulative_surplus_deficit):,.2f}" if repayment_capacity.cumulative_surplus_deficit is not None else "unresolved"
            evidence.append(f"Operating cash flow cannot cover debt service obligations (CADS deficit: {deficit_str}).")

        # C. Critical Low DSCR (< DSCR_MINIMUM)
        if dscr and dscr.minimum_dscr is not None and not is_zero_debt:
            if dscr.minimum_dscr < DSCR_MINIMUM:
                is_stressed = True
                reason_codes.append(ReasonCode.LOW_DSCR)
                evidence.append(f"Minimum DSCR ({dscr.minimum_dscr}x) is below {DSCR_MINIMUM}x.")

        # D. Negative Profitability
        if profitability and profitability.average_net_profit_margin_pct is not None and profitability.average_net_profit_margin_pct < 0.0:
            is_stressed = True
            reason_codes.append(ReasonCode.NEGATIVE_PROFITABILITY)
            evidence.append(f"Enterprise operates at a loss with negative net profit margin ({profitability.average_net_profit_margin_pct}%).")

        # E. Critical Risk Flags
        if risk_result.critical_flags > 0:
            is_stressed = True

        if is_stressed:
            return ViabilityAssessmentResult(
                classification=ViabilityClassification.FINANCIALLY_STRESSED,
                reason_codes=reason_codes,
                supporting_metrics=metrics,
                evidence=evidence,
                unresolved_dependencies=[]
            )

        # ---------------------------------------------------------------------
        # Condition 3: CONDITIONALLY_VIABLE (Modest buffers or material weaknesses)
        # ---------------------------------------------------------------------
        is_conditional = False

        # A. Promoter Contribution Gap
        if promoter_contribution and not promoter_contribution.is_adequate:
            is_conditional = True
            reason_codes.append(ReasonCode.PROMOTER_CONTRIBUTION_GAP)
            if promoter_contribution.gap_surplus is not None:
                evidence.append(f"Promoter margin deficit of ₹{abs(promoter_contribution.gap_surplus):,.2f}.")
            else:
                evidence.append("Promoter equity margin does not meet required benchmark.")

        # B. Tight DSCR (DSCR_MINIMUM <= DSCR < DSCR_BENCHMARK)
        if dscr and dscr.minimum_dscr is not None and not is_zero_debt:
            if dscr.minimum_dscr < DSCR_BENCHMARK:
                is_conditional = True
                reason_codes.append(ReasonCode.LOW_DSCR)
                evidence.append(f"Minimum DSCR ({dscr.minimum_dscr}x) is below institutional benchmark ({DSCR_BENCHMARK}x).")

        # C. Repayment Capacity Tight
        if repayment_capacity and repayment_capacity.capacity_assessment == "TIGHT":
            is_conditional = True
            reason_codes.append(ReasonCode.WEAK_REPAYMENT_CAPACITY)
            evidence.append("Repayment capacity coverage provides thin buffer against revenue shortfall.")

        # D. Weak Liquidity (Current Ratio < LIQUIDITY_CURRENT_RATIO_ADEQUATE)
        if liquidity and liquidity.average_current_ratio is not None and liquidity.average_current_ratio < LIQUIDITY_CURRENT_RATIO_ADEQUATE:
            is_conditional = True
            reason_codes.append(ReasonCode.WEAK_LIQUIDITY)
            evidence.append(f"Current ratio ({liquidity.average_current_ratio}x) is below institutional benchmark ({LIQUIDITY_CURRENT_RATIO_ADEQUATE}x).")

        # E. High Leverage (DER > LEVERAGE_DER_ELEVATED)
        if leverage and leverage.initial_der is not None and leverage.initial_der > LEVERAGE_DER_ELEVATED:
            is_conditional = True
            reason_codes.append(ReasonCode.HIGH_LEVERAGE)
            evidence.append(f"Elevated initial Debt-Equity ratio ({leverage.initial_der}x > {LEVERAGE_DER_ELEVATED}x).")

        # F. High Break-Even (> BREAK_EVEN_UTILIZATION_MODERATE)
        if break_even and break_even.year1_break_even_utilization_pct is not None and break_even.year1_break_even_utilization_pct > BREAK_EVEN_UTILIZATION_MODERATE:
            is_conditional = True
            reason_codes.append(ReasonCode.HIGH_BREAK_EVEN)
            evidence.append(f"Break-even utilization is high at {break_even.year1_break_even_utilization_pct:.1f}%.")

        # G. Any High severity risk flags
        if risk_result.high_flags > 0:
            is_conditional = True

        if is_conditional:
            return ViabilityAssessmentResult(
                classification=ViabilityClassification.CONDITIONALLY_VIABLE,
                reason_codes=reason_codes,
                supporting_metrics=metrics,
                evidence=evidence,
                unresolved_dependencies=[]
            )

        # ---------------------------------------------------------------------
        # Condition 4: FINANCIALLY_VIABLE (All criteria satisfied)
        # ---------------------------------------------------------------------
        evidence.append("Repayment capacity satisfies institutional debt coverage norms.")
        evidence.append("Sources and uses of funds are balanced with zero financing gap.")
        evidence.append("Operating margins, liquidity, and leverage remain within prudent banking parameters.")

        return ViabilityAssessmentResult(
            classification=ViabilityClassification.FINANCIALLY_VIABLE,
            reason_codes=reason_codes,
            supporting_metrics=metrics,
            evidence=evidence,
            unresolved_dependencies=[]
        )


viability_engine = ViabilityEngine()
