"""
Driver-Based Revenue Projection Engine for Milestone 3.
Implements multi-year revenue modeling with strictly sourced growth and operational drivers.
Zero invented growth rates. Zero arbitrary defaults.
"""
from typing import Dict, Any, List, Optional, Union
from app.schemas.financial_analysis import (
    RevenueProjection,
    RevenueProjectionLine,
    ProjectAssumptionsInput,
    ProfitabilityProjection,
)
from app.services.financial_engine.benchmark_adapter import BenchmarkFinancialData


from app.services.financial_engine.projection.revenue_resolver import revenue_projection_resolver


class RevenueProjectionEngine:
    """
    Constructs multi-year driver-based revenue projections.
    """

    @staticmethod
    def project(
        projection_years: int = 5,
        project_assumptions: Optional[ProjectAssumptionsInput] = None,
        profitability: Optional[ProfitabilityProjection] = None,
        benchmark_data: Optional[BenchmarkFinancialData] = None,
        assumptions_map: Optional[Dict[str, Any]] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        business_profile: Optional[Any] = None,
        market_data: Optional[Dict[str, Any]] = None,
        allow_flat_base_case: bool = False,
    ) -> RevenueProjection:
        """
        Projects revenue across 1..N operating years based strictly on evidenced parameters.
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

        # 1. Determine Year 1 Base Revenue
        monthly_rev: Optional[float] = None
        annual_rev: Optional[float] = None
        base_volume: Optional[float] = None
        base_price: Optional[float] = None
        methodology = "ANNUAL_TOTAL"
        confidence = 0.85

        # Check explicit units * price
        units = get_val("monthly_units")
        if units is None:
            units = get_val("expected_monthly_units")
        if units is None:
            units = get_val("monthly_transactions")
        if units is None:
            daily_cust = get_val("daily_customers")
            if daily_cust is not None:
                op_days = get_val("operating_days")
                if op_days is not None:
                    units = daily_cust * op_days
                else:
                    units = None

        price = get_val("expected_unit_price")
        if price is None:
            price = get_val("selling_price")
        if price is None:
            price = get_val("average_ticket")
        if price is None:
            price = get_val("average_order_value")

        if units is not None and price is not None and units >= 0 and price >= 0:
            monthly_rev = round(units * price, 2)
            annual_rev = round(monthly_rev * 12.0, 2)
            base_volume = units * 12.0
            base_price = price
            methodology = "VOLUME_X_PRICE"
            confidence = 0.90
        elif (
            getattr(project_assumptions, "expected_monthly_revenue", None) is not None
            or (isinstance(project_assumptions, dict) and project_assumptions.get("expected_monthly_revenue") is not None)
        ):
            raw_rev = getattr(project_assumptions, "expected_monthly_revenue", None)
            if raw_rev is None and isinstance(project_assumptions, dict):
                raw_rev = project_assumptions.get("expected_monthly_revenue")
            if raw_rev is not None and raw_rev >= 0:
                monthly_rev = round(float(raw_rev), 2)
                annual_rev = round(monthly_rev * 12.0, 2)
                methodology = "MONTHLY_AGGREGATED"
                confidence = 0.90
        elif profitability and profitability.annual_revenue is not None and profitability.annual_revenue >= 0:
            annual_rev = round(float(profitability.annual_revenue), 2)
            monthly_rev = profitability.monthly_revenue
            methodology = "STAGE9_PROFITABILITY_BASIS"
            confidence = 0.85
        elif get_val("monthly_revenue") is not None and get_val("monthly_revenue") >= 0:
            monthly_rev = round(float(get_val("monthly_revenue")), 2)
            annual_rev = round(monthly_rev * 12.0, 2)
            methodology = "RESOLVED_DRIVER_BASIS"
            confidence = 0.85

        if annual_rev is None:
            # Unresolved revenue
            lines = []
            for y in range(1, projection_years + 1):
                lines.append(
                    RevenueProjectionLine(
                        year=y,
                        volume=None,
                        price_per_unit=None,
                        revenue=None,
                        growth_rate=None,
                        growth_source=None,
                        growth_method="UNRESOLVED",
                        status="UNKNOWN",
                        confidence=0.0
                    )
                )
            return RevenueProjection(
                status="INSUFFICIENT_DATA",
                methodology="UNRESOLVED",
                base_annual_revenue=None,
                years=lines,
                confidence=0.0,
                notes="Revenue parameters are missing or insufficient to construct projections."
            )

        # 2. Sourced Growth Rate Resolution via Centralized Resolver
        effective_mkt = market_data or user_in.get("market_data") or user_in.get("stage6_market_intelligence")
        effective_biz = business_profile or user_in.get("business_profile")
        growth_assumptions = revenue_projection_resolver.resolve_growth_schedule(
            projection_years=projection_years,
            project_assumptions=project_assumptions,
            benchmark_data=benchmark_data,
            market_data=effective_mkt,
            business_profile=effective_biz,
            user_inputs=user_in,
        )
        growth_by_year = {ga.year: ga for ga in growth_assumptions}

        # 3. Generate Projection Years
        lines: List[RevenueProjectionLine] = []
        current_rev = annual_rev
        current_vol = base_volume

        for y in range(1, projection_years + 1):
            if y == 1:
                year_growth = 0.0
                g_src = "BASELINE"
                g_meth = "YEAR_1_BASE"
                y_conf = confidence
            else:
                ga = growth_by_year.get(y)
                has_evidenced_growth = ga is not None and ga.source_type in ("USER_INPUT", "MARKET_INTELLIGENCE", "INDUSTRY_BENCHMARK")
                has_biz_context = bool(
                    effective_biz
                    or benchmark_data
                    or effective_mkt
                    or user_in.get("sector")
                    or user_in.get("category")
                    or user_in.get("business_id")
                )
                if allow_flat_base_case is True:
                    year_growth = 0.0
                    g_src = "POLICY_SCENARIO"
                    g_meth = "EXPLICIT_FLAT_GROWTH_POLICY"
                    y_conf = 0.70
                    current_rev = round(current_rev * 1.0, 2)
                    if current_vol is not None:
                        current_vol = round(current_vol * 1.0, 2)
                elif has_evidenced_growth and ga is not None and ga.growth_rate is not None:
                    year_growth = ga.growth_rate
                    g_src = ga.source_type
                    g_meth = ga.method
                    y_conf = ga.confidence
                    current_rev = round(current_rev * (1.0 + year_growth), 2)
                    if current_vol is not None:
                        current_vol = round(current_vol * (1.0 + year_growth), 2)
                elif has_biz_context and ga is not None and ga.growth_rate is not None:
                    # Sector policy schedule applied when business context is present
                    year_growth = ga.growth_rate
                    g_src = ga.source_type
                    g_meth = ga.method
                    y_conf = ga.confidence
                    current_rev = round(current_rev * (1.0 + year_growth), 2)
                    if current_vol is not None:
                        current_vol = round(current_vol * (1.0 + year_growth), 2)
                else:
                    # Growth is genuinely UNKNOWN (no growth evidence and no business context or flat base disallowed)
                    current_rev = None
                    year_growth = None
                    g_src = "UNKNOWN"
                    g_meth = "UNKNOWN_GROWTH"
                    y_conf = 0.0

            lines.append(
                RevenueProjectionLine(
                    year=y,
                    volume=current_vol if current_rev is not None else None,
                    price_per_unit=base_price if current_rev is not None else None,
                    revenue=current_rev,
                    growth_rate=year_growth,
                    growth_source=g_src,
                    growth_method=g_meth,
                    status="RESOLVED" if current_rev is not None else "UNKNOWN",
                    confidence=y_conf if current_rev is not None else 0.0
                )
            )

        resolved_count = sum(1 for l in lines if l.revenue is not None)
        overall_status = "RESOLVED" if resolved_count == len(lines) else ("PARTIALLY_DERIVED" if resolved_count > 0 else "INSUFFICIENT_DATA")

        return RevenueProjection(
            status=overall_status,
            methodology=methodology,
            base_annual_revenue=annual_rev,
            years=lines,
            confidence=confidence,
            notes=f"Revenue projected using {methodology} with multi-tier deterministic growth policy."
        )


revenue_projection_engine = RevenueProjectionEngine()

