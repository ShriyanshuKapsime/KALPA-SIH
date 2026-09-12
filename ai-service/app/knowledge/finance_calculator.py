import math
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.knowledge import (
    FinancialCalculationRules,
    AmortizationRowSchema,
    FinancialFeasibilityResult,
    FinancialBenchmarkSchema,
    GovernmentSchemeSchema,
)


def calculate_standard_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    """
    Standard reducing balance EMI calculation:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    where r = annual_rate_pct / (12 * 100)
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    if annual_rate_pct <= 0:
        return round(principal / tenure_months, 2)

    r = (annual_rate_pct / 100.0) / 12.0
    numerator = principal * r * math.pow(1 + r, tenure_months)
    denominator = math.pow(1 + r, tenure_months) - 1.0
    if denominator == 0:
        return round(principal / tenure_months, 2)
    return round(numerator / denominator, 2)


def generate_amortization_schedule(
    principal: float,
    annual_rate_pct: float,
    tenure_months: int,
    moratorium_months: int = 0,
    moratorium_policy: str = "principal_only",
    months_to_generate: int = 12,
) -> Tuple[List[AmortizationRowSchema], float, float]:
    """
    Generates deterministic amortization schedule with moratorium support.
    Returns: (schedule_rows, total_interest_payable, total_payment)
    """
    if principal <= 0 or tenure_months <= 0:
        return [], 0.0, 0.0

    r = (annual_rate_pct / 100.0) / 12.0
    repayment_months = max(1, tenure_months - moratorium_months)
    regular_emi = calculate_standard_emi(principal, annual_rate_pct, repayment_months)

    rows: List[AmortizationRowSchema] = []
    balance = float(principal)
    total_interest = 0.0
    total_paid = 0.0

    limit = min(tenure_months, months_to_generate)
    for m in range(1, limit + 1):
        opening = balance
        interest_payment = round(opening * r, 2)
        total_interest += interest_payment

        if m <= moratorium_months and moratorium_policy == "principal_only":
            # Principal deferred; only interest is serviced
            principal_payment = 0.0
            installment = interest_payment
            closing = opening
        else:
            # Regular EMI amortization
            installment = min(regular_emi, opening + interest_payment)
            principal_payment = round(installment - interest_payment, 2)
            if principal_payment < 0:
                principal_payment = 0.0
            closing = round(max(0.0, opening - principal_payment), 2)

        total_paid += installment
        rows.append(
            AmortizationRowSchema(
                month=m,
                opening_balance=opening,
                principal_payment=principal_payment,
                interest_payment=interest_payment,
                total_installment=installment,
                closing_balance=closing,
            )
        )
        balance = closing
        if balance <= 0.01:
            break

    # Calculate full tenure totals
    if moratorium_months > 0 and moratorium_policy == "principal_only":
        full_moratorium_interest = round(principal * r * moratorium_months, 2)
        full_regular_interest = round((regular_emi * repayment_months) - principal, 2)
        est_total_interest = round(full_moratorium_interest + full_regular_interest, 2)
        est_total_payment = round(principal + est_total_interest, 2)
    else:
        full_regular_emi = calculate_standard_emi(principal, annual_rate_pct, tenure_months)
        est_total_payment = round(full_regular_emi * tenure_months, 2)
        est_total_interest = round(est_total_payment - principal, 2)

    return rows, est_total_interest, est_total_payment


def calculate_baseline_rules(
    project_cost: float,
    available_margin: Optional[float] = None,
    scheme_override: Optional[GovernmentSchemeSchema] = None,
) -> FinancialCalculationRules:
    """
    Deterministic rule-based baseline finance calculation per SIH Problem Statement.
    Zero LLM calls.
    """
    cost = max(0.0, float(project_cost))
    is_micro = cost <= 140000.0

    if scheme_override:
        rule_name = scheme_override.scheme_id
        rate = scheme_override.financial_terms.interest_rate_pct or (6.5 if is_micro else 8.0)
        tenure = scheme_override.financial_terms.tenure_months or (36 if is_micro else 84)
        moratorium = scheme_override.financial_terms.moratorium_months or (3 if is_micro else 6)
        min_margin_pct = scheme_override.financial_terms.min_promoter_contribution_pct or 10.0
        max_loan_cap = scheme_override.financial_terms.max_loan_amount or (125000.0 if is_micro else 4500000.0)
    elif is_micro:
        rule_name = "SIH_BASELINE_MICRO_FINANCE"
        rate = 6.5
        tenure = 36
        moratorium = 3
        min_margin_pct = 10.0
        max_loan_cap = 125000.0
    else:
        rule_name = "SIH_BASELINE_TERM_LOAN"
        rate = 8.0
        tenure = 84
        moratorium = 6
        min_margin_pct = 10.0
        max_loan_cap = 4500000.0

    # Determine promoter contribution
    if available_margin is not None and available_margin > 0:
        promoter_amount = float(available_margin)
        promoter_pct = round((promoter_amount / cost) * 100.0, 2) if cost > 0 else 10.0
        if promoter_pct < min_margin_pct:
            promoter_amount = round(cost * (min_margin_pct / 100.0), 2)
            promoter_pct = min_margin_pct
    else:
        promoter_amount = round(cost * (min_margin_pct / 100.0), 2)
        promoter_pct = min_margin_pct

    loan_required = max(0.0, cost - promoter_amount)
    loan_amount = min(loan_required, max_loan_cap)

    repayment_months = max(1, tenure - moratorium)
    monthly_emi = calculate_standard_emi(loan_amount, rate, repayment_months)

    schedule_rows, total_interest, total_payment = generate_amortization_schedule(
        principal=loan_amount,
        annual_rate_pct=rate,
        tenure_months=tenure,
        moratorium_months=moratorium,
        moratorium_policy="principal_only",
        months_to_generate=12,
    )

    return FinancialCalculationRules(
        baseline_rule_applied=rule_name,
        is_micro_enterprise=is_micro,
        project_cost=cost,
        promoter_contribution_amount=promoter_amount,
        promoter_contribution_pct=promoter_pct,
        loan_amount=loan_amount,
        interest_rate_pct=rate,
        tenure_months=tenure,
        moratorium_months=moratorium,
        moratorium_policy="principal_only",
        monthly_emi=monthly_emi,
        total_interest_payable=total_interest,
        total_payment=total_payment,
        first_year_schedule=schedule_rows,
    )


def evaluate_financial_feasibility(
    business_node_id: str,
    project_cost: float,
    rules: FinancialCalculationRules,
    benchmark: Optional[FinancialBenchmarkSchema] = None,
) -> FinancialFeasibilityResult:
    """
    Evaluates debt service coverage ratio (DSCR), breakeven, and feasibility status deterministically.
    """
    cost = max(1.0, project_cost)
    emi = rules.monthly_emi
    loan = rules.loan_amount
    margin = rules.promoter_contribution_amount

    # Estimate monthly revenue and net profit from benchmarks or heuristics
    if benchmark and benchmark.margins:
        typical_net_margin = benchmark.margins.net_margin_pct_typical / 100.0
        # Estimate monthly revenue based on capital turnover (typically 2.0x - 3.5x annual capex turnover)
        est_monthly_revenue = round((cost * 2.4) / 12.0, 2)
        est_monthly_net_profit = round(est_monthly_revenue * typical_net_margin, 2)
        breakeven_months = benchmark.timelines.breakeven_months
        payback_months = benchmark.timelines.payback_period_months
    else:
        est_monthly_revenue = round((cost * 2.2) / 12.0, 2)
        est_monthly_net_profit = round(est_monthly_revenue * 0.18, 2)
        breakeven_months = 4
        payback_months = 24

    # Calculate Debt Service Coverage Ratio (DSCR): (Monthly Net Profit + EMI) / EMI
    if emi > 0:
        dscr = round((est_monthly_net_profit + emi) / emi, 2)
    else:
        dscr = 5.0

    # Risk evaluation
    risk_notes: List[str] = []
    if dscr >= 1.50:
        feasibility_status = "FEASIBLE"
    elif dscr >= 1.15:
        feasibility_status = "CONDITIONAL"
        risk_notes.append("Moderate DSCR buffer; tight cash flow during low-season months.")
    else:
        feasibility_status = "HIGH_RISK"
        risk_notes.append("Low DSCR (<1.15); loan repayment may face strain without higher promoter equity.")

    if rules.promoter_contribution_pct < 10.0:
        risk_notes.append("Promoter equity is below standard 10% threshold.")

    return FinancialFeasibilityResult(
        business_node_id=business_node_id,
        project_cost=cost,
        promoter_contribution=margin,
        loan_amount=loan,
        monthly_emi=emi,
        estimated_monthly_revenue=est_monthly_revenue,
        estimated_monthly_net_profit=est_monthly_net_profit,
        dscr_ratio=dscr,
        breakeven_months=breakeven_months,
        payback_period_months=payback_months,
        feasibility_status=feasibility_status,
        risk_notes=risk_notes,
        baseline_rule_applied=rules.baseline_rule_applied,
    )
