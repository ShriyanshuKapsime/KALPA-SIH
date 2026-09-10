from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class FinanceModelInput(BaseModel):
    capex_equipment: float = 0.0
    capex_civil_works: float = 0.0
    working_capital_months: int = 3
    promoter_equity: float = 0.0
    expected_unit_price: float = 0.0
    expected_monthly_volume: float = 0.0


class FinancialProjections(BaseModel):
    total_project_cost: float = 0.0
    term_loan_required: float = 0.0
    eligible_subsidy_amount: float = 0.0
    projected_annual_ebitda: float = 0.0
    dscr: float = 0.0
    break_even_output: float = 0.0
