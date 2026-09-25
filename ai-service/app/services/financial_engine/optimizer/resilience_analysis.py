"""
Resilience Analysis for Milestone 5.
Evaluates the comparative resilience matrix across base case, individual downside shocks,
and combined macro stress. Transparently identifies key vulnerabilities.
Zero arbitrary scoring. Follows explicit policy thresholds and severity hierarchy.
"""
from typing import List, Optional
from app.services.financial_engine.optimizer.m5_config import (
    SEVERITY_ORDER,
    DSCR_RESILIENCE_BENCHMARK,
    DSCR_RESILIENCE_MINIMUM,
    CURRENT_RATIO_RESILIENCE_MINIMUM,
    CASH_BUFFER_RESILIENCE_MONTHS,
    BREAK_EVEN_MAX_UTILIZATION,
    MAX_ACCEPTABLE_DER
)
from app.services.financial_engine.optimizer.m5_schema import (
    StressScenarioResult,
    ResilienceComparisonRow,
    ResilienceAnalysisResult,
    ResilienceStatus
)
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode


def select_worst_case_scenario(
    stress_scenarios: List[StressScenarioResult]
) -> Optional[StressScenarioResult]:
    """
    Selects the single worst-case scenario using a transparent multi-dimensional policy hierarchy:
    1. Severity Tier: CRITICAL > STRESSED > RESILIENT > NOT_ASSESSABLE
    2. Policy Ordering within Tier:
       a. Financing Gap Shortfall (descending: highest gap first)
       b. DSCR (ascending: lowest DSCR first)
       c. Current Ratio (ascending: lowest liquidity first)
       d. Cash Buffer Months (ascending: shortest buffer first)
       e. Break-Even Utilization % (descending: highest utilization first)
    """
    if not stress_scenarios:
        return None

    def worst_scenario_key(sc: StressScenarioResult):
        # 1. Severity rank (lower number = more severe)
        sev_rank = SEVERITY_ORDER.get(sc.resilience_status.value, 99)

        # 2. Financing Gap (negated so higher gap gives smaller number)
        gap = -(sc.financing_gap) if sc.financing_gap is not None else 0.0

        # 3. DSCR (lower DSCR gives smaller number)
        dscr = sc.dscr if sc.dscr is not None else 999.0

        # 4. Current Ratio (lower CR gives smaller number)
        cr = sc.current_ratio if sc.current_ratio is not None else 999.0

        # 5. Cash Buffer (lower buffer gives smaller number)
        cb = sc.cash_buffer_months if sc.cash_buffer_months is not None else 999.0

        # 6. Break-Even Utilization (negated so higher utilization gives smaller number)
        be = -(sc.break_even_utilization_pct) if sc.break_even_utilization_pct is not None else 0.0

        return (sev_rank, gap, dscr, cr, cb, be)

    sorted_scenarios = sorted(stress_scenarios, key=worst_scenario_key)
    return sorted_scenarios[0]


class ResilienceAnalysisEngine:
    """
    Synthesizes stress scenario outputs into an executive resilience comparison matrix.
    """

    def evaluate(
        self,
        stress_scenarios: List[StressScenarioResult]
    ) -> ResilienceAnalysisResult:
        if not stress_scenarios:
            return ResilienceAnalysisResult(
                status="UNRESOLVED",
                comparison_matrix=[],
                overall_resilience=ResilienceStatus.NOT_ASSESSABLE,
                key_vulnerabilities=["No stress scenarios evaluated."],
                reason_codes=[M5ReasonCode.INSUFFICIENT_DATA]
            )

        rows: List[ResilienceComparisonRow] = []
        worst_resilience = ResilienceStatus.RESILIENT
        has_unresolved = False
        vulnerabilities: List[str] = []
        overall_reason_codes: List[M5ReasonCode] = []

        for sc in stress_scenarios:
            margin_pct: Optional[float] = None
            if sc.revenue is not None and sc.revenue > 0 and sc.pat is not None:
                margin_pct = round((sc.pat / sc.revenue) * 100.0, 2)

            row = ResilienceComparisonRow(
                scenario_id=sc.scenario_id,
                scenario_name=sc.scenario_name,
                revenue=sc.revenue,
                profitability_margin_pct=margin_pct,
                cash_from_ops=sc.operating_cash_flow,
                dscr=sc.dscr,
                current_ratio=sc.current_ratio,
                break_even_utilization_pct=sc.break_even_utilization_pct,
                funding_gap=sc.financing_gap,
                resilience_status=sc.resilience_status,
                reason_codes=sc.reason_codes
            )
            rows.append(row)

            # Track overall worst severity
            if sc.resilience_status == ResilienceStatus.CRITICAL:
                worst_resilience = ResilienceStatus.CRITICAL
                if M5ReasonCode.DSCR_BELOW_THRESHOLD in sc.reason_codes:
                    vulnerabilities.append(f"Debt service default risk under {sc.scenario_name} (DSCR < 1.0).")
                if M5ReasonCode.NEGATIVE_CASH_FLOW in sc.reason_codes:
                    vulnerabilities.append(f"Operating cash deficit under {sc.scenario_name}.")
                if M5ReasonCode.FINANCING_GAP in sc.reason_codes:
                    vulnerabilities.append(f"Financing gap shortfall under {sc.scenario_name}.")
            elif sc.resilience_status == ResilienceStatus.STRESSED and worst_resilience != ResilienceStatus.CRITICAL:
                worst_resilience = ResilienceStatus.STRESSED
                if M5ReasonCode.LIQUIDITY_STRESS in sc.reason_codes:
                    vulnerabilities.append(f"Working capital / liquidity tightening under {sc.scenario_name}.")
                if M5ReasonCode.BREAK_EVEN_EXCEEDED in sc.reason_codes:
                    vulnerabilities.append(f"High break-even utilization (> {BREAK_EVEN_MAX_UTILIZATION}%) under {sc.scenario_name}.")
            elif sc.resilience_status in (ResilienceStatus.NOT_ASSESSABLE, ResilienceStatus.UNRESOLVED):
                has_unresolved = True

            for rc in sc.reason_codes:
                if rc not in overall_reason_codes and rc != M5ReasonCode.RESILIENT:
                    overall_reason_codes.append(rc)

        all_unresolved = all(sc.resilience_status in (ResilienceStatus.NOT_ASSESSABLE, ResilienceStatus.UNRESOLVED) for sc in stress_scenarios)
        if all_unresolved:
            worst_resilience = ResilienceStatus.UNRESOLVED if all(sc.resilience_status == ResilienceStatus.UNRESOLVED for sc in stress_scenarios) else ResilienceStatus.NOT_ASSESSABLE
            result_status = "UNRESOLVED"
        elif has_unresolved:
            if worst_resilience == ResilienceStatus.RESILIENT:
                worst_resilience = ResilienceStatus.NOT_ASSESSABLE
            result_status = "PARTIALLY_DERIVED"
        else:
            result_status = "RESOLVED"

        if not overall_reason_codes:
            overall_reason_codes.append(M5ReasonCode.RESILIENT)

        unique_vulns = list(dict.fromkeys(vulnerabilities))

        return ResilienceAnalysisResult(
            status=result_status,
            comparison_matrix=rows,
            overall_resilience=worst_resilience,
            key_vulnerabilities=unique_vulns,
            reason_codes=overall_reason_codes
        )


resilience_analysis_engine = ResilienceAnalysisEngine()
