"""
Cost & Operating Expense Projection Engine for Milestone 3.
Models variable COGS and separate fixed/variable operating expense line items.
Zero unsourced salary defaults. Unknown expense items are never silently zeroed.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    CostProjection,
    CostProjectionLine,
    RevenueProjection,
    ProfitabilityProjection,
)
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData


class CostProjectionEngine:
    """
    Constructs multi-year cost and operating expense projections.
    """

    @staticmethod
    def project(
        revenue_projection: RevenueProjection,
        profitability: Optional[ProfitabilityProjection] = None,
        benchmark_data: Optional[BenchmarkFinancialData] = None,
        assumptions_map: Optional[Dict[str, Any]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> CostProjection:
        """
        Projects COGS and detailed operating expenses for each year.
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

        # 1. Base COGS parameters
        cogs_ratio: Optional[float] = None
        explicit_cogs = get_val("monthly_cogs")
        if explicit_cogs is not None:
            explicit_cogs = explicit_cogs * 12.0

        gm_pct = get_val("gross_margin")
        if gm_pct is None:
            gm_pct = get_val("gross_margin_pct")
        if gm_pct is not None:
            cogs_ratio = round(max(0.0, 1.0 - (gm_pct / 100.0 if gm_pct > 1.0 else gm_pct)), 4)
        elif benchmark_data and hasattr(benchmark_data, "cogs_percentage") and getattr(benchmark_data, "cogs_percentage") is not None:
            raw_cogs = float(getattr(benchmark_data, "cogs_percentage"))
            cogs_ratio = round(raw_cogs / 100.0 if raw_cogs > 1.0 else raw_cogs, 4)
        elif benchmark_data and hasattr(benchmark_data, "gross_margin_pct") and getattr(benchmark_data, "gross_margin_pct") is not None:
            raw_gm = float(getattr(benchmark_data, "gross_margin_pct"))
            cogs_ratio = round(max(0.0, 1.0 - (raw_gm / 100.0 if raw_gm > 1.0 else raw_gm)), 4)
        elif profitability and profitability.annual_revenue and profitability.annual_cogs:
            cogs_ratio = round(profitability.annual_cogs / profitability.annual_revenue, 4)

        # 2. Operating Expenses Line Items (Monthly to Annual)
        # Salaries: staff_count * salary_per_person OR total salary. NO ₹10k defaults!
        salary_annual: Optional[float] = None
        staff_count = get_val("staff_count")
        salary_per_person = get_val("salary_per_person")
        total_salary_monthly = get_val("salary_cost")
        if total_salary_monthly is None:
            total_salary_monthly = get_val("salaries")
        if total_salary_monthly is None:
            total_salary_monthly = get_val("monthly_salary")

        if total_salary_monthly is not None:
            salary_annual = round(total_salary_monthly * 12.0, 2)
        elif staff_count is not None and salary_per_person is not None:
            salary_annual = round(staff_count * salary_per_person * 12.0, 2)
        elif staff_count == 0:
            salary_annual = 0.0  # Solo entrepreneur

        # Rent
        rent_monthly = get_val("monthly_rent")
        if rent_monthly is None:
            rent_monthly = get_val("rent")
        rent_annual = round(rent_monthly * 12.0, 2) if rent_monthly is not None else None

        # Utilities / Electricity
        elec_monthly = get_val("electricity_cost")
        if elec_monthly is None:
            elec_monthly = get_val("utilities_cost")
        if elec_monthly is None:
            elec_monthly = get_val("power_cost")
        elec_annual = round(elec_monthly * 12.0, 2) if elec_monthly is not None else None

        # Marketing
        mkt_monthly = get_val("marketing_cost")
        if mkt_monthly is None:
            mkt_monthly = get_val("advertising_cost")
        mkt_annual = round(mkt_monthly * 12.0, 2) if mkt_monthly is not None else None

        # Repairs & Maintenance
        repairs_monthly = get_val("maintenance_cost")
        if repairs_monthly is None:
            repairs_monthly = get_val("repairs_cost")
        repairs_annual = round(repairs_monthly * 12.0, 2) if repairs_monthly is not None else None

        # Admin, Transport, Technology
        admin_monthly = get_val("admin_cost")
        admin_annual = round(admin_monthly * 12.0, 2) if admin_monthly is not None else None

        transport_monthly = get_val("transport_cost")
        transport_annual = round(transport_monthly * 12.0, 2) if transport_monthly is not None else None

        tech_monthly = get_val("software_cost")
        if tech_monthly is None:
            tech_monthly = get_val("tech_cost")
        tech_annual = round(tech_monthly * 12.0, 2) if tech_monthly is not None else None

        other_opex_monthly = get_val("other_operating_cost")
        if other_opex_monthly is None:
            other_opex_monthly = get_val("misc_opex")
        other_opex_annual = round(other_opex_monthly * 12.0, 2) if other_opex_monthly is not None else None

        # Check if premises are structurally owned (zero rent)
        if rent_annual is None:
            if user_in.get("owns_premises") is True or user_in.get("premises_ownership") == "owned" or user_in.get("rent") == 0.0:
                rent_annual = 0.0

        # Check if solo entrepreneur (zero salary)
        if salary_annual is None:
            if staff_count == 0 or user_in.get("staff_count") == 0 or user_in.get("is_solo") is True:
                salary_annual = 0.0

        # Check if electricity is explicitly unknown or unresolved
        elec_is_unresolved = False
        if ("electricity_cost" in user_in and user_in["electricity_cost"] is None) or \
           ("utilities_cost" in user_in and user_in["utilities_cost"] is None) or \
           ("power_cost" in user_in and user_in["power_cost"] is None) or \
           ("electricity_status" in user_in and str(user_in["electricity_status"]).upper() in ("UNKNOWN", "UNRESOLVED")):
            elec_is_unresolved = True
        elif "electricity_cost" in asm_map:
            val_e = getattr(asm_map["electricity_cost"], "value", asm_map["electricity_cost"])
            stat_e = getattr(asm_map["electricity_cost"], "status", None)
            stat_str_e = getattr(stat_e, "value", str(stat_e)) if stat_e else ""
            if val_e is None or "UNRESOLVED" in stat_str_e.upper():
                elec_is_unresolved = True

        # Check if marketing is explicitly unknown or unresolved
        mkt_is_unresolved = False
        if ("marketing_cost" in user_in and user_in["marketing_cost"] is None) or \
           ("advertising_cost" in user_in and user_in["advertising_cost"] is None) or \
           ("marketing_status" in user_in and str(user_in["marketing_status"]).upper() in ("UNKNOWN", "UNRESOLVED")):
            mkt_is_unresolved = True
        elif "marketing_cost" in asm_map:
            val_m = getattr(asm_map["marketing_cost"], "value", asm_map["marketing_cost"])
            stat_m = getattr(asm_map["marketing_cost"], "status", None)
            stat_str_m = getattr(stat_m, "value", str(stat_m)) if stat_m else ""
            if val_m is None or "UNRESOLVED" in stat_str_m.upper():
                mkt_is_unresolved = True

        # Check any other OPEX component explicitly provided as None
        other_component_unresolved = any(
            k in user_in and user_in[k] is None
            for k in ("repairs_cost", "maintenance_cost", "admin_cost", "transport_cost", "software_cost", "tech_cost", "other_operating_cost", "misc_opex")
        )

        # Archetype-required material OPEX check
        arch = user_in.get("archetype")
        if not arch:
            sector = user_in.get("sector")
            category = user_in.get("category")
            biz = user_in.get("specific_business") or user_in.get("business_name")
            if sector or category or biz:
                from app.services.financial_engine.intelligence.archetype_registry import archetype_registry
                arch = archetype_registry.resolve(specific_business=biz, sector=sector, category=category)
        
        arch_str = getattr(arch, "value", str(arch)) if arch else ""
        if arch_str in ("INVENTORY_RETAIL", "SMALL_MANUFACTURING", "FOOD_PROCESSING") and elec_annual is None:
            elec_is_unresolved = True

        has_unresolved_opex_component = elec_is_unresolved or mkt_is_unresolved or other_component_unresolved

        # Authoritative aggregate OPEX check
        base_stage9_opex_annual = (
            round(profitability.monthly_operating_expenses * 12.0, 2)
            if profitability and profitability.monthly_operating_expenses is not None
            else None
        )
        if base_stage9_opex_annual is None and user_in.get("monthly_operating_expenses") is not None:
            try:
                base_stage9_opex_annual = round(float(user_in["monthly_operating_expenses"]) * 12.0, 2)
            except (ValueError, TypeError):
                pass

        lines: List[CostProjectionLine] = []

        for r_line in revenue_projection.years:
            y = r_line.year
            rev = r_line.revenue

            # COGS calculation for this year
            year_cogs: Optional[float] = None
            if rev is not None and cogs_ratio is not None:
                year_cogs = round(rev * cogs_ratio, 2)
            elif y == 1 and explicit_cogs is not None:
                year_cogs = round(explicit_cogs, 2)
            elif profitability and profitability.annual_cogs is not None and y == 1:
                year_cogs = round(profitability.annual_cogs, 2)

            # Operating expenses for this year
            total_opex: Optional[float] = None
            if base_stage9_opex_annual is not None:
                # Use authoritative aggregate OPEX
                total_opex = base_stage9_opex_annual
            else:
                # If any material component (salary, rent) is unknown or any OPEX component is unresolved, total OPEX must remain UNKNOWN
                material_components_known = (salary_annual is not None and rent_annual is not None)
                if material_components_known and not has_unresolved_opex_component:
                    known_opex = [
                        v for v in (
                            salary_annual, rent_annual, elec_annual, mkt_annual,
                            repairs_annual, admin_annual, transport_annual, tech_annual, other_opex_annual
                        ) if v is not None
                    ]
                    total_opex = round(sum(known_opex), 2) if known_opex else None
                else:
                    total_opex = None

            status = "RESOLVED" if (year_cogs is not None and total_opex is not None) else "PARTIALLY_DERIVED"
            conf = 0.85 if status == "RESOLVED" else 0.50

            lines.append(
                CostProjectionLine(
                    year=y,
                    cogs=year_cogs,
                    salaries_wages=salary_annual,
                    rent=rent_annual,
                    utilities_electricity=elec_annual,
                    marketing=mkt_annual,
                    repairs_maintenance=repairs_annual,
                    admin_expenses=admin_annual,
                    transport=transport_annual,
                    technology_software=tech_annual,
                    other_operating_expenses=other_opex_annual,
                    total_operating_expenses=total_opex,
                    status=status,
                    confidence=conf
                )
            )

        overall_status = "RESOLVED" if all(l.status == "RESOLVED" for l in lines) else "PARTIALLY_DERIVED"

        return CostProjection(
            status=overall_status,
            years=lines,
            confidence=0.85 if overall_status == "RESOLVED" else 0.60,
            notes="Costs projected from evidenced COGS ratio and itemized operating expenses."
        )


cost_projection_engine = CostProjectionEngine()
