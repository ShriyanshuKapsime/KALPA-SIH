"""
Multi-Year Working Capital Projection Engine for Milestone 3.
Projects inventory, receivables, payables, and Net Working Capital changes over time.
Propagates uncertainty faithfully without inventing turnover days.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    WorkingCapitalProjection,
    WorkingCapitalYear,
    WorkingCapitalAnalysis,
    RevenueProjection,
    CostProjection,
    ProjectCostAnalysis,
)
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData


class WorkingCapitalProjectionEngine:
    """
    Projects multi-year working capital based on evidenced turnover days and operating cycles.
    """

    @staticmethod
    def project(
        revenue_projection: RevenueProjection,
        cost_projection: CostProjection,
        working_capital_analysis: Optional[WorkingCapitalAnalysis] = None,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        benchmark_data: Optional[BenchmarkFinancialData] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        assumptions_map: Optional[Dict[str, Any]] = None,
    ) -> WorkingCapitalProjection:
        """
        Calculates working capital requirements and annual delta for each projection year.
        """
        user_in = user_inputs or {}
        asm_map = assumptions_map or {}

        def get_val(key: str) -> Optional[float]:
            if key in user_in and user_in[key] is not None:
                try:
                    return float(user_in[key])
                except (ValueError, TypeError):
                    pass
            if key in asm_map and asm_map[key] is not None:
                val = asm_map[key]
                raw = getattr(val, "value", val)
                if raw is not None:
                    try:
                        return float(raw)
                    except (ValueError, TypeError):
                        pass
            return None

        # Extract turnover days
        inv_days = get_val("inventory_days")
        if inv_days is None and benchmark_data and hasattr(benchmark_data, "inventory_turnover_days"):
            b_inv = getattr(benchmark_data, "inventory_turnover_days")
            if b_inv is not None:
                inv_days = float(b_inv)

        rec_days = get_val("receivable_days")
        if rec_days is None and benchmark_data and hasattr(benchmark_data, "receivable_days"):
            b_rec = getattr(benchmark_data, "receivable_days")
            if b_rec is not None:
                rec_days = float(b_rec)

        pay_days = get_val("payable_days")
        if pay_days is None and benchmark_data and hasattr(benchmark_data, "payable_days"):
            b_pay = getattr(benchmark_data, "payable_days")
            if b_pay is not None:
                pay_days = float(b_pay)

        # Baseline M2 values
        m2_inv = working_capital_analysis.inventory_requirement if working_capital_analysis else None
        if m2_inv is None and project_cost_analysis and project_cost_analysis.opening_inventory is not None:
            m2_inv = project_cost_analysis.opening_inventory

        m2_rec = working_capital_analysis.receivable_requirement if working_capital_analysis else None
        m2_pay = working_capital_analysis.payable_credit if working_capital_analysis else None
        m2_cash_buf = working_capital_analysis.operating_cash_buffer if working_capital_analysis else None

        # Year 0 initial working capital baseline (at Day 0 inception prior to operations)
        # Opening inventory is funded via project cost.
        y0_inv: Optional[float] = None
        if project_cost_analysis and project_cost_analysis.opening_inventory is not None:
            y0_inv = float(project_cost_analysis.opening_inventory)
        elif m2_inv is not None:
            y0_inv = float(m2_inv)

        # Receivables & Payables at Day 0: 0.0 for new greenfield projects unless existing business specified
        is_greenfield = user_in.get("is_greenfield", True) if not user_in.get("is_existing_business") else False
        y0_rec: Optional[float] = None
        if "opening_receivables" in user_in and user_in["opening_receivables"] is not None:
            y0_rec = float(user_in["opening_receivables"])
        elif is_greenfield:
            y0_rec = 0.0

        y0_pay: Optional[float] = None
        if "opening_payables" in user_in and user_in["opening_payables"] is not None:
            y0_pay = float(user_in["opening_payables"])
        elif is_greenfield:
            y0_pay = 0.0

        y0_nwc: Optional[float] = None
        if y0_inv is not None and y0_rec is not None and y0_pay is not None:
            y0_nwc = round(y0_inv + y0_rec - y0_pay, 2)

        prev_nwc: Optional[float] = y0_nwc
        years: List[WorkingCapitalYear] = []

        rev_map = {l.year: l.revenue for l in revenue_projection.years} if (revenue_projection and hasattr(revenue_projection, 'years') and revenue_projection.years) else {}
        cogs_map = {l.year: l.cogs for l in cost_projection.years} if (cost_projection and hasattr(cost_projection, 'years') and cost_projection.years) else {}
        rev_y1 = rev_map.get(1)
        cogs_y1 = cogs_map.get(1)

        for r_line in revenue_projection.years:
            y = r_line.year
            rev = r_line.revenue
            cogs = cogs_map.get(y)

            # 1. Inventory
            inv_val: Optional[float] = None
            if inv_days is not None:
                if inv_days == 0:
                    inv_val = 0.0
                elif cogs is not None and cogs > 0:
                    inv_val = round((cogs / 365.0) * inv_days, 2)
            elif m2_inv is not None:
                if cogs is not None and cogs_y1 is not None and cogs_y1 > 0:
                    inv_val = round(m2_inv * (cogs / cogs_y1), 2)
                else:
                    inv_val = round(m2_inv, 2)

            # 2. Receivables
            rec_val: Optional[float] = None
            if rec_days is not None:
                if rec_days == 0:
                    rec_val = 0.0
                elif rev is not None and rev > 0:
                    rec_val = round((rev / 365.0) * rec_days, 2)
            elif m2_rec is not None:
                if rev is not None and rev_y1 is not None and rev_y1 > 0:
                    rec_val = round(m2_rec * (rev / rev_y1), 2)
                else:
                    rec_val = round(m2_rec, 2)
            else:
                rec_val = 0.0

            # 3. Payables
            pay_val: Optional[float] = None
            if pay_days is not None:
                if pay_days == 0:
                    pay_val = 0.0
                elif cogs is not None and cogs > 0:
                    pay_val = round((cogs / 365.0) * pay_days, 2)
            elif m2_pay is not None:
                if cogs is not None and cogs_y1 is not None and cogs_y1 > 0:
                    pay_val = round(m2_pay * (cogs / cogs_y1), 2)
                else:
                    pay_val = round(m2_pay, 2)
            else:
                pay_val = 0.0

            # 4. Operating Cycle Days
            op_cycle: Optional[float] = None
            if inv_days is not None and rec_days is not None and pay_days is not None:
                op_cycle = round(inv_days + rec_days - pay_days, 1)
            elif inv_days is not None and rec_days is not None:
                # payable_days unknown — cannot compute full CCC
                op_cycle = None

            # 5. Net Working Capital
            # If ANY component is unknown, totals must remain unknown (not silently zeroed)
            ca: Optional[float] = None
            cl: Optional[float] = None
            nwc: Optional[float] = None
            delta_nwc: Optional[float] = None

            all_ca_known = (inv_val is not None and rec_val is not None)
            all_cl_known = (pay_val is not None)

            if all_ca_known:
                ca = round(inv_val + rec_val, 2)
            elif inv_val is not None:
                ca = inv_val  # Partial — only inventory known
            elif rec_val is not None:
                ca = rec_val  # Partial — only receivables known

            if all_cl_known:
                cl = round(pay_val, 2)

            if all_ca_known and all_cl_known:
                nwc = round((inv_val + rec_val) - pay_val, 2)
                if prev_nwc is not None:
                    delta_nwc = round(nwc - prev_nwc, 2)
                prev_nwc = nwc
            else:
                # NWC cannot be fully determined — propagate None
                prev_nwc = None

            # Status determination
            status = "RESOLVED"
            if inv_val is None or rec_val is None or pay_val is None:
                status = "PARTIALLY_DERIVED"
            if inv_val is None and rec_val is None and pay_val is None:
                status = "UNKNOWN"

            years.append(
                WorkingCapitalYear(
                    year=y,
                    inventory=inv_val,
                    receivables=rec_val,
                    payables=pay_val,
                    operating_cash_buffer=m2_cash_buf,
                    current_assets=ca,
                    current_liabilities=cl,
                    net_working_capital=nwc,
                    change_in_working_capital=delta_nwc,
                    operating_cycle_days=op_cycle,
                    status=status
                )
            )

        return WorkingCapitalProjection(
            status="RESOLVED" if all(y.status == "RESOLVED" for y in years) else "PARTIALLY_DERIVED",
            years=years,
            methodology="TURNOVER_DAYS",
            notes="Working capital projected from turnover days and revenue/COGS progression."
        )


working_capital_projection_engine = WorkingCapitalProjectionEngine()
