"""
Financial Calculation Registry (Milestone 1 Foundation).
Deterministic formulas. No LLM involvement.
Establishes the architecture for future milestones.
"""
from typing import Dict, Any, Optional
import math


def calc_project_cost_from_margin(margin_capital: float, margin_ratio: float = 0.10) -> float:
    if margin_capital <= 0 or margin_ratio <= 0:
        return 0.0
    return round(margin_capital / margin_ratio, 2)


def calc_loan_amount(project_cost: float, margin_ratio: float = 0.10) -> float:
    return round(project_cost * (1.0 - margin_ratio), 2)


def calc_promoter_margin(project_cost: float, margin_ratio: float = 0.10) -> float:
    return round(project_cost * margin_ratio, 2)


def calc_revenue_retail(monthly_transactions: float, average_ticket: float) -> float:
    return round(monthly_transactions * average_ticket, 2)


def calc_revenue_manufacturing(
    installed_capacity: float, operating_days: float,
    utilization: float, selling_price: float
) -> float:
    return round(installed_capacity * operating_days * (utilization / 100.0) * selling_price, 2)


def calc_revenue_service(jobs_per_day: float, operating_days: float, average_realization: float) -> float:
    return round(jobs_per_day * operating_days * average_realization, 2)


def calc_cogs(revenue: float, gross_margin_pct: float) -> float:
    return round(revenue * (1.0 - gross_margin_pct / 100.0), 2)


def calc_gross_profit(revenue: float, cogs: float) -> float:
    return round(revenue - cogs, 2)


def calc_operating_expenses(**costs) -> float:
    return round(sum(v for v in costs.values() if v is not None and v > 0), 2)


def calc_ebitda(gross_profit: float, operating_expenses: float) -> float:
    return round(gross_profit - operating_expenses, 2)


def calc_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    if annual_rate <= 0:
        return round(principal / tenure_months, 2)
    r = annual_rate / 12.0
    emi = principal * r * math.pow(1 + r, tenure_months) / (math.pow(1 + r, tenure_months) - 1)
    return round(emi, 2)


def calc_dscr(annual_operating_cash_flow: float, annual_debt_service: float) -> Optional[float]:
    if annual_debt_service <= 0:
        return None
    return round(annual_operating_cash_flow / annual_debt_service, 4)


def calc_break_even_revenue(fixed_costs: float, contribution_margin_ratio: float) -> Optional[float]:
    if contribution_margin_ratio <= 0:
        return None
    return round(fixed_costs / contribution_margin_ratio, 2)


def calc_working_capital(
    monthly_cogs: float, inventory_days: int = 30,
    receivable_days: int = 0, payable_days: int = 0
) -> float:
    daily_cogs = monthly_cogs / 30.0
    wc = daily_cogs * (inventory_days + receivable_days - payable_days)
    return round(max(0, wc), 2)


# ─── Calculation Registry ────────────────────────────────────────────────────
# Maps calculation names to functions for future extensibility.
CALCULATION_REGISTRY: Dict[str, Any] = {
    "PROJECT_COST": calc_project_cost_from_margin,
    "PROMOTER_MARGIN": calc_promoter_margin,
    "LOAN_AMOUNT": calc_loan_amount,
    "REVENUE_RETAIL": calc_revenue_retail,
    "REVENUE_MANUFACTURING": calc_revenue_manufacturing,
    "REVENUE_SERVICE": calc_revenue_service,
    "COGS": calc_cogs,
    "GROSS_PROFIT": calc_gross_profit,
    "OPERATING_EXPENSES": calc_operating_expenses,
    "EBITDA": calc_ebitda,
    "EMI": calc_emi,
    "DSCR": calc_dscr,
    "BREAK_EVEN_REVENUE": calc_break_even_revenue,
    "WORKING_CAPITAL": calc_working_capital,
}
