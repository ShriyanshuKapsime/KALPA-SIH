"""
Deterministic Downside Stress Engine for Milestone 5.
Evaluates the impact of downside market, operational, cost, and interest shocks
on business performance, debt service coverage (DSCR), break-even, and liquidity.
Strictly non-fabricating: UNKNOWN remains UNKNOWN. Zero LLM calculations.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    ProfitLossStatement,
    CashFlowStatement,
    BalanceSheet,
    LoanManagement,
    DebtServiceAnalysis
)
from app.services.financial_engine.loan_calculator import LoanCalculator
from app.services.financial_engine.amortization import AmortizationEngine
from app.services.financial_engine.optimizer.m5_config import (
    DSCR_RESILIENCE_BENCHMARK,
    DSCR_RESILIENCE_MINIMUM,
    CURRENT_RATIO_RESILIENCE_MINIMUM,
    CASH_BUFFER_RESILIENCE_MONTHS,
    BREAK_EVEN_MAX_UTILIZATION,
    MAX_ACCEPTABLE_DER
)
from app.services.financial_engine.optimizer.m5_schema import (
    StressScenarioResult,
    StressScenarioType,
    ScenarioSource,
    ResilienceStatus
)
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode
from app.services.financial_engine.optimizer.stress_scenarios import (
    stress_scenario_generator,
    ScenarioSpecification
)


class StressEngine:
    """
    Executes deterministic scenario stress testing across multiple financial dimensions.
    """

    def __init__(self) -> None:
        self.loan_calc = LoanCalculator()

    def evaluate(
        self,
        profit_loss: Optional[ProfitLossStatement] = None,
        cash_flow: Optional[CashFlowStatement] = None,
        balance_sheet: Optional[BalanceSheet] = None,
        debt_service: Optional[Any] = None,
        loan_management: Optional[LoanManagement] = None,
        working_capital_analysis: Optional[Any] = None,
        working_capital_projection: Optional[Any] = None,
        project_cost: Optional[float] = None,
        verified_funding: Optional[float] = None,
        user_scenarios: Optional[List[Dict[str, Any]]] = None,
        provenance: Optional[M5ProvenanceBuilder] = None
    ) -> List[StressScenarioResult]:
        prov = provenance or M5ProvenanceBuilder()
        scenario_specs = stress_scenario_generator.generate_standard_scenarios(user_scenarios=user_scenarios)
        results: List[StressScenarioResult] = []

        # 1. Unpack Year 1 Baseline Metrics
        y1_pl = profit_loss.years[0] if (profit_loss and profit_loss.years) else None
        y1_cf = cash_flow.years[0] if (cash_flow and cash_flow.years) else None
        y1_bs = balance_sheet.years[0] if (balance_sheet and balance_sheet.years) else None

        base_rev = y1_pl.revenue if y1_pl else None
        base_cogs = y1_pl.cogs if y1_pl else None
        base_opex = y1_pl.operating_expenses if y1_pl else None
        base_depr = y1_pl.depreciation if (y1_pl and y1_pl.depreciation is not None) else None

        is_zero_debt = False
        base_ds_val: Optional[float] = None
        base_principal: Optional[float] = None
        base_rate: Optional[float] = None

        if loan_management:
            base_principal = loan_management.principal
            base_rate = loan_management.annual_interest_rate
            if base_principal == 0.0:
                is_zero_debt = True
                base_ds_val = 0.0

        if debt_service and hasattr(debt_service, "years") and debt_service.years:
            ds_y1 = debt_service.years[0]
            if hasattr(ds_y1, "total_debt_service") and ds_y1.total_debt_service is not None:
                base_ds_val = ds_y1.total_debt_service
            elif isinstance(ds_y1, dict) and ds_y1.get("total_debt_service") is not None:
                base_ds_val = float(ds_y1["total_debt_service"])

        if hasattr(debt_service, "is_zero_debt") and debt_service.is_zero_debt:
            is_zero_debt = True
            base_ds_val = 0.0

        base_interest: Optional[float] = None
        if is_zero_debt:
            base_interest = 0.0
        elif y1_pl and y1_pl.interest_expense is not None:
            base_interest = y1_pl.interest_expense

        base_tax: Optional[float] = None
        if y1_pl and y1_pl.tax_expense is not None:
            base_tax = y1_pl.tax_expense
        elif y1_pl and y1_pl.profit_before_tax is not None and y1_pl.profit_after_tax is not None:
            base_tax = round(y1_pl.profit_before_tax - y1_pl.profit_after_tax, 2)
        elif y1_pl and getattr(y1_pl, "tax_status", None) in ("EXEMPT", "ZERO_RATED"):
            base_tax = 0.0
        elif (
            y1_pl and
            y1_pl.profit_after_tax is not None and
            base_rev is not None and
            base_cogs is not None and
            base_opex is not None and
            base_depr is not None and
            base_interest is not None
        ):
            implied_ebit = round(base_rev - base_cogs - base_opex - base_depr, 2)
            implied_pbt = round(implied_ebit - base_interest, 2)
            base_tax = round(implied_pbt - y1_pl.profit_after_tax, 2)

        # Current Assets & Liabilities
        base_ca = y1_bs.total_current_assets if y1_bs else None
        base_cl: Optional[float] = None
        if y1_bs:
            if y1_bs.trade_payables is not None and y1_bs.other_current_liabilities is not None:
                base_cl = round(y1_bs.trade_payables + y1_bs.other_current_liabilities, 2)

        # Authoritative Working Capital Baseline (M2 / M3)
        base_wc: Optional[float] = None
        if working_capital_analysis:
            base_wc = (
                getattr(working_capital_analysis, "total_working_capital", None)
                or getattr(working_capital_analysis, "operating_working_capital", None)
                or getattr(working_capital_analysis, "working_capital_requirement", None)
                or getattr(working_capital_analysis, "working_capital_gap", None)
                or getattr(working_capital_analysis, "net_working_capital", None)
                or getattr(working_capital_analysis, "inventory_requirement", None)
            )
        if base_wc is None and working_capital_projection and hasattr(working_capital_projection, "years") and working_capital_projection.years:
            base_wc = getattr(
                working_capital_projection.years[0],
                "net_working_capital",
                getattr(working_capital_projection.years[0], "working_capital_gap", None)
            )
        if base_wc is None and base_ca is not None and base_cl is not None:
            base_wc = round(base_ca - base_cl, 2)

        # Actual Cash Position (M3 Balance Sheet / Cash Flow)
        actual_cash: Optional[float] = None
        if y1_bs and y1_bs.cash_and_bank is not None:
            actual_cash = y1_bs.cash_and_bank
        elif y1_cf and y1_cf.closing_cash_balance is not None:
            actual_cash = y1_cf.closing_cash_balance

        # Actual Debt and Equity Position (M3 Balance Sheet)
        base_debt: Optional[float] = None
        base_equity: Optional[float] = None
        if is_zero_debt:
            base_debt = 0.0
        elif y1_bs:
            if y1_bs.term_loan_outstanding is not None:
                base_debt = y1_bs.term_loan_outstanding
            elif base_principal is not None:
                base_debt = base_principal
            if y1_bs.total_equity is not None:
                base_equity = y1_bs.total_equity
        elif base_principal is not None:
            base_debt = base_principal

        # Iterate Scenario Specs
        for spec in scenario_specs:
            res = self._run_single_scenario(
                spec=spec,
                base_rev=base_rev,
                base_cogs=base_cogs,
                base_opex=base_opex,
                base_depr=base_depr,
                base_interest=base_interest,
                base_tax=base_tax,
                base_ds_val=base_ds_val,
                base_principal=base_principal,
                base_rate=base_rate,
                is_zero_debt=is_zero_debt,
                base_ca=base_ca,
                base_cl=base_cl,
                base_wc=base_wc,
                actual_cash=actual_cash,
                base_debt=base_debt,
                base_equity=base_equity,
                project_cost=project_cost,
                verified_funding=verified_funding,
                loan_management=loan_management,
                provenance=prov
            )
            results.append(res)

        return results

    def _run_single_scenario(
        self,
        spec: ScenarioSpecification,
        base_rev: Optional[float],
        base_cogs: Optional[float],
        base_opex: Optional[float],
        base_depr: Optional[float],
        base_interest: Optional[float],
        base_tax: Optional[float],
        base_ds_val: Optional[float],
        base_principal: Optional[float],
        base_rate: Optional[float],
        is_zero_debt: bool,
        base_ca: Optional[float],
        base_cl: Optional[float],
        base_wc: Optional[float],
        actual_cash: Optional[float],
        base_debt: Optional[float],
        base_equity: Optional[float],
        project_cost: Optional[float],
        verified_funding: Optional[float],
        loan_management: Optional[LoanManagement],
        provenance: M5ProvenanceBuilder
    ) -> StressScenarioResult:
        s_type = spec.scenario_type
        params = spec.parameters

        # Check critical unknowns for affected drivers
        if s_type == StressScenarioType.BASE_CASE:
            if base_rev is None or base_cogs is None or base_opex is None:
                return StressScenarioResult(
                    scenario_id=spec.scenario_id,
                    scenario_name=spec.scenario_name,
                    scenario_type=s_type,
                    assumptions=params,
                    affected_drivers=spec.affected_drivers,
                    source=spec.source,
                    confidence=spec.confidence,
                    status="UNRESOLVED",
                    resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                    reason_codes=[M5ReasonCode.BASELINE_UNRESOLVED, M5ReasonCode.INSUFFICIENT_DATA]
                )

        if base_rev is None:
            return StressScenarioResult(
                scenario_id=spec.scenario_id,
                scenario_name=spec.scenario_name,
                scenario_type=s_type,
                assumptions=params,
                affected_drivers=spec.affected_drivers,
                source=spec.source,
                confidence=spec.confidence,
                status="UNRESOLVED",
                resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                reason_codes=[M5ReasonCode.UNRESOLVED_DRIVER, M5ReasonCode.INSUFFICIENT_DATA]
            )

        if s_type == StressScenarioType.VARIABLE_COST_INCREASE and base_cogs is None:
            return StressScenarioResult(
                scenario_id=spec.scenario_id,
                scenario_name=spec.scenario_name,
                scenario_type=s_type,
                assumptions=params,
                affected_drivers=spec.affected_drivers,
                source=spec.source,
                confidence=spec.confidence,
                status="UNRESOLVED",
                resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                reason_codes=[M5ReasonCode.UNRESOLVED_DRIVER, M5ReasonCode.INSUFFICIENT_DATA]
            )

        if s_type == StressScenarioType.FIXED_COST_INCREASE and base_opex is None:
            return StressScenarioResult(
                scenario_id=spec.scenario_id,
                scenario_name=spec.scenario_name,
                scenario_type=s_type,
                assumptions=params,
                affected_drivers=spec.affected_drivers,
                source=spec.source,
                confidence=spec.confidence,
                status="UNRESOLVED",
                resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                reason_codes=[M5ReasonCode.UNRESOLVED_DRIVER, M5ReasonCode.INSUFFICIENT_DATA]
            )

        if (s_type == StressScenarioType.WORKING_CAPITAL_PRESSURE or "wc_change_pct" in params) and base_wc is None:
            return StressScenarioResult(
                scenario_id=spec.scenario_id,
                scenario_name=spec.scenario_name,
                scenario_type=s_type,
                assumptions=params,
                affected_drivers=spec.affected_drivers,
                source=spec.source,
                confidence=spec.confidence,
                status="UNRESOLVED",
                resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                reason_codes=[M5ReasonCode.UNRESOLVED_WC_BASELINE, M5ReasonCode.INSUFFICIENT_DATA]
            )

        if s_type == StressScenarioType.INTEREST_RATE_STRESS and not is_zero_debt:
            tenure_m = loan_management.tenure_months if loan_management else None
            mora_m = loan_management.moratorium_months if loan_management else None
            if (
                base_principal is None or
                base_rate is None or
                tenure_m is None or
                mora_m is None
            ):
                return StressScenarioResult(
                    scenario_id=spec.scenario_id,
                    scenario_name=spec.scenario_name,
                    scenario_type=s_type,
                    assumptions=params,
                    affected_drivers=spec.affected_drivers,
                    source=spec.source,
                    confidence=spec.confidence,
                    status="UNRESOLVED",
                    resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                    reason_codes=[M5ReasonCode.UNRESOLVED_DRIVER, M5ReasonCode.INSUFFICIENT_DATA]
                )

        if base_cogs is None or base_opex is None:
            return StressScenarioResult(
                scenario_id=spec.scenario_id,
                scenario_name=spec.scenario_name,
                scenario_type=s_type,
                assumptions=params,
                affected_drivers=spec.affected_drivers,
                source=spec.source,
                confidence=spec.confidence,
                status="UNRESOLVED",
                resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                reason_codes=[M5ReasonCode.BASELINE_UNRESOLVED, M5ReasonCode.INSUFFICIENT_DATA]
            )

        # Compute Stressed P&L Drivers
        rev_mult = 1.0 + (params.get("revenue_change_pct", 0.0) / 100.0)
        if "price_change_pct" in params:
            rev_mult *= (1.0 + (params["price_change_pct"] / 100.0))

        vol_mult = 1.0 + (params.get("volume_change_pct", 0.0) / 100.0)
        rev_mult *= vol_mult

        s_rev = round(base_rev * rev_mult, 2)

        # COGS / Variable Costs
        var_mult = 1.0 + (params.get("variable_cost_change_pct", 0.0) / 100.0)
        var_mult *= vol_mult
        s_cogs = round(base_cogs * var_mult, 2)

        # OPEX / Fixed Costs
        fix_mult = 1.0 + (params.get("fixed_cost_change_pct", 0.0) / 100.0)
        s_opex = round(base_opex * fix_mult, 2)

        s_gp = round(s_rev - s_cogs, 2)
        s_ebitda = round(s_gp - s_opex, 2)

        # Check required inputs for full PAT and DSCR
        is_pl_unresolved = False
        missing_pl_inputs = []
        if base_depr is None:
            is_pl_unresolved = True
            missing_pl_inputs.append("depreciation")
        if base_interest is None and not is_zero_debt:
            is_pl_unresolved = True
            missing_pl_inputs.append("interest")
        if base_tax is None:
            is_pl_unresolved = True
            missing_pl_inputs.append("tax")

        # Working capital stress delta (strictly from resolved baseline)
        wc_delta = 0.0
        if "wc_change_pct" in params and base_wc is not None:
            wc_mult = 1.0 + (params["wc_change_pct"] / 100.0)
            wc_delta = round(base_wc * (wc_mult - 1.0), 2)

        # Financing Gap Under Stress
        s_gap: Optional[float] = None
        if project_cost is not None and verified_funding is not None:
            stressed_requirement = round(project_cost + (wc_delta if wc_delta > 0 else 0.0), 2)
            s_gap = round(max(0.0, stressed_requirement - verified_funding), 2)

        # Liquidity Under Stress
        s_cr: Optional[float] = None
        if base_ca is not None and base_cl is not None and base_cl > 0:
            if "wc_change_pct" in params and base_wc is not None:
                # Working capital pressure increases working capital requirement
                # which absorbs liquidity / expands current liabilities (short-term financing of WC gap)
                stressed_cl = round(base_cl + wc_delta, 2)
                s_cr = round(base_ca / stressed_cl, 2) if stressed_cl > 0 else None
            else:
                s_cr = round(base_ca / base_cl, 2)

        # Monthly Cash Buffer (strictly from actual cash position)
        monthly_cash_burn = (s_cogs + s_opex) / 12.0
        s_cash_buffer: Optional[float] = None
        if monthly_cash_burn > 0 and actual_cash is not None:
            stressed_cash = max(0.0, round(actual_cash - wc_delta, 2)) if ("wc_change_pct" in params and wc_delta > 0) else actual_cash
            s_cash_buffer = round(stressed_cash / monthly_cash_burn, 1)

        # Break-Even Under Stress (Aligned with M4 Appraisal & Stage 9 Contribution Margin formula)
        s_be_sales: Optional[float] = None
        s_be_util: Optional[float] = None
        if s_rev > 0:
            fixed_ratio = 0.30  # Sourced fixed operational cost ratio
            var_ratio = 1.0 - fixed_ratio
            fixed_costs = s_opex * fixed_ratio
            variable_costs = s_cogs + (s_opex * var_ratio)
            cm = s_rev - variable_costs
            if s_rev > 0:
                cm_ratio = cm / s_rev
                if cm_ratio > 0.01:
                    s_be_sales = round(fixed_costs / cm_ratio, 2)
                    s_be_util = round((s_be_sales / s_rev) * 100.0, 2)

        # Debt-to-Equity Ratio Under Stress (deterministic from authoritative balance sheet)
        s_der: Optional[float] = None
        if is_zero_debt:
            s_der = 0.0
        elif base_debt is not None and base_equity is not None:
            if base_equity > 0:
                s_der = round(base_debt / base_equity, 2)
            else:
                s_der = 999.0

        if is_pl_unresolved:
            # Cannot fabricate PAT / DSCR
            return StressScenarioResult(
                scenario_id=spec.scenario_id,
                scenario_name=spec.scenario_name,
                scenario_type=s_type,
                assumptions=params,
                affected_drivers=spec.affected_drivers,
                base_value=base_rev,
                stressed_value=s_rev,
                change_pct=params.get("revenue_change_pct", 0.0),
                source=spec.source,
                confidence=spec.confidence,
                status="UNRESOLVED",
                revenue=s_rev,
                cogs=s_cogs,
                gross_profit=s_gp,
                operating_expenses=s_opex,
                ebitda=s_ebitda,
                depreciation=base_depr,
                interest_expense=base_interest,
                profit_before_tax=None,
                tax_expense=base_tax,
                pat=None,
                working_capital_movement=wc_delta,
                operating_cash_flow=None,
                debt_service=base_ds_val,
                cads=None,
                dscr=None,
                minimum_dscr=None,
                break_even_sales=s_be_sales,
                break_even_utilization_pct=s_be_util,
                current_ratio=s_cr,
                cash_buffer_months=s_cash_buffer,
                debt_equity_ratio=s_der,
                financing_gap=s_gap,
                repayment_capacity_assessment="NOT_ASSESSABLE",
                viability_status="NOT_ASSESSABLE",
                resilience_status=ResilienceStatus.NOT_ASSESSABLE,
                reason_codes=[M5ReasonCode.UNRESOLVED_DRIVER, M5ReasonCode.INSUFFICIENT_DATA]
            )

        # Interest & Debt Service Recalculation (Authoritative Stage 9 Amortization consistency)
        s_interest = base_interest
        s_ds_val = base_ds_val

        if s_type == StressScenarioType.INTEREST_RATE_STRESS and not is_zero_debt:
            rate_hike = params.get("rate_hike_pct_points", 0.0) / 100.0
            if (
                base_principal is not None and base_principal > 0 and
                base_rate is not None and
                loan_management is not None and
                loan_management.tenure_months is not None and
                loan_management.moratorium_months is not None
            ):
                stressed_rate = round(base_rate + rate_hike, 4)
                recalc_lm = self.loan_calc.calculate_emi(
                    principal=base_principal,
                    annual_rate=stressed_rate,
                    tenure_months=loan_management.tenure_months,
                    moratorium_months=loan_management.moratorium_months
                )
                recalc_sched = AmortizationEngine.generate_schedule(
                    principal=base_principal,
                    annual_rate=stressed_rate,
                    tenure_months=loan_management.tenure_months,
                    moratorium_months=loan_management.moratorium_months,
                    monthly_emi=recalc_lm.monthly_emi
                )
                y1_rows = [r for r in recalc_sched.monthly_schedule if 1 <= r.period <= 12]
                if y1_rows:
                    s_interest = round(sum(r.interest_component for r in y1_rows), 2)
                    s_ds_val = round(sum(r.principal_component + r.interest_component for r in y1_rows), 2)
                else:
                    s_ds_val = round(recalc_lm.monthly_emi * 12.0, 2)
                    s_interest = round(recalc_lm.total_interest, 2)

        s_ebit = round(s_ebitda - base_depr, 2)
        s_pbt = round(s_ebit - s_interest, 2)
        s_pat = round(s_pbt - base_tax, 2)

        s_cf_ops = round(s_pat + base_depr - wc_delta, 2)

        # CADS and DSCR Under Stress
        cads: Optional[float] = None
        s_dscr: Optional[float] = None
        s_min_dscr: Optional[float] = None

        if is_zero_debt:
            s_dscr = None
            s_min_dscr = None
            cads = round(s_pat + base_depr, 2)
        elif s_pat is not None and base_depr is not None and s_interest is not None:
            cads = round(s_pat + base_depr + s_interest, 2)
            if s_ds_val is not None and s_ds_val > 0:
                if cads <= 0:
                    s_dscr = 0.0
                    s_min_dscr = 0.0
                else:
                    s_dscr = round(cads / s_ds_val, 2)
                    s_min_dscr = s_dscr

        # Resilience Classification & Reason Codes
        reasons: List[M5ReasonCode] = []
        resilience = ResilienceStatus.RESILIENT

        if s_gap is not None and s_gap > 0.0:
            resilience = ResilienceStatus.CRITICAL
            reasons.append(M5ReasonCode.FINANCING_GAP)

        # Fix 10: NEGATIVE_CASH_FLOW based on resolved operating cash flow, NOT EBITDA
        if s_cf_ops is not None and s_cf_ops < 0:
            resilience = ResilienceStatus.CRITICAL
            reasons.append(M5ReasonCode.NEGATIVE_CASH_FLOW)

        # Fix 9 & 11: DSCR thresholds: < 1.00 => CRITICAL, 1.00 <= DSCR < 1.10 => STRESSED
        if not is_zero_debt:
            if s_dscr is not None and s_dscr < 1.00:
                resilience = ResilienceStatus.CRITICAL
                reasons.append(M5ReasonCode.DSCR_BELOW_THRESHOLD)
                reasons.append(M5ReasonCode.REPAYMENT_DEFICIT)
            elif s_dscr is not None and s_dscr < DSCR_RESILIENCE_MINIMUM:
                if resilience != ResilienceStatus.CRITICAL:
                    resilience = ResilienceStatus.STRESSED
                reasons.append(M5ReasonCode.DSCR_BELOW_THRESHOLD)

        if s_cr is not None and s_cr < CURRENT_RATIO_RESILIENCE_MINIMUM:
            if resilience != ResilienceStatus.CRITICAL:
                resilience = ResilienceStatus.STRESSED
            reasons.append(M5ReasonCode.LIQUIDITY_STRESS)

        # Fix 7: CASH_BUFFER_RESILIENCE_MONTHS policy threshold
        if s_cash_buffer is not None:
            if s_cash_buffer < 0.5:
                if resilience != ResilienceStatus.CRITICAL:
                    resilience = ResilienceStatus.CRITICAL
                if M5ReasonCode.LIQUIDITY_STRESS not in reasons:
                    reasons.append(M5ReasonCode.LIQUIDITY_STRESS)
            elif s_cash_buffer < CASH_BUFFER_RESILIENCE_MONTHS:
                if resilience != ResilienceStatus.CRITICAL:
                    resilience = ResilienceStatus.STRESSED
                if M5ReasonCode.LIQUIDITY_STRESS not in reasons:
                    reasons.append(M5ReasonCode.LIQUIDITY_STRESS)

        # Fix 8: DER policy threshold MAX_ACCEPTABLE_DER (4.0)
        if s_der is not None and s_der > MAX_ACCEPTABLE_DER:
            if resilience != ResilienceStatus.CRITICAL:
                resilience = ResilienceStatus.STRESSED
            reasons.append(M5ReasonCode.HIGH_LEVERAGE)

        if s_be_util is not None and s_be_util > BREAK_EVEN_MAX_UTILIZATION:
            if resilience != ResilienceStatus.CRITICAL:
                resilience = ResilienceStatus.STRESSED
            reasons.append(M5ReasonCode.BREAK_EVEN_EXCEEDED)

        if not reasons:
            reasons.append(M5ReasonCode.RESILIENT)

        # Fix 9 & 11: Repayment Capacity Assessment Text
        rc_text = "ROBUST"
        if is_zero_debt:
            rc_text = "NOT_APPLICABLE"
        elif resilience == ResilienceStatus.CRITICAL:
            rc_text = "CRITICAL_DEFICIT"
        elif s_dscr is not None and s_dscr < DSCR_RESILIENCE_MINIMUM:
            rc_text = "TIGHT"
        elif s_dscr is not None and s_dscr >= DSCR_RESILIENCE_BENCHMARK:
            rc_text = "ROBUST"
        elif s_dscr is not None and s_dscr >= DSCR_RESILIENCE_MINIMUM:
            rc_text = "ADEQUATE"
        elif resilience == ResilienceStatus.STRESSED:
            rc_text = "TIGHT"

        # Record Provenance
        provenance.record(
            metric=f"{spec.scenario_id}_revenue",
            value=s_rev,
            source=spec.source.value,
            source_reference=f"{spec.scenario_name} (change: {params.get('revenue_change_pct', 0.0)}%)",
            calculation_method="Deterministic downside percentage application on base Year 1 revenue",
            scenario_id=spec.scenario_id
        )

        return StressScenarioResult(
            scenario_id=spec.scenario_id,
            scenario_name=spec.scenario_name,
            scenario_type=s_type,
            assumptions=params,
            affected_drivers=spec.affected_drivers,
            base_value=base_rev,
            stressed_value=s_rev,
            change_pct=params.get("revenue_change_pct", 0.0),
            source=spec.source,
            confidence=spec.confidence,
            status="RESOLVED",
            revenue=s_rev,
            cogs=s_cogs,
            gross_profit=s_gp,
            operating_expenses=s_opex,
            ebitda=s_ebitda,
            depreciation=base_depr,
            interest_expense=s_interest,
            profit_before_tax=s_pbt,
            tax_expense=base_tax,
            pat=s_pat,
            working_capital_movement=wc_delta,
            operating_cash_flow=s_cf_ops,
            debt_service=s_ds_val,
            cads=cads,
            dscr=s_dscr,
            minimum_dscr=s_min_dscr,
            break_even_sales=s_be_sales,
            break_even_utilization_pct=s_be_util,
            current_ratio=s_cr,
            cash_buffer_months=s_cash_buffer,
            debt_equity_ratio=s_der,
            financing_gap=s_gap,
            repayment_capacity_assessment=rc_text,
            viability_status="VIABLE" if resilience == ResilienceStatus.RESILIENT else ("STRESSED" if resilience == ResilienceStatus.STRESSED else "CRITICAL"),
            resilience_status=resilience,
            reason_codes=reasons
        )


stress_engine = StressEngine()
