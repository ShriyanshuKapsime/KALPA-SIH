"""
Profitability Engine for Stage 9 Financial Engine.
Calculates deterministic monthly and annual Revenue, COGS, Gross Profit,
Operating Expenses, Operating Profit (EBITDA), and Net Cash Flow after Debt.
Enforces strict revenue priority and returns BENCHMARK_DATA_UNAVAILABLE if data is missing.
"""
from typing import Optional, Tuple, Dict, Any
from app.schemas.financial_analysis import (
    ProfitabilityProjection,
    CalculationStatus,
    LoanManagement,
    ProjectAssumptionsInput
)
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData


class ProfitabilityEngine:
    """
    Deterministic profitability modeling engine.
    """

    @staticmethod
    def calculate_profitability(
        project_assumptions: ProjectAssumptionsInput,
        loan_management: LoanManagement,
        benchmark_data: Optional[BenchmarkFinancialData] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> ProfitabilityProjection:
        """
        Calculates monthly and annual financial operating metrics with strict revenue priority,
        itemized OPEX construction, deterministic EBITDA (Revenue - COGS - OPEX), and PBT/PAT.
        """
        # 1. Determine Revenue Source based on strict priority
        monthly_revenue = None
        source = "BENCHMARK_DATABASE"

        # Priority 1: User expected monthly revenue
        if project_assumptions.expected_monthly_revenue is not None and project_assumptions.expected_monthly_revenue > 0:
            monthly_revenue = float(project_assumptions.expected_monthly_revenue)
            source = "USER_INPUT"
        # Priority 2: User expected monthly units * unit price
        elif (
            project_assumptions.expected_monthly_units is not None and project_assumptions.expected_monthly_units > 0 and
            project_assumptions.expected_unit_price is not None and project_assumptions.expected_unit_price > 0
        ):
            monthly_revenue = float(project_assumptions.expected_monthly_units) * float(project_assumptions.expected_unit_price)
            source = "USER_INPUT"
        # Priority 3: Benchmark Database
        elif benchmark_data is not None:
            unit_econ = benchmark_data.unit_economics or {}
            raw_bm = benchmark_data.raw_benchmark or {}
            raw_unit_econ = raw_bm.get("unit_economics", {})

            # 3A. Retail Unit Economics (e.g. daily_sarees_sold * average_saree_price_inr)
            daily_qty = unit_econ.get("daily_sarees_sold") or raw_unit_econ.get("daily_sarees_sold") or unit_econ.get("daily_units_sold")
            avg_price = unit_econ.get("average_saree_price_inr") or raw_unit_econ.get("average_saree_price_inr") or unit_econ.get("average_price_inr")

            daily_turnover = unit_econ.get("daily_turnover_inr") or raw_unit_econ.get("daily_turnover_inr")
            if daily_turnover is None and unit_econ.get("daily_footfall") and unit_econ.get("average_bill_value_inr"):
                daily_turnover = float(unit_econ["daily_footfall"]) * float(unit_econ["average_bill_value_inr"])

            if daily_qty is not None and avg_price is not None and float(daily_qty) > 0 and float(avg_price) > 0:
                daily_sales = float(daily_qty) * float(avg_price)
                # Standard retail operating days policy: 26 days/month
                op_days = float(getattr(project_assumptions, "operating_days", None) or 26.0)
                monthly_revenue = daily_sales * op_days
                source = "BENCHMARK_UNIT_ECONOMICS"
            elif daily_turnover is not None and float(daily_turnover) > 0:
                op_days = float(getattr(project_assumptions, "operating_days", None) or 26.0)
                monthly_revenue = float(daily_turnover) * op_days
                source = "BENCHMARK_UNIT_ECONOMICS"
            # 3B. Agro / Processing Unit Economics
            elif "capacity_per_day_kg" in unit_econ and "processing_charge_per_kg" in unit_econ:
                cap_day = float(unit_econ["capacity_per_day_kg"])
                chg_kg = float(unit_econ["processing_charge_per_kg"])
                operating_days = float(getattr(project_assumptions, "operating_days", None) or 25.0)
                monthly_revenue = cap_day * chg_kg * operating_days
                source = "BENCHMARK_UNIT_ECONOMICS"
            # 3C. Working Capital Turnover Basis
            elif benchmark_data.typical_working_capital_monthly_inr:
                wc_monthly = float(benchmark_data.typical_working_capital_monthly_inr)
                op_ratio = max(0.5, min(0.95, float(benchmark_data.operating_cost_ratio)))
                monthly_revenue = wc_monthly / op_ratio
                source = "BENCHMARK_WORKING_CAPITAL_TURNOVER"
            else:
                monthly_revenue = (benchmark_data.typical_capex_inr or 500000.0) * 0.20
                source = "BENCHMARK_CAPEX_RATIO"

        # Priority 4: Unavailable
        if monthly_revenue is None or monthly_revenue <= 0:
            return ProfitabilityProjection(
                status=CalculationStatus.BENCHMARK_DATA_UNAVAILABLE,
                source="BENCHMARK_DATA_UNAVAILABLE",
                notes="Business-specific benchmark data or user revenue assumptions are required for profitability estimation."
            )

        monthly_revenue = round(monthly_revenue, 2)
        annual_revenue = round(monthly_revenue * 12.0, 2)

        # 2. Margin & Cost Parameters
        if benchmark_data:
            gross_margin_pct = float(benchmark_data.gross_margin_pct)
            net_margin_pct = float(benchmark_data.net_margin_pct)
            cogs_pct = float(benchmark_data.cogs_percentage)
            cost_struct = benchmark_data.cost_structure_pct or {}
            op_cost_ratio = float(benchmark_data.operating_cost_ratio or 0.77)
        else:
            gross_margin_pct = 30.0
            net_margin_pct = 18.0
            cogs_pct = 70.0
            cost_struct = {}
            op_cost_ratio = 0.80

        # Ensure complementary COGS and Gross Margin: 100 - Gross Margin = COGS%
        cogs_pct = max(5.0, min(95.0, round(100.0 - gross_margin_pct, 1)))

        # 3. Calculate COGS & Gross Profit
        monthly_cogs = round(monthly_revenue * (cogs_pct / 100.0), 2)
        annual_cogs = round(monthly_cogs * 12.0, 2)
        monthly_gross_profit = round(monthly_revenue - monthly_cogs, 2)
        annual_gross_profit = round(annual_revenue - annual_cogs, 2)

        # 4. Construct Itemized Operating Expenses (OPEX)
        # Never calculate OPEX as merely Gross Profit - assumed EBITDA.
        # Construct OPEX from verified cost structure or evidenced cost ratio.
        itemized_opex: Dict[str, float] = {}
        monthly_opex: float = 0.0

        if cost_struct:
            # Separate procurement/COGS key from OPEX line items
            cogs_keys = [k for k in cost_struct.keys() if "inventory" in k or "purchase" in k or "raw_material" in k]
            opex_keys = [k for k in cost_struct.keys() if k not in cogs_keys]

            total_opex_pct = sum(float(cost_struct[k]) for k in opex_keys)

            # Determine whether cost_struct percentages are relative to revenue or relative to total operating costs
            total_cost_pct = sum(float(v) for v in cost_struct.values())
            if total_cost_pct > 0 and op_cost_ratio > 0:
                # If total cost percentages sum to 100%, total operating cost = revenue * op_cost_ratio
                total_monthly_operating_cost = round(monthly_revenue * op_cost_ratio, 2)
                # OPEX pool = total operating costs - monthly COGS
                opex_pool = max(0.0, round(total_monthly_operating_cost - monthly_cogs, 2))
                if opex_pool > 0 and total_opex_pct > 0:
                    for k in opex_keys:
                        pct_weight = float(cost_struct[k]) / total_opex_pct
                        item_val = round(opex_pool * pct_weight, 2)
                        itemized_opex[k] = item_val
                    monthly_opex = round(sum(itemized_opex.values()), 2)
                else:
                    # Fallback directly to opex percentages
                    for k in opex_keys:
                        item_val = round(monthly_revenue * (float(cost_struct[k]) / 100.0), 2)
                        itemized_opex[k] = item_val
                    monthly_opex = round(sum(itemized_opex.values()), 2)
            else:
                for k in opex_keys:
                    item_val = round(monthly_revenue * (float(cost_struct[k]) / 100.0), 2)
                    itemized_opex[k] = item_val
                monthly_opex = round(sum(itemized_opex.values()), 2)
        else:
            # Generic verified operating expense ratio fallback
            # OPEX ratio = max(0.05, (1.0 - (cogs_pct / 100.0)) - (net_margin_pct / 100.0))
            derived_opex_ratio = max(0.05, round(op_cost_ratio - (cogs_pct / 100.0), 4))
            monthly_opex = round(monthly_revenue * derived_opex_ratio, 2)
            itemized_opex["general_operating_expenses"] = monthly_opex

        annual_opex = round(monthly_opex * 12.0, 2)

        # 5. EBITDA (Operating Profit) = Gross Profit - Operating Expenses
        # Critical Fix: net_margin_pct is NEVER used as EBITDA margin.
        monthly_operating_profit = round(monthly_gross_profit - monthly_opex, 2)
        annual_operating_profit = round(monthly_operating_profit * 12.0, 2)
        operating_margin_pct = round((monthly_operating_profit / monthly_revenue) * 100.0, 2) if monthly_revenue > 0 else 0.0

        # 6. Depreciation, Interest, PBT, Tax, and PAT
        # Sourced Depreciation from CapEx (straight line 10% annual baseline if capex known)
        typ_capex = benchmark_data.typical_capex_inr if benchmark_data else None
        annual_depr = round(float(typ_capex) * 0.10, 2) if typ_capex else None
        monthly_depr = round(annual_depr / 12.0, 2) if annual_depr is not None else None

        # Interest & Debt Service from loan management
        monthly_debt_service = float(loan_management.monthly_emi) if loan_management else 0.0
        annual_debt_service = round(monthly_debt_service * 12.0, 2)

        monthly_interest = 0.0
        if loan_management and loan_management.tenure_months > 0 and loan_management.principal > 0:
            monthly_interest = round(max(0.0, monthly_debt_service - (loan_management.principal / loan_management.tenure_months)), 2)
        annual_interest = round(monthly_interest * 12.0, 2)

        # Profit Before Tax (PBT) = EBITDA - Depreciation - Interest
        depr_deduction = monthly_depr or 0.0
        monthly_pbt = round(monthly_operating_profit - depr_deduction - monthly_interest, 2)
        annual_pbt = round(monthly_pbt * 12.0, 2)

        # Tax & Profit After Tax (PAT)
        # Authoritative tax regime resolution per INDIA_INCOME_TAX_AY_2026_27
        user_in = user_inputs or {}
        from app.services.financial_engine.projection.tax_policy import tax_policy_resolver

        tax_res = tax_policy_resolver.resolve_tax(
            pbt=annual_pbt,
            annual_revenue=annual_revenue,
            business_constitution=getattr(project_assumptions, "business_constitution", None) or user_in.get("business_constitution") or user_in.get("constitution"),
            sector=getattr(project_assumptions, "sector", None) or user_in.get("sector"),
            category=getattr(project_assumptions, "category", None) or user_in.get("category"),
            user_inputs=user_in,
        )
        annual_tax = tax_res.annual_tax_expense
        monthly_tax = round(annual_tax / 12.0, 2)
        monthly_pat = round(monthly_pbt - monthly_tax, 2)
        annual_pat = round(monthly_pat * 12.0, 2)
        tax_rate = tax_res.effective_tax_rate
        tax_status = tax_res.tax_regime
        calculated_net_margin = round((annual_pat / annual_revenue) * 100.0, 2) if annual_revenue > 0 else 0.0

        # 7. Cash Flow after Debt Service
        monthly_net_cash = round(monthly_operating_profit - monthly_debt_service, 2)
        annual_net_cash = round(annual_operating_profit - annual_debt_service, 2)

        return ProfitabilityProjection(
            status=CalculationStatus.CALCULATED,
            monthly_revenue=monthly_revenue,
            annual_revenue=annual_revenue,
            monthly_cogs=monthly_cogs,
            annual_cogs=annual_cogs,
            monthly_gross_profit=monthly_gross_profit,
            annual_gross_profit=annual_gross_profit,
            gross_margin_percentage=round(gross_margin_pct, 1),
            monthly_operating_expenses=monthly_opex,
            annual_operating_expenses=annual_opex,
            itemized_opex=itemized_opex,
            monthly_operating_profit=monthly_operating_profit,
            annual_operating_profit=annual_operating_profit,
            monthly_ebitda=monthly_operating_profit,
            annual_ebitda=annual_operating_profit,
            operating_margin_percentage=operating_margin_pct,
            monthly_depreciation=monthly_depr,
            annual_depreciation=annual_depr,
            monthly_interest=monthly_interest,
            annual_interest=annual_interest,
            monthly_pbt=monthly_pbt,
            annual_pbt=annual_pbt,
            monthly_pat=monthly_pat,
            annual_pat=annual_pat,
            calculated_net_margin_pct=calculated_net_margin,
            benchmark_net_margin_pct=round(net_margin_pct, 1),
            tax_status=tax_status,
            tax_rate_pct=tax_rate,
            monthly_debt_service=monthly_debt_service,
            annual_debt_service=annual_debt_service,
            monthly_net_cash_after_debt=monthly_net_cash,
            annual_net_cash_after_debt=annual_net_cash,
            source=source,
            notes="Deterministic projection based on verified margin, unit economics, and cost structure benchmarks."
        )


# Global singleton instance
profitability_engine = ProfitabilityEngine()
