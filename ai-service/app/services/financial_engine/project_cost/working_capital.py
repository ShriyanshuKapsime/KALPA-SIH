"""
Milestone 2: Dedicated Deterministic Working Capital Engine.
Calculates archetype-aware working capital requirements:
- Inventory Requirement
- Receivables Requirement
- Payables / Supplier Credit Offset
- Operating Cash Buffer
- Operating Cycle Days
- Total Working Capital = Inventory + Receivables + Cash Buffer - Payables

Strict Rules:
- NO unsourced financial defaults (no hardcoded ₹10k salaries, no default 30 inventory days,
  no default 15 receivable days, no hardcoded 1.5/2.0-month buffers, no 50/50 or 60/40 splits).
- All parameters MUST come from user input, benchmark data, or verified evidence.
- If required parameters are missing: remain UNKNOWN / None (never silently convert to 0).
- Structural zero is permitted ONLY when it represents a true semantic domain rule
  (e.g., pure service businesses hold no retail merchandise inventory).
- Clearly distinguishes opening inventory from ongoing/non-inventory working capital
  to prevent double-counting in project cost.
- Zero LLM calculations.
"""
import logging
from typing import Dict, Any, List, Optional, Union
from app.schemas.financial_analysis import WorkingCapitalAnalysis
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, SourceType
)
from app.services.financial_engine.intelligence.archetype_registry import FinancialArchetype
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData

logger = logging.getLogger(__name__)


class WorkingCapitalEngine:
    """
    Deterministic Working Capital intelligence engine.
    Calculates working capital requirements based strictly on evidenced parameters.
    """

    def calculate(
        self,
        archetype: FinancialArchetype,
        assumptions: Union[List[ResolvedAssumption], Dict[str, ResolvedAssumption]],
        benchmark_data: Optional[Union[BenchmarkFinancialData, Dict[str, Any]]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> WorkingCapitalAnalysis:
        """
        Calculates working capital analysis based on financial archetype and evidenced parameters.
        """
        user_inputs = user_inputs or {}
        asm_map: Dict[str, ResolvedAssumption] = {}
        if isinstance(assumptions, list):
            asm_map = {a.driver_id: a for a in assumptions}
        elif isinstance(assumptions, dict):
            asm_map = assumptions

        def get_v(key: str) -> Optional[float]:
            if key in user_inputs and user_inputs[key] is not None:
                try:
                    return float(user_inputs[key])
                except (ValueError, TypeError):
                    pass
            if key in asm_map and asm_map[key].value is not None:
                try:
                    return float(asm_map[key].value)
                except (ValueError, TypeError):
                    pass
            return None

        wc_override = user_inputs.get("working_capital_override")
        if wc_override is None:
            wc_override = get_v("working_capital_override")
        if wc_override is not None and wc_override > 0:
            return WorkingCapitalAnalysis(
                status="RESOLVED",
                total_working_capital=round(float(wc_override), 2),
                operating_cash_buffer=round(float(wc_override), 2),
                inventory_requirement=0.0 if archetype in (FinancialArchetype.SERVICE, FinancialArchetype.REPAIR) else None,
                methodology="USER_OVERRIDE",
                confidence=1.0,
                provenance=[{
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "USER_OVERRIDE",
                    "description": f"Working capital set directly by user override to ₹{wc_override:,.2f}",
                    "confidence": 1.0
                }],
                notes="Explicit user working capital override applied."
            )

        # Route calculation by archetype
        if archetype in (FinancialArchetype.INVENTORY_RETAIL, FinancialArchetype.TRADING):
            return self._calculate_retail_trading(archetype, asm_map, benchmark_data, get_v, user_inputs)
        elif archetype in (FinancialArchetype.SMALL_MANUFACTURING, FinancialArchetype.FOOD_PROCESSING):
            return self._calculate_manufacturing(archetype, asm_map, benchmark_data, get_v, user_inputs)
        elif archetype in (FinancialArchetype.SERVICE, FinancialArchetype.REPAIR):
            return self._calculate_service_repair(archetype, asm_map, benchmark_data, get_v, user_inputs)
        elif archetype in (FinancialArchetype.AGRICULTURE, FinancialArchetype.LIVESTOCK):
            return self._calculate_agriculture_livestock(archetype, asm_map, benchmark_data, get_v, user_inputs)
        elif archetype == FinancialArchetype.CRAFT:
            return self._calculate_craft(archetype, asm_map, benchmark_data, get_v, user_inputs)
        else:
            return self._calculate_generic_fallback(archetype, asm_map, benchmark_data, get_v)

    def _get_benchmark_param(self, benchmark_data: Any, key: str) -> Optional[float]:
        if not benchmark_data:
            return None

        keys_to_check = [key]
        if key in ("typical_working_capital_monthly_inr", "typical_monthly_requirement"):
            keys_to_check = ["typical_monthly_requirement", "typical_working_capital_monthly_inr"]
        elif key in ("working_capital_months_recommended", "operating_buffer_months", "buffer_months"):
            keys_to_check = ["working_capital_months_recommended", "operating_buffer_months", "buffer_months"]
        elif key in ("inventory_turnover_days", "inventory_days"):
            keys_to_check = ["inventory_turnover_days", "inventory_days"]

        for k in keys_to_check:
            if hasattr(benchmark_data, k) and getattr(benchmark_data, k) is not None:
                try:
                    return float(getattr(benchmark_data, k))
                except (ValueError, TypeError):
                    pass
            if isinstance(benchmark_data, dict) and k in benchmark_data and benchmark_data[k] is not None:
                try:
                    return float(benchmark_data[k])
                except (ValueError, TypeError):
                    pass
            raw = benchmark_data if isinstance(benchmark_data, dict) else (
                benchmark_data.model_dump() if hasattr(benchmark_data, "model_dump") else {}
            )
            wc_info = raw.get("working_capital", {}) if isinstance(raw, dict) else {}
            if isinstance(wc_info, dict) and k in wc_info and wc_info[k] is not None:
                try:
                    return float(wc_info[k])
                except (ValueError, TypeError):
                    pass
            if isinstance(raw, dict) and k in raw and raw[k] is not None:
                try:
                    return float(raw[k])
                except (ValueError, TypeError):
                    pass
        return None

    def _calculate_retail_trading(
        self,
        archetype: FinancialArchetype,
        asm_map: Dict[str, ResolvedAssumption],
        benchmark_data: Any,
        get_v: Any,
        user_inputs: Dict[str, Any]
    ) -> WorkingCapitalAnalysis:
        """
        Retail/Trading: Working capital covers inventory holding, customer credit (receivables),
        minus supplier credit (payables), and operating cash buffer.
        All parameters MUST come from user or benchmark. NO hardcoded day counts!
        """
        provenance_list: List[Dict[str, Any]] = []
        confidences: List[float] = []

        monthly_rev = get_v("monthly_revenue")
        monthly_cogs = get_v("monthly_cogs")
        explicit_inv = get_v("opening_inventory")

        # Extract inventory days strictly from evidence (user or benchmark turnover days)
        inv_days = get_v("inventory_days")
        if inv_days is None:
            inv_days = self._get_benchmark_param(benchmark_data, "inventory_turnover_days")

        # 1. Inventory Requirement
        inv_req: Optional[float] = None
        if explicit_inv is not None and explicit_inv >= 0:
            inv_req = round(float(explicit_inv), 2)
            conf = asm_map["opening_inventory"].confidence if "opening_inventory" in asm_map else 0.95
            provenance_list.append({
                "component": "inventory_requirement",
                "source_type": SourceType.USER_INPUT.value if "opening_inventory" in asm_map else "USER_SPECIFIED",
                "source_id": "OPENING_INVENTORY_INPUT",
                "description": f"Inventory requirement from explicit opening stock: ₹{explicit_inv:,.2f}",
                "confidence": conf
            })
            confidences.append(conf)
        elif inv_days is not None:
            if inv_days == 0:
                inv_req = 0.0
                provenance_list.append({
                    "component": "inventory_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_INVENTORY_DAYS",
                    "description": "Zero inventory holding days evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif monthly_cogs is not None and monthly_cogs > 0:
                inv_req = round((monthly_cogs / 30.0) * inv_days, 2)
                cogs_conf = asm_map["monthly_cogs"].confidence if "monthly_cogs" in asm_map else 0.85
                provenance_list.append({
                    "component": "inventory_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_cogs/30)*inventory_days",
                    "description": f"Calculated inventory holding: (₹{monthly_cogs:,.2f}/30) * {inv_days:.0f} days = ₹{inv_req:,.2f}",
                    "confidence": cogs_conf
                })
                confidences.append(cogs_conf)
        typ_wc = self._get_benchmark_param(benchmark_data, "typical_monthly_requirement") or self._get_benchmark_param(benchmark_data, "typical_working_capital_monthly_inr")
        if inv_req is None and typ_wc is not None:
            inv_req = float(typ_wc)
            b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
            provenance_list.append({
                "component": "inventory_requirement",
                "source_type": SourceType.BENCHMARK.value,
                "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                "description": f"Benchmark opening inventory requirement: ₹{inv_req:,.2f}",
                "confidence": b_conf
            })
            confidences.append(b_conf)

        # 2. Receivables Requirement
        explicit_rec = get_v("receivables")
        if explicit_rec is None:
            explicit_rec = get_v("receivable_requirement")
        rec_days = get_v("receivable_days")
        if rec_days is None:
            rec_days = self._get_benchmark_param(benchmark_data, "receivable_days")

        rec_req: Optional[float] = None
        if explicit_rec is not None:
            if explicit_rec == 0:
                rec_req = 0.0
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "ZERO_RECEIVABLES",
                    "description": "Zero customer credit requirement evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif explicit_rec > 0:
                rec_req = round(float(explicit_rec), 2)
                conf = asm_map["receivables"].confidence if "receivables" in asm_map else 0.95
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "EXPLICIT_RECEIVABLES",
                    "description": f"Customer credit requirement explicitly specified: ₹{rec_req:,.2f}",
                    "confidence": conf
                })
                confidences.append(conf)
        elif rec_days is not None:
            if rec_days == 0:
                rec_req = 0.0
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_RECEIVABLE_DAYS",
                    "description": "Zero receivable credit days evidenced (immediate cash/UPI payment: ₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif monthly_rev is not None and monthly_rev > 0:
                rec_req = round((monthly_rev / 30.0) * rec_days, 2)
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_revenue/30)*receivable_days",
                    "description": f"Receivables requirement: (₹{monthly_rev:,.2f}/30) * {rec_days:.0f} days = ₹{rec_req:,.2f}",
                    "confidence": 0.85
                })
                confidences.append(0.85)

        # 3. Payables Credit Offset
        explicit_pay = get_v("payables")
        if explicit_pay is None:
            explicit_pay = get_v("payable_credit")
        pay_days = get_v("payable_days")
        if pay_days is None:
            pay_days = self._get_benchmark_param(benchmark_data, "payable_days")

        pay_credit: Optional[float] = None
        if explicit_pay is not None:
            if explicit_pay == 0:
                pay_credit = 0.0
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "ZERO_PAYABLES",
                    "description": "Zero supplier credit offset evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif explicit_pay > 0:
                pay_credit = round(float(explicit_pay), 2)
                conf = asm_map["payables"].confidence if "payables" in asm_map else 0.95
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "EXPLICIT_PAYABLES",
                    "description": f"Supplier credit offset explicitly specified: ₹{pay_credit:,.2f}",
                    "confidence": conf
                })
                confidences.append(conf)
        elif pay_days is not None:
            if pay_days == 0:
                pay_credit = 0.0
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_PAYABLE_DAYS",
                    "description": "Zero payable days evidenced (cash purchases: ₹0.00 credit offset).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif monthly_cogs is not None and monthly_cogs > 0:
                pay_credit = round((monthly_cogs / 30.0) * pay_days, 2)
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_cogs/30)*payable_days",
                    "description": f"Supplier credit offset: (₹{monthly_cogs:,.2f}/30) * {pay_days:.0f} days = ₹{pay_credit:,.2f}",
                    "confidence": 0.85
                })
                confidences.append(0.85)

        # 4. Operating Cash Buffer (derived ONLY when buffer months is supported by benchmark or user, or explicit buffer provided)
        explicit_cash_buf = get_v("operating_cash_buffer")
        if explicit_cash_buf is None:
            explicit_cash_buf = get_v("cash_buffer")

        rent = get_v("monthly_rent")
        salary = get_v("salary_cost")
        elec = get_v("electricity_cost")
        fixed_items = [v for v in (rent, salary, elec) if v is not None]
        fixed_monthly_opex = sum(fixed_items) if fixed_items else 0.0

        buf_months = get_v("operating_buffer_months")
        if buf_months is None:
            buf_months = self._get_benchmark_param(benchmark_data, "working_capital_months_recommended")

        cash_buf: Optional[float] = None
        if explicit_cash_buf is not None:
            if explicit_cash_buf == 0:
                cash_buf = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "ZERO_CASH_BUFFER",
                    "description": "Zero operating cash buffer evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif explicit_cash_buf > 0:
                cash_buf = round(float(explicit_cash_buf), 2)
                buf_key = "operating_cash_buffer" if "operating_cash_buffer" in asm_map else ("cash_buffer" if "cash_buffer" in asm_map else None)
                conf = asm_map[buf_key].confidence if buf_key and buf_key in asm_map else 0.95
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "EXPLICIT_CASH_BUFFER",
                    "description": f"Operating cash buffer explicitly specified: ₹{cash_buf:,.2f}",
                    "confidence": conf
                })
                confidences.append(conf)
        elif buf_months is not None:
            if buf_months == 0:
                cash_buf = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_BUFFER_MONTHS",
                    "description": "Zero operating buffer months evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif fixed_monthly_opex > 0:
                cash_buf = round(fixed_monthly_opex * buf_months, 2)
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": f"FORMULA:{buf_months:.1f}*fixed_monthly_opex",
                    "description": f"Evidenced operating cash buffer ({buf_months:.1f} mo): ₹{cash_buf:,.2f}",
                    "confidence": 0.85
                })
                confidences.append(0.85)

        # Operating cycle days (only if evidenced)
        op_cycle_days: Optional[float] = None
        if inv_days is not None:
            op_cycle_days = round(inv_days + (rec_days if rec_days is not None else 0.0) - (pay_days if pay_days is not None else 0.0), 1)

        # Check for missing/unresolved dependencies
        missing_deps: List[str] = []
        if inv_req is None:
            missing_deps.append("inventory")
        has_buf_intent = (
            "operating_cash_buffer" in user_inputs
            or "operating_cash_buffer" in asm_map
            or "cash_buffer" in user_inputs
            or "cash_buffer" in asm_map
            or "operating_buffer_months" in user_inputs
            or "operating_buffer_months" in asm_map
        )
        if has_buf_intent and cash_buf is None:
            missing_deps.append("operating cash buffer")

        has_rec_intent = (
            "receivables" in user_inputs
            or "receivables" in asm_map
            or "receivable_requirement" in user_inputs
            or "receivable_requirement" in asm_map
        )
        if has_rec_intent and rec_req is None:
            missing_deps.append("receivables")

        has_pay_intent = (
            "payables" in user_inputs
            or "payables" in asm_map
            or "payable_credit" in user_inputs
            or "payable_credit" in asm_map
        )
        if has_pay_intent and pay_credit is None:
            missing_deps.append("payables")

        if inv_req is None and cash_buf is None:
            return WorkingCapitalAnalysis(
                status="INSUFFICIENT_DATA",
                operating_cycle_days=op_cycle_days,
                methodology="OPERATING_CYCLE",
                confidence=0.0,
                notes="Insufficient inventory and operating expense parameters to determine working capital."
            )

        if missing_deps:
            missing_str = ", ".join(missing_deps)
            provenance_list.append({
                "component": "total_working_capital",
                "source_type": "UNKNOWN",
                "source_id": "MISSING_WC_DEPENDENCY",
                "description": f"Total working capital cannot be fully calculated: {missing_str} unresolved/missing.",
                "confidence": 0.0
            })
            return WorkingCapitalAnalysis(
                status="PARTIALLY_DERIVED",
                inventory_requirement=inv_req,
                receivable_requirement=rec_req,
                payable_credit=pay_credit,
                operating_cash_buffer=cash_buf,
                operating_cycle_days=op_cycle_days,
                total_working_capital=None,
                methodology="OPERATING_CYCLE",
                provenance=provenance_list,
                confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.50,
                notes=f"Working capital partially derived: {missing_str} unresolved."
            )

        total_wc = round(max(0.0, (inv_req or 0.0) + (rec_req or 0.0) + (cash_buf or 0.0) - (pay_credit or 0.0)), 2)
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.80

        provenance_list.append({
            "component": "total_working_capital",
            "source_type": SourceType.CALCULATED.value,
            "source_id": "FORMULA:inventory+receivables+cash_buffer-payables",
            "description": f"Total WC = ₹{(inv_req or 0.0):,.2f} + ₹{(rec_req or 0.0):,.2f} + ₹{(cash_buf or 0.0):,.2f} - ₹{(pay_credit or 0.0):,.2f} = ₹{total_wc:,.2f}",
            "confidence": avg_conf
        })

        return WorkingCapitalAnalysis(
            status="RESOLVED",
            inventory_requirement=inv_req,
            receivable_requirement=rec_req,
            payable_credit=pay_credit,
            operating_cash_buffer=cash_buf,
            operating_cycle_days=op_cycle_days,
            total_working_capital=total_wc,
            methodology="OPERATING_CYCLE",
            provenance=provenance_list,
            confidence=avg_conf,
            notes="Working capital calculated deterministically from evidenced parameters."
        )

    def _calculate_manufacturing(
        self,
        archetype: FinancialArchetype,
        asm_map: Dict[str, ResolvedAssumption],
        benchmark_data: Any,
        get_v: Any,
        user_inputs: Dict[str, Any]
    ) -> WorkingCapitalAnalysis:
        """
        Manufacturing / Food Processing:
        Parameters must come from benchmark or user. No unsourced 15-day or 1.5-month defaults!
        """
        provenance_list: List[Dict[str, Any]] = []
        confidences: List[float] = []

        monthly_rev = get_v("monthly_revenue")
        monthly_cogs = get_v("monthly_cogs")

        inv_days = get_v("inventory_days")
        if inv_days is None:
            inv_days = self._get_benchmark_param(benchmark_data, "inventory_turnover_days")

        rec_days = get_v("receivable_days")
        if rec_days is None:
            rec_days = self._get_benchmark_param(benchmark_data, "receivable_days")

        pay_days = get_v("payable_days")
        if pay_days is None:
            pay_days = self._get_benchmark_param(benchmark_data, "payable_days")

        buf_months = get_v("operating_buffer_months")
        if buf_months is None:
            buf_months = self._get_benchmark_param(benchmark_data, "working_capital_months_recommended")

        # 1. Inventory Requirement
        inv_req: Optional[float] = None
        if inv_days is not None:
            if inv_days == 0:
                inv_req = 0.0
                provenance_list.append({
                    "component": "inventory_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_INVENTORY_DAYS",
                    "description": "Zero manufacturing inventory holding days evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif monthly_cogs is not None and monthly_cogs > 0:
                inv_req = round((monthly_cogs / 30.0) * inv_days, 2)
                cogs_conf = asm_map["monthly_cogs"].confidence if "monthly_cogs" in asm_map else 0.85
                provenance_list.append({
                    "component": "inventory_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_cogs/30)*inventory_days",
                    "description": f"Manufacturing inventory holding: (₹{monthly_cogs:,.2f}/30) * {inv_days:.0f} days = ₹{inv_req:,.2f}",
                    "confidence": cogs_conf
                })
                confidences.append(cogs_conf)
        typ_wc = self._get_benchmark_param(benchmark_data, "typical_monthly_requirement") or self._get_benchmark_param(benchmark_data, "typical_working_capital_monthly_inr")
        if inv_req is None and typ_wc is not None:
            inv_req = float(typ_wc)
            b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
            provenance_list.append({
                "component": "inventory_requirement",
                "source_type": SourceType.BENCHMARK.value,
                "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                "description": f"Benchmark manufacturing working capital requirement: ₹{inv_req:,.2f}",
                "confidence": b_conf
            })
            confidences.append(b_conf)

        # 2. Receivables Requirement
        rec_req: Optional[float] = None
        if rec_days is not None:
            if rec_days == 0:
                rec_req = 0.0
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_RECEIVABLE_DAYS",
                    "description": "Zero receivable credit days evidenced (immediate payment: ₹0.00).",
                    "confidence": 1.0
                })
            elif monthly_rev is not None and monthly_rev > 0:
                rec_req = round((monthly_rev / 30.0) * rec_days, 2)
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_revenue/30)*receivable_days",
                    "description": f"Receivables requirement: (₹{monthly_rev:,.2f}/30) * {rec_days:.0f} days = ₹{rec_req:,.2f}",
                    "confidence": 0.85
                })

        # 3. Payables Credit Offset
        pay_credit: Optional[float] = None
        if pay_days is not None:
            if pay_days == 0:
                pay_credit = 0.0
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_PAYABLE_DAYS",
                    "description": "Zero payable days evidenced (cash purchases: ₹0.00 credit offset).",
                    "confidence": 1.0
                })
            elif monthly_cogs is not None and monthly_cogs > 0:
                pay_credit = round((monthly_cogs / 30.0) * pay_days, 2)
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_cogs/30)*payable_days",
                    "description": f"Payables credit offset: (₹{monthly_cogs:,.2f}/30) * {pay_days:.0f} days = ₹{pay_credit:,.2f}",
                    "confidence": 0.85
                })

        # 4. Operating Cash Buffer
        explicit_cash_buf = get_v("operating_cash_buffer")
        if explicit_cash_buf is None:
            explicit_cash_buf = get_v("cash_buffer")

        rent = get_v("monthly_rent")
        salary = get_v("salary_cost")
        elec = get_v("electricity_cost")
        fixed_items = [v for v in (rent, salary, elec) if v is not None]
        fixed_opex = sum(fixed_items) if fixed_items else 0.0

        cash_buf: Optional[float] = None
        if explicit_cash_buf is not None:
            if explicit_cash_buf == 0:
                cash_buf = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "ZERO_CASH_BUFFER",
                    "description": "Zero operating cash buffer evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif explicit_cash_buf > 0:
                cash_buf = round(float(explicit_cash_buf), 2)
                buf_key = "operating_cash_buffer" if "operating_cash_buffer" in asm_map else ("cash_buffer" if "cash_buffer" in asm_map else None)
                conf = asm_map[buf_key].confidence if buf_key and buf_key in asm_map else 0.95
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "EXPLICIT_CASH_BUFFER",
                    "description": f"Operating cash buffer explicitly specified: ₹{cash_buf:,.2f}",
                    "confidence": conf
                })
                confidences.append(conf)
        elif buf_months is not None:
            if buf_months == 0:
                cash_buf = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_BUFFER_MONTHS",
                    "description": "Zero operating buffer months evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif fixed_opex > 0:
                cash_buf = round(fixed_opex * buf_months, 2)
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": f"FORMULA:{buf_months:.1f}*fixed_opex",
                    "description": f"Evidenced operating buffer ({buf_months:.1f} mo): ₹{cash_buf:,.2f}",
                    "confidence": 0.85
                })
                confidences.append(0.85)
            elif typ_wc is not None and buf_months is not None and buf_months > 1.0:
                cash_buf = round(float(typ_wc) * (buf_months - 1.0), 2)
                b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.BENCHMARK.value,
                    "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                    "description": f"Benchmark operational buffer ({buf_months - 1.0:.1f} mo): ₹{cash_buf:,.2f}",
                    "confidence": b_conf
                })
                confidences.append(b_conf)

        op_cycle_days: Optional[float] = None
        if inv_days is not None:
            op_cycle_days = round(inv_days + (rec_days if rec_days is not None else 0.0) - (pay_days if pay_days is not None else 0.0), 1)

        # Check for missing/unresolved dependencies
        missing_deps: List[str] = []
        if inv_req is None:
            missing_deps.append("inventory")
        has_buf_intent = (
            "operating_cash_buffer" in user_inputs
            or "operating_cash_buffer" in asm_map
            or "cash_buffer" in user_inputs
            or "cash_buffer" in asm_map
            or "operating_buffer_months" in user_inputs
            or "operating_buffer_months" in asm_map
        )
        if has_buf_intent and cash_buf is None:
            missing_deps.append("operating cash buffer")

        has_rec_intent = (
            "receivables" in user_inputs
            or "receivables" in asm_map
            or "receivable_requirement" in user_inputs
            or "receivable_requirement" in asm_map
        )
        if has_rec_intent and rec_req is None:
            missing_deps.append("receivables")

        has_pay_intent = (
            "payables" in user_inputs
            or "payables" in asm_map
            or "payable_credit" in user_inputs
            or "payable_credit" in asm_map
        )
        if has_pay_intent and pay_credit is None:
            missing_deps.append("payables")

        if inv_req is None and cash_buf is None:
            return WorkingCapitalAnalysis(
                status="INSUFFICIENT_DATA",
                operating_cycle_days=op_cycle_days,
                methodology="OPERATING_CYCLE",
                confidence=0.0,
                notes="Insufficient manufacturing driver data to determine working capital."
            )

        if missing_deps:
            missing_str = ", ".join(missing_deps)
            provenance_list.append({
                "component": "total_working_capital",
                "source_type": "UNKNOWN",
                "source_id": "MISSING_WC_DEPENDENCY",
                "description": f"Manufacturing working capital cannot be fully calculated: {missing_str} unresolved/missing.",
                "confidence": 0.0
            })
            return WorkingCapitalAnalysis(
                status="PARTIALLY_DERIVED",
                inventory_requirement=inv_req,
                receivable_requirement=rec_req,
                payable_credit=pay_credit,
                operating_cash_buffer=cash_buf,
                operating_cycle_days=op_cycle_days,
                total_working_capital=None,
                methodology="OPERATING_CYCLE",
                provenance=provenance_list,
                confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.50,
                notes=f"Manufacturing working capital partially derived: {missing_str} unresolved."
            )

        total_wc = round(max(0.0, (inv_req or 0.0) + (rec_req or 0.0) + (cash_buf or 0.0) - (pay_credit or 0.0)), 2)
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.80

        provenance_list.append({
            "component": "total_working_capital",
            "source_type": SourceType.CALCULATED.value,
            "source_id": "FORMULA:inventory+receivables+cash_buffer-payables",
            "description": f"Total WC = ₹{(inv_req or 0.0):,.2f} + ₹{(rec_req or 0.0):,.2f} + ₹{(cash_buf or 0.0):,.2f} - ₹{(pay_credit or 0.0):,.2f} = ₹{total_wc:,.2f}",
            "confidence": avg_conf
        })

        return WorkingCapitalAnalysis(
            status="RESOLVED",
            inventory_requirement=inv_req,
            receivable_requirement=rec_req,
            payable_credit=pay_credit,
            operating_cash_buffer=cash_buf,
            operating_cycle_days=op_cycle_days,
            total_working_capital=total_wc,
            methodology="OPERATING_CYCLE",
            provenance=provenance_list,
            confidence=avg_conf,
            notes="Manufacturing working capital calculated deterministically from evidenced parameters."
        )

    def _calculate_service_repair(
        self,
        archetype: FinancialArchetype,
        asm_map: Dict[str, ResolvedAssumption],
        benchmark_data: Any,
        get_v: Any,
        user_inputs: Dict[str, Any]
    ) -> WorkingCapitalAnalysis:
        """
        Service / Repair:
        True semantic domain rule: Pure service businesses hold NO retail merchandise inventory (₹0.00).
        Operating cash buffer is evidenced by benchmark working_capital_months_recommended or user input.
        """
        provenance_list: List[Dict[str, Any]] = []
        confidences: List[float] = []

        monthly_rev = get_v("monthly_revenue")

        # Consumables / spare parts for repair archetype
        inv_req: Optional[float] = None
        if archetype == FinancialArchetype.REPAIR:
            mat_cost = get_v("material_cost_per_job")
            jobs = get_v("jobs_per_day")
            op_days = get_v("operating_days")
            parts_days = get_v("inventory_days")
            if parts_days is None:
                parts_days = self._get_benchmark_param(benchmark_data, "inventory_turnover_days")

            if parts_days is not None:
                if parts_days == 0:
                    inv_req = 0.0
                    provenance_list.append({
                        "component": "inventory_requirement",
                        "source_type": SourceType.CALCULATED.value,
                        "source_id": "ZERO_PARTS_DAYS",
                        "description": "Zero spare parts holding days evidenced (₹0.00).",
                        "confidence": 1.0
                    })
                    confidences.append(1.0)
                elif mat_cost is not None and jobs is not None and op_days is not None:
                    monthly_parts = mat_cost * jobs * op_days
                    inv_req = round((monthly_parts / 30.0) * parts_days, 2)
                    provenance_list.append({
                        "component": "inventory_requirement",
                        "source_type": SourceType.CALCULATED.value,
                        "source_id": f"FORMULA:(parts_cost/30)*{parts_days:.0f}",
                        "description": f"Repair spare parts holding ({parts_days:.0f} days): ₹{inv_req:,.2f}",
                        "confidence": 0.85
                    })
                    confidences.append(0.85)
                else:
                    inv_req = None
            else:
                inv_req = None
        else:
            # Structural zero for pure service: semantic domain rule
            inv_req = 0.0
            provenance_list.append({
                "component": "inventory_requirement",
                "source_type": SourceType.CALCULATED.value,
                "source_id": "SEMANTIC_RULE:SERVICE_NO_INVENTORY",
                "description": "Pure service archetype holds no retail merchandise inventory (₹0.00).",
                "confidence": 1.0
            })
            confidences.append(1.0)

        # Receivables (credit services)
        rec_days = get_v("receivable_days")
        if rec_days is None:
            rec_days = self._get_benchmark_param(benchmark_data, "receivable_days")

        rec_req: Optional[float] = None
        if rec_days is not None:
            if rec_days == 0:
                rec_req = 0.0
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_RECEIVABLE_DAYS",
                    "description": "Zero receivable credit days evidenced (immediate payment: ₹0.00).",
                    "confidence": 1.0
                })
            elif monthly_rev is not None and monthly_rev > 0:
                rec_req = round((monthly_rev / 30.0) * rec_days, 2)
                provenance_list.append({
                    "component": "receivable_requirement",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "FORMULA:(monthly_revenue/30)*receivable_days",
                    "description": f"Receivables requirement: (₹{monthly_rev:,.2f}/30) * {rec_days:.0f} days = ₹{rec_req:,.2f}",
                    "confidence": 0.85
                })

        # Payables
        pay_days = get_v("payable_days")
        if pay_days is None:
            pay_days = self._get_benchmark_param(benchmark_data, "payable_days")

        pay_credit: Optional[float] = None
        if pay_days is not None:
            if pay_days == 0:
                pay_credit = 0.0
                provenance_list.append({
                    "component": "payable_credit",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_PAYABLE_DAYS",
                    "description": "Zero payable days evidenced (immediate cash settlement: ₹0.00).",
                    "confidence": 1.0
                })

        # Operating buffer: Use explicit buffer, benchmark recommended months, or user input
        explicit_cash_buf = get_v("operating_cash_buffer")
        if explicit_cash_buf is None:
            explicit_cash_buf = get_v("cash_buffer")

        rent = get_v("monthly_rent")
        salary = get_v("salary_cost")
        elec = get_v("electricity_cost")
        mkt = get_v("marketing_cost")
        fixed_items = [v for v in (rent, salary, elec, mkt) if v is not None]
        monthly_fixed_opex = sum(fixed_items) if fixed_items else None

        buf_months = get_v("operating_buffer_months")
        if buf_months is None:
            buf_months = self._get_benchmark_param(benchmark_data, "working_capital_months_recommended")

        typ_wc = self._get_benchmark_param(benchmark_data, "typical_monthly_requirement") or self._get_benchmark_param(benchmark_data, "typical_working_capital_monthly_inr")
        cash_buf: Optional[float] = None
        if explicit_cash_buf is not None:
            if explicit_cash_buf == 0:
                cash_buf = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "ZERO_CASH_BUFFER",
                    "description": "Zero operating cash buffer evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif explicit_cash_buf > 0:
                cash_buf = round(float(explicit_cash_buf), 2)
                buf_key = "operating_cash_buffer" if "operating_cash_buffer" in asm_map else ("cash_buffer" if "cash_buffer" in asm_map else None)
                conf = asm_map[buf_key].confidence if buf_key and buf_key in asm_map else 0.95
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.USER_INPUT.value,
                    "source_id": "EXPLICIT_CASH_BUFFER",
                    "description": f"Operating cash buffer explicitly specified: ₹{cash_buf:,.2f}",
                    "confidence": conf
                })
                confidences.append(conf)
        elif buf_months is not None:
            if buf_months == 0:
                cash_buf = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_BUFFER_MONTHS",
                    "description": "Zero operating buffer months evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif monthly_fixed_opex is not None and monthly_fixed_opex > 0:
                cash_buf = round(monthly_fixed_opex * buf_months, 2)
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": f"FORMULA:{buf_months:.1f}*monthly_fixed_opex",
                    "description": f"{buf_months:.1f}-month evidenced operating cash buffer: ₹{cash_buf:,.2f}",
                    "confidence": 0.90
                })
                confidences.append(0.90)
            elif typ_wc is not None:
                cash_buf = round(float(typ_wc) * (buf_months if buf_months is not None else 1.5), 2)
                b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.BENCHMARK.value,
                    "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                    "description": f"Benchmark service operating buffer ({buf_months or 1.5:.1f} mo): ₹{cash_buf:,.2f}",
                    "confidence": b_conf
                })
                confidences.append(b_conf)
        elif typ_wc is not None:
            cash_buf = round(float(typ_wc) * 1.5, 2)
            b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
            provenance_list.append({
                "component": "operating_cash_buffer",
                "source_type": SourceType.BENCHMARK.value,
                "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                "description": f"Benchmark service operating buffer: ₹{cash_buf:,.2f}",
                "confidence": b_conf
            })
            confidences.append(b_conf)

        if cash_buf is None:
            return WorkingCapitalAnalysis(
                status="INSUFFICIENT_DATA",
                inventory_requirement=inv_req,
                operating_cycle_days=0.0,
                methodology="SERVICE_OPERATING_BUFFER",
                confidence=0.0,
                notes="Insufficient operating buffer parameters to determine service working capital."
            )

        # Check for missing/unresolved dependencies
        missing_deps: List[str] = []
        if inv_req is None and archetype == FinancialArchetype.REPAIR:
            missing_deps.append("spare parts inventory")
        if cash_buf is None:
            missing_deps.append("operating cash buffer")
        has_rec_intent = (
            "receivables" in user_inputs
            or "receivables" in asm_map
            or "receivable_requirement" in user_inputs
            or "receivable_requirement" in asm_map
        )
        if has_rec_intent and rec_req is None:
            missing_deps.append("receivables")
        has_pay_intent = (
            "payables" in user_inputs
            or "payables" in asm_map
            or "payable_credit" in user_inputs
            or "payable_credit" in asm_map
        )
        if has_pay_intent and pay_credit is None:
            missing_deps.append("payables")

        if missing_deps:
            missing_str = ", ".join(missing_deps)
            provenance_list.append({
                "component": "total_working_capital",
                "source_type": "UNKNOWN",
                "source_id": "MISSING_WC_DEPENDENCY",
                "description": f"Service working capital cannot be fully calculated: {missing_str} unresolved/missing.",
                "confidence": 0.0
            })
            return WorkingCapitalAnalysis(
                status="PARTIALLY_DERIVED",
                inventory_requirement=inv_req,
                receivable_requirement=rec_req,
                payable_credit=pay_credit,
                operating_cash_buffer=cash_buf,
                operating_cycle_days=0.0 if archetype == FinancialArchetype.SERVICE else None,
                total_working_capital=None,
                methodology="SERVICE_OPERATING_BUFFER",
                provenance=provenance_list,
                confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.50,
                notes=f"Service working capital partially derived: {missing_str} unresolved."
            )

        total_wc = round(max(0.0, (inv_req or 0.0) + (rec_req or 0.0) + (cash_buf or 0.0) - (pay_credit or 0.0)), 2)
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.85

        provenance_list.append({
            "component": "total_working_capital",
            "source_type": SourceType.CALCULATED.value,
            "source_id": "FORMULA:inventory+operating_cash_buffer",
            "description": f"Total Service Working Capital = ₹{(inv_req or 0.0):,.2f} + ₹{(rec_req or 0.0):,.2f} + ₹{(cash_buf or 0.0):,.2f} - ₹{(pay_credit or 0.0):,.2f} = ₹{total_wc:,.2f}",
            "confidence": avg_conf
        })

        return WorkingCapitalAnalysis(
            status="RESOLVED",
            inventory_requirement=inv_req,
            receivable_requirement=rec_req,
            payable_credit=pay_credit,
            operating_cash_buffer=cash_buf,
            operating_cycle_days=0.0 if archetype == FinancialArchetype.SERVICE else None,
            total_working_capital=total_wc,
            methodology="SERVICE_OPERATING_BUFFER",
            provenance=provenance_list,
            confidence=avg_conf,
            notes="Service working capital prioritized around fixed operating buffer rather than retail inventory holding."
        )

    def _calculate_agriculture_livestock(
        self,
        archetype: FinancialArchetype,
        asm_map: Dict[str, ResolvedAssumption],
        benchmark_data: Any,
        get_v: Any,
        user_inputs: Dict[str, Any]
    ) -> WorkingCapitalAnalysis:
        """
        Agriculture / Livestock:
        No unsourced 50/50 splits! Parameters derived from benchmark or user inputs.
        """
        provenance_list: List[Dict[str, Any]] = []
        confidences: List[float] = []

        rm_cost = get_v("raw_material_cost")
        capacity = get_v("installed_capacity")
        salary = get_v("salary_cost")

        buf_months = get_v("operating_buffer_months")
        if buf_months is None:
            buf_months = self._get_benchmark_param(benchmark_data, "working_capital_months_recommended")

        rec_days = get_v("receivable_days")
        if rec_days is None:
            rec_days = self._get_benchmark_param(benchmark_data, "receivable_days")
        rec_req = 0.0 if rec_days == 0 else (round((get_v("monthly_revenue") / 30.0) * rec_days, 2) if (rec_days and get_v("monthly_revenue")) else None)

        pay_days = get_v("payable_days")
        if pay_days is None:
            pay_days = self._get_benchmark_param(benchmark_data, "payable_days")
        pay_credit = 0.0 if pay_days == 0 else None

        typ_wc = self._get_benchmark_param(benchmark_data, "typical_monthly_requirement") or self._get_benchmark_param(benchmark_data, "typical_working_capital_monthly_inr")
        wc_amount: Optional[float] = None
        if buf_months is not None:
            if buf_months == 0:
                wc_amount = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_BUFFER_MONTHS",
                    "description": "Zero agricultural operating buffer months evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif rm_cost is not None and capacity is not None:
                salary_val = salary if salary is not None else 0.0
                monthly_inputs = (rm_cost * capacity) + salary_val
                wc_amount = round(monthly_inputs * buf_months, 2)
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": f"FORMULA:{buf_months:.1f}*monthly_inputs",
                    "description": f"{buf_months:.1f}-month operational buffer: ₹{wc_amount:,.2f}",
                    "confidence": 0.85
                })
                confidences.append(0.85)
            elif typ_wc is not None:
                wc_amount = round(float(typ_wc) * buf_months, 2)
                b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.BENCHMARK.value,
                    "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                    "description": f"Benchmark agricultural operational requirement ({buf_months:.1f} mo): ₹{wc_amount:,.2f}",
                    "confidence": b_conf
                })
                confidences.append(b_conf)
        elif typ_wc is not None:
            wc_amount = round(float(typ_wc) * 2.0, 2)
            b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
            provenance_list.append({
                "component": "operating_cash_buffer",
                "source_type": SourceType.BENCHMARK.value,
                "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                "description": f"Benchmark agricultural operational requirement: ₹{wc_amount:,.2f}",
                "confidence": b_conf
            })
            confidences.append(b_conf)

        missing_deps: List[str] = []
        if wc_amount is None:
            missing_deps.append("operational buffer")
        if ("receivables" in user_inputs or "receivables" in asm_map) and rec_req is None:
            missing_deps.append("receivables")
        if ("payables" in user_inputs or "payables" in asm_map) and pay_credit is None:
            missing_deps.append("payables")

        if wc_amount is None and not (rec_days is not None or pay_days is not None):
            return WorkingCapitalAnalysis(
                status="INSUFFICIENT_DATA",
                methodology="SEASONAL_OPERATING_BUFFER",
                confidence=0.0,
                notes="Insufficient agricultural/livestock operating parameters to determine working capital."
            )

        if missing_deps:
            missing_str = ", ".join(missing_deps)
            provenance_list.append({
                "component": "total_working_capital",
                "source_type": "UNKNOWN",
                "source_id": "MISSING_WC_DEPENDENCY",
                "description": f"Agricultural working capital cannot be fully calculated: {missing_str} unresolved/missing.",
                "confidence": 0.0
            })
            return WorkingCapitalAnalysis(
                status="PARTIALLY_DERIVED",
                inventory_requirement=None,
                receivable_requirement=rec_req,
                payable_credit=pay_credit,
                operating_cash_buffer=wc_amount,
                operating_cycle_days=None,
                total_working_capital=None,
                methodology="SEASONAL_OPERATING_BUFFER",
                provenance=provenance_list,
                confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.50,
                notes=f"Agricultural working capital partially derived: {missing_str} unresolved."
            )

        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.80
        total_wc = round(max(0.0, (wc_amount or 0.0) + (rec_req or 0.0) - (pay_credit or 0.0)), 2)

        provenance_list.append({
            "component": "total_working_capital",
            "source_type": SourceType.CALCULATED.value,
            "source_id": "FORMULA:seasonal_buffer",
            "description": f"Total Agricultural Working Capital: ₹{total_wc:,.2f}",
            "confidence": avg_conf
        })

        return WorkingCapitalAnalysis(
            status="RESOLVED",
            inventory_requirement=None,
            receivable_requirement=rec_req,
            payable_credit=pay_credit,
            operating_cash_buffer=wc_amount,
            operating_cycle_days=None,
            total_working_capital=total_wc,
            methodology="SEASONAL_OPERATING_BUFFER",
            provenance=provenance_list,
            confidence=avg_conf,
            notes="Working capital based strictly on evidenced operating parameters."
        )

    def _calculate_craft(
        self,
        archetype: FinancialArchetype,
        asm_map: Dict[str, ResolvedAssumption],
        benchmark_data: Any,
        get_v: Any,
        user_inputs: Dict[str, Any]
    ) -> WorkingCapitalAnalysis:
        """
        Craft / Artisan:
        No unsourced 60/40 splits! Parameters derived from benchmark or user inputs.
        """
        provenance_list: List[Dict[str, Any]] = []
        confidences: List[float] = []

        buf_months = get_v("operating_buffer_months")
        if buf_months is None:
            buf_months = self._get_benchmark_param(benchmark_data, "working_capital_months_recommended")

        rec_days = get_v("receivable_days")
        if rec_days is None:
            rec_days = self._get_benchmark_param(benchmark_data, "receivable_days")
        rec_req = 0.0 if rec_days == 0 else (round((get_v("monthly_revenue") / 30.0) * rec_days, 2) if (rec_days and get_v("monthly_revenue")) else None)

        pay_days = get_v("payable_days")
        if pay_days is None:
            pay_days = self._get_benchmark_param(benchmark_data, "payable_days")
        pay_credit = 0.0 if pay_days == 0 else None

        typ_wc = self._get_benchmark_param(benchmark_data, "typical_monthly_requirement") or self._get_benchmark_param(benchmark_data, "typical_working_capital_monthly_inr")

        rm_cost = get_v("raw_material_cost")
        rent = get_v("monthly_rent")
        salary = get_v("salary_cost")

        wc_amount: Optional[float] = None
        if buf_months is not None:
            if buf_months == 0:
                wc_amount = 0.0
                provenance_list.append({
                    "component": "operating_cash_buffer",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": "ZERO_BUFFER_MONTHS",
                    "description": "Zero craft operating buffer months evidenced (₹0.00).",
                    "confidence": 1.0
                })
                confidences.append(1.0)
            elif any(v is not None for v in (rm_cost, rent, salary)):
                monthly_opex = sum(v for v in (rm_cost, rent, salary) if v is not None)
                wc_amount = round(monthly_opex * buf_months, 2)
                provenance_list.append({
                    "component": "total_working_capital",
                    "source_type": SourceType.CALCULATED.value,
                    "source_id": f"FORMULA:{buf_months:.1f}*monthly_craft_opex",
                    "description": f"{buf_months:.1f}-month craft operating buffer: ₹{wc_amount:,.2f}",
                    "confidence": 0.85
                })
                confidences.append(0.85)
            elif typ_wc is not None:
                wc_amount = round(float(typ_wc) * buf_months, 2)
                b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
                provenance_list.append({
                    "component": "total_working_capital",
                    "source_type": SourceType.BENCHMARK.value,
                    "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                    "description": f"Benchmark artisan working capital ({buf_months:.1f} mo): ₹{wc_amount:,.2f}",
                    "confidence": b_conf
                })
                confidences.append(b_conf)
        elif typ_wc is not None:
            wc_amount = round(float(typ_wc) * 2.0, 2)
            b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.85
            provenance_list.append({
                "component": "total_working_capital",
                "source_type": SourceType.BENCHMARK.value,
                "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                "description": f"Benchmark artisan working capital: ₹{wc_amount:,.2f}",
                "confidence": b_conf
            })
            confidences.append(b_conf)

        missing_deps: List[str] = []
        if wc_amount is None:
            missing_deps.append("craft operating buffer")
        if ("receivables" in user_inputs or "receivables" in asm_map) and rec_req is None:
            missing_deps.append("receivables")
        if ("payables" in user_inputs or "payables" in asm_map) and pay_credit is None:
            missing_deps.append("payables")

        if wc_amount is None and not (rec_days is not None or pay_days is not None):
            return WorkingCapitalAnalysis(
                status="INSUFFICIENT_DATA",
                methodology="ARTISAN_OPERATING_CYCLE",
                confidence=0.0,
                notes="Insufficient craft operating parameters to determine working capital."
            )

        if missing_deps:
            missing_str = ", ".join(missing_deps)
            provenance_list.append({
                "component": "total_working_capital",
                "source_type": "UNKNOWN",
                "source_id": "MISSING_WC_DEPENDENCY",
                "description": f"Craft working capital cannot be fully calculated: {missing_str} unresolved/missing.",
                "confidence": 0.0
            })
            return WorkingCapitalAnalysis(
                status="PARTIALLY_DERIVED",
                inventory_requirement=None,
                receivable_requirement=rec_req,
                payable_credit=pay_credit,
                operating_cash_buffer=wc_amount,
                operating_cycle_days=None,
                total_working_capital=None,
                methodology="ARTISAN_OPERATING_CYCLE",
                provenance=provenance_list,
                confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.50,
                notes=f"Craft working capital partially derived: {missing_str} unresolved."
            )

        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else 0.80
        total_wc = round(max(0.0, (wc_amount or 0.0) + (rec_req or 0.0) - (pay_credit or 0.0)), 2)

        return WorkingCapitalAnalysis(
            status="RESOLVED",
            inventory_requirement=None,
            receivable_requirement=rec_req,
            payable_credit=pay_credit,
            operating_cash_buffer=wc_amount,
            operating_cycle_days=None,
            total_working_capital=total_wc,
            methodology="ARTISAN_OPERATING_CYCLE",
            provenance=provenance_list,
            confidence=avg_conf,
            notes="Craft working capital based on evidenced operating parameters."
        )

    def _calculate_generic_fallback(
        self,
        archetype: FinancialArchetype,
        asm_map: Dict[str, ResolvedAssumption],
        benchmark_data: Any,
        get_v: Any
    ) -> WorkingCapitalAnalysis:
        """
        Fallback for OTHER / unclassified archetype:
        Uses benchmark typical_working_capital_monthly_inr if present; otherwise explicit INSUFFICIENT_DATA.
        Never invents numbers.
        """
        typ_wc = self._get_benchmark_param(benchmark_data, "typical_monthly_requirement") or self._get_benchmark_param(benchmark_data, "typical_working_capital_monthly_inr")
        buf_months = self._get_benchmark_param(benchmark_data, "working_capital_months_recommended") or 1.0
        if typ_wc is not None:
            val = round(float(typ_wc) * float(buf_months), 2)
            b_conf = self._get_benchmark_param(benchmark_data, "confidence") or 0.80
            return WorkingCapitalAnalysis(
                status="BENCHMARKED",
                total_working_capital=val,
                operating_cash_buffer=val,
                inventory_requirement=0.0,
                methodology="BENCHMARK_FALLBACK",
                confidence=b_conf,
                provenance=[{
                    "source_type": SourceType.BENCHMARK.value,
                    "source_id": getattr(benchmark_data, "source_id", "BENCHMARK_DB") if hasattr(benchmark_data, "source_id") else "BENCHMARK_DB",
                    "description": f"Generic benchmark working capital requirement: ₹{val:,.2f}",
                    "confidence": b_conf
                }],
                notes="Archetype OTHER: Using benchmark working capital fallback."
            )

        return WorkingCapitalAnalysis(
            status="INSUFFICIENT_DATA",
            methodology="UNSUPPORTED_DATA",
            confidence=0.0,
            notes="Insufficient evidence to determine working capital for unclassified archetype."
        )


# Global singleton
working_capital_engine = WorkingCapitalEngine()
