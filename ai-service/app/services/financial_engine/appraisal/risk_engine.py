"""
Deterministic Risk Engine for M4 Banking Appraisal.
Scans financial appraisal results across all sub-engines and raises structured,
deterministic risk flags without using opaque AI scoring.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    RiskEngineResult,
    RiskFlag,
    RiskCategory,
    RiskSeverity,
    MetricSource,
    ValidationState,
    DebtServiceAnalysisResult,
    RepaymentCapacityResult,
    DSCRAnalysisResult,
    BreakEvenAnalysisResult,
    LiquidityAnalysisResult,
    ProfitabilityAnalysisResult,
    LeverageAnalysisResult,
    PromoterContributionResult,
    FinancingStructureResult,
    AppraisalValidationResult,
    AppraisalStatus
)
from app.services.financial_engine.appraisal.constants import (
    DSCR_MINIMUM,
    DSCR_BENCHMARK,
    LIQUIDITY_CURRENT_RATIO_TIGHT,
    LIQUIDITY_CURRENT_RATIO_ADEQUATE,
    LEVERAGE_DER_HIGH,
    LEVERAGE_DER_ELEVATED,
    BREAK_EVEN_UTILIZATION_HIGH,
    BREAK_EVEN_UTILIZATION_MODERATE
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.risk_flags import create_risk_flag


class RiskEngine:
    """
    Deterministic banking risk appraisal engine.
    """

    def evaluate(
        self,
        debt_service: Optional[DebtServiceAnalysisResult] = None,
        repayment_capacity: Optional[RepaymentCapacityResult] = None,
        dscr: Optional[DSCRAnalysisResult] = None,
        break_even: Optional[BreakEvenAnalysisResult] = None,
        liquidity: Optional[LiquidityAnalysisResult] = None,
        profitability: Optional[ProfitabilityAnalysisResult] = None,
        leverage: Optional[LeverageAnalysisResult] = None,
        promoter_contribution: Optional[PromoterContributionResult] = None,
        financing: Optional[FinancingStructureResult] = None,
        validation: Optional[AppraisalValidationResult] = None,
        critical_unknowns: Optional[List[str]] = None
    ) -> RiskEngineResult:
        flags: List[RiskFlag] = []

        # 1. Critical Data Unresolved
        if critical_unknowns:
            for unk in critical_unknowns:
                flags.append(create_risk_flag(
                    category=RiskCategory.DATA_INTEGRITY,
                    severity=RiskSeverity.CRITICAL,
                    reason_code=ReasonCode.INSUFFICIENT_DATA,
                    trigger=f"Critical variable '{unk}' is unresolved",
                    evidence=f"Input for {unk} is None or missing from foundation",
                    source=MetricSource.DERIVED,
                    affected_metric=unk,
                    message=f"Appraisal cannot be verified because required input '{unk}' is missing.",
                    mitigation=f"Obtain verified baseline data for {unk} before sanction."
                ))

        # 2. Debt Service Risks
        if debt_service and debt_service.status == AppraisalStatus.UNRESOLVED and not debt_service.is_zero_debt:
            flags.append(create_risk_flag(
                category=RiskCategory.REPAYMENT,
                severity=RiskSeverity.CRITICAL,
                reason_code=ReasonCode.MISSING_DEBT_SERVICE,
                trigger="Debt service schedule unresolved",
                evidence="Amortization / repayment schedule is missing or incomplete",
                source=MetricSource.STAGE9,
                affected_metric="total_debt_service",
                message="Cannot establish annual debt service liability.",
                mitigation="Re-run Stage 9 amortization schedule generator."
            ))

        # 3. Repayment Capacity Risks
        if repayment_capacity and repayment_capacity.status == AppraisalStatus.RESOLVED:
            if repayment_capacity.capacity_assessment == "INSUFFICIENT":
                flags.append(create_risk_flag(
                    category=RiskCategory.REPAYMENT,
                    severity=RiskSeverity.CRITICAL,
                    reason_code=ReasonCode.WEAK_REPAYMENT_CAPACITY,
                    trigger="Cash Available for Debt Service (CADS) is less than debt service obligations",
                    evidence=f"Cumulative surplus/deficit: ₹{repayment_capacity.cumulative_surplus_deficit:,.2f}",
                    source=MetricSource.DERIVED,
                    affected_metric="repayment_capacity",
                    message="Projected operating cash flow is insufficient to service proposed loan obligations.",
                    mitigation="Restructure debt tenure, negotiate lower interest, or increase promoter equity."
                ))
            elif repayment_capacity.capacity_assessment == "TIGHT":
                flags.append(create_risk_flag(
                    category=RiskCategory.REPAYMENT,
                    severity=RiskSeverity.MEDIUM,
                    reason_code=ReasonCode.WEAK_REPAYMENT_CAPACITY,
                    trigger="Debt service coverage buffer is tight (CADS/Debt Service between 1.0x and 1.15x)",
                    evidence=f"Minimum capacity ratio: {repayment_capacity.minimum_capacity_ratio}x",
                    source=MetricSource.DERIVED,
                    affected_metric="repayment_capacity",
                    message="Repayment capacity provides thin buffer against operational underperformance.",
                    mitigation="Build debt service reserve account (DSRA) equivalent to 3-6 months EMI."
                ))

        # 4. DSCR Risks & Stage 9 Reconciliation Mismatch
        if dscr:
            if dscr.minimum_dscr is not None and not (debt_service and debt_service.is_zero_debt):
                if dscr.minimum_dscr < DSCR_MINIMUM:
                    flags.append(create_risk_flag(
                        category=RiskCategory.REPAYMENT,
                        severity=RiskSeverity.CRITICAL,
                        reason_code=ReasonCode.LOW_DSCR,
                        trigger=f"Minimum DSCR ({dscr.minimum_dscr}x) is below {DSCR_MINIMUM}x",
                        evidence=f"Average DSCR: {dscr.average_dscr}x, Minimum DSCR: {dscr.minimum_dscr}x",
                        source=MetricSource.DERIVED,
                        affected_metric="minimum_dscr",
                        message="Operating cash flow does not cover annual debt service obligations in at least one year.",
                        mitigation="Extend loan tenure or reduce principal borrowing."
                    ))
                elif dscr.minimum_dscr < DSCR_BENCHMARK:
                    flags.append(create_risk_flag(
                        category=RiskCategory.REPAYMENT,
                        severity=RiskSeverity.MEDIUM,
                        reason_code=ReasonCode.LOW_DSCR,
                        trigger=f"Minimum DSCR ({dscr.minimum_dscr}x) is below institutional benchmark ({DSCR_BENCHMARK}x)",
                        evidence=f"Minimum DSCR: {dscr.minimum_dscr}x",
                        source=MetricSource.DERIVED,
                        affected_metric="minimum_dscr",
                        message=f"Coverage ratio is below preferred banking safety threshold of {DSCR_BENCHMARK}x.",
                        mitigation="Enhance operating efficiency or infuse additional promoter equity."
                    ))

            if dscr.reconciliation_status == ValidationState.FAILED:
                flags.append(create_risk_flag(
                    category=RiskCategory.STAGE9_RECONCILIATION,
                    severity=RiskSeverity.HIGH,
                    reason_code=ReasonCode.STAGE9_RECONCILIATION_FAILED,
                    trigger="M4 DSCR differs from authoritative Stage 9 DSCR",
                    evidence=f"Stage 9 DSCR: {dscr.stage9_dscr}x, M4 DSCR: {dscr.years[0].dscr if dscr.years else dscr.average_dscr}x, Diff: {dscr.reconciliation_difference}",
                    source=MetricSource.STAGE9,
                    affected_metric="dscr_reconciliation",
                    message="Discrepancy detected between Stage 9 and M4 DSCR models.",
                    mitigation="Audit cash flow basis differences between quarterly and annual statement projections."
                ))

        # 5. Liquidity Risks
        if liquidity and liquidity.status == AppraisalStatus.RESOLVED:
            if liquidity.average_current_ratio is not None:
                if liquidity.average_current_ratio < LIQUIDITY_CURRENT_RATIO_TIGHT:
                    flags.append(create_risk_flag(
                        category=RiskCategory.LIQUIDITY,
                        severity=RiskSeverity.HIGH,
                        reason_code=ReasonCode.WEAK_LIQUIDITY,
                        trigger=f"Average Current Ratio ({liquidity.average_current_ratio}x) is below {LIQUIDITY_CURRENT_RATIO_TIGHT}x",
                        evidence="Current assets are lower than current liabilities.",
                        source=MetricSource.DERIVED,
                        affected_metric="average_current_ratio",
                        message="Negative working capital; current liabilities exceed liquid assets.",
                        mitigation="Infuse long-term working capital term loan or promoter margin."
                    ))
                elif liquidity.average_current_ratio < LIQUIDITY_CURRENT_RATIO_ADEQUATE:
                    flags.append(create_risk_flag(
                        category=RiskCategory.LIQUIDITY,
                        severity=RiskSeverity.LOW,
                        reason_code=ReasonCode.WEAK_LIQUIDITY,
                        trigger=f"Average Current Ratio ({liquidity.average_current_ratio}x) is below {LIQUIDITY_CURRENT_RATIO_ADEQUATE}x",
                        evidence=f"Current Ratio falls below institutional Tandon Committee benchmark ({LIQUIDITY_CURRENT_RATIO_ADEQUATE}x).",
                        source=MetricSource.DERIVED,
                        affected_metric="average_current_ratio",
                        message="Working capital liquidity buffer is modest.",
                        mitigation="Optimize inventory turnover and accelerate receivables collection."
                    ))

        # 6. Leverage Risks
        if leverage and leverage.status == AppraisalStatus.RESOLVED:
            if leverage.initial_der is not None:
                if leverage.initial_der > LEVERAGE_DER_HIGH:
                    flags.append(create_risk_flag(
                        category=RiskCategory.LEVERAGE,
                        severity=RiskSeverity.HIGH,
                        reason_code=ReasonCode.HIGH_LEVERAGE,
                        trigger=f"Initial Debt-to-Equity Ratio ({leverage.initial_der}x) exceeds {LEVERAGE_DER_HIGH}x",
                        evidence=f"Debt/Equity: {leverage.initial_der}x",
                        source=MetricSource.DERIVED,
                        affected_metric="initial_der",
                        message="Highly leveraged capital structure increases financial vulnerability to demand shocks.",
                        mitigation="Increase promoter equity contribution."
                    ))
                elif leverage.initial_der > LEVERAGE_DER_ELEVATED:
                    flags.append(create_risk_flag(
                        category=RiskCategory.LEVERAGE,
                        severity=RiskSeverity.MEDIUM,
                        reason_code=ReasonCode.HIGH_LEVERAGE,
                        trigger=f"Initial Debt-to-Equity Ratio ({leverage.initial_der}x) exceeds {LEVERAGE_DER_ELEVATED}x",
                        evidence=f"Debt/Equity: {leverage.initial_der}x",
                        source=MetricSource.DERIVED,
                        affected_metric="initial_der",
                        message="Moderately elevated financial leverage.",
                        mitigation="Retain initial earnings within the business."
                    ))

        # 7. Profitability Risks
        if profitability and profitability.status == AppraisalStatus.RESOLVED:
            if profitability.average_net_profit_margin_pct is not None and profitability.average_net_profit_margin_pct < 0.0:
                flags.append(create_risk_flag(
                    category=RiskCategory.PROFITABILITY,
                    severity=RiskSeverity.HIGH,
                    reason_code=ReasonCode.NEGATIVE_PROFITABILITY,
                    trigger=f"Negative average Net Profit Margin ({profitability.average_net_profit_margin_pct}%)",
                    evidence="Average PAT margin is negative.",
                    source=MetricSource.DERIVED,
                    affected_metric="average_net_profit_margin_pct",
                    message="Business operations are projected to generate net losses.",
                    mitigation="Improve pricing structure, lower cost of goods sold, or reduce fixed overheads."
                ))

        # 8. Break-Even Risks
        if break_even and break_even.year1_break_even_utilization_pct is not None:
            if break_even.year1_break_even_utilization_pct > BREAK_EVEN_UTILIZATION_HIGH:
                flags.append(create_risk_flag(
                    category=RiskCategory.BREAK_EVEN,
                    severity=RiskSeverity.HIGH,
                    reason_code=ReasonCode.HIGH_BREAK_EVEN,
                    trigger=f"Year 1 Break-Even utilization is {break_even.year1_break_even_utilization_pct:.1f}%",
                    evidence=f"Margin of safety is only {break_even.year1_margin_of_safety_pct:.1f}%",
                    source=MetricSource.DERIVED,
                    affected_metric="year1_break_even_utilization_pct",
                    message="High operational gearing; small drops in sales volume cause losses.",
                    mitigation="Convert fixed costs to variable costs where feasible."
                ))

        # 9. Promoter Contribution Gap
        if promoter_contribution and promoter_contribution.status == AppraisalStatus.RESOLVED:
            if not promoter_contribution.is_adequate and promoter_contribution.gap_surplus is not None and promoter_contribution.gap_surplus < 0:
                flags.append(create_risk_flag(
                    category=RiskCategory.CAPITAL_STRUCTURE,
                    severity=RiskSeverity.HIGH,
                    reason_code=ReasonCode.PROMOTER_CONTRIBUTION_GAP,
                    trigger="Promoter equity contribution is below required scheme/banking margin",
                    evidence=f"Deficit: ₹{abs(promoter_contribution.gap_surplus):,.2f} ({promoter_contribution.contribution_percentage}% actual vs {promoter_contribution.required_percentage}% required)",
                    source=MetricSource.DERIVED,
                    affected_metric="promoter_contribution_gap",
                    message="Promoter has not committed sufficient equity to satisfy underwriting norms.",
                    mitigation="Infuse additional promoter margin capital prior to loan disbursement."
                ))

        # 10. Financing Gap
        if financing and financing.status == AppraisalStatus.RESOLVED:
            if financing.financing_gap_surplus is not None and financing.financing_gap_surplus < -1.0:
                flags.append(create_risk_flag(
                    category=RiskCategory.CAPITAL_STRUCTURE,
                    severity=RiskSeverity.CRITICAL,
                    reason_code=ReasonCode.FINANCING_GAP,
                    trigger=f"Financing gap of ₹{abs(financing.financing_gap_surplus):,.2f} identified",
                    evidence=f"Total Uses (₹{financing.total_uses:,.2f}) exceeds Total Sources (₹{financing.total_sources:,.2f})",
                    source=MetricSource.DERIVED,
                    affected_metric="financing_gap",
                    message="Total identified funding sources do not cover total estimated project costs.",
                    mitigation="Bridge financing gap with additional term loan, promoter equity, or capital subsidy."
                ))

        # Flag Counts
        crit = sum(1 for f in flags if f.severity == RiskSeverity.CRITICAL)
        high = sum(1 for f in flags if f.severity == RiskSeverity.HIGH)
        med = sum(1 for f in flags if f.severity == RiskSeverity.MEDIUM)
        low = sum(1 for f in flags if f.severity == RiskSeverity.LOW)

        return RiskEngineResult(
            total_flags=len(flags),
            critical_flags=crit,
            high_flags=high,
            medium_flags=med,
            low_flags=low,
            flags=flags
        )


risk_engine = RiskEngine()
