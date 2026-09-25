"""
Profit & Loss Statement Engine for Milestone 3.
Generates institutional multi-year P&L statement (Revenue -> EBITDA -> EBIT -> PBT -> PAT).
Tax abstraction preserves UNKNOWN / NOT_MODELED without fabricating rates.
Reconciles interest expense directly with Stage 9 loan amortization.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    ProfitLossStatement,
    ProfitLossYear,
    RevenueProjection,
    CostProjection,
    RepaymentSchedule,
    FundingSourcesUses,
)
from app.services.financial_engine.projection.depreciation import DepreciationEngine, DepreciationScheduleYear
from app.services.financial_engine.projection.tax_policy import tax_policy_resolver


class ProfitLossEngine:
    """
    Constructs multi-year Profit and Loss Statement.
    """

    @staticmethod
    def generate(
        revenue_projection: RevenueProjection,
        cost_projection: CostProjection,
        depreciation_schedule: Dict[int, DepreciationScheduleYear],
        repayment_schedule: Optional[RepaymentSchedule] = None,
        sources_uses: Optional[FundingSourcesUses] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        tax_rate: Optional[float] = None,
        business_profile: Optional[Any] = None,
    ) -> ProfitLossStatement:
        """
        Builds Year 1..N P&L Statement.
        """
        user_in = user_inputs or {}

        # Sourced tax rate (Explicit external tax_rate override only; otherwise authoritative tax_policy_resolver handles it)
        resolved_tax_rate: Optional[float] = tax_rate
        if resolved_tax_rate is None:
            raw_tax = user_in.get("income_tax_rate") if "income_tax_rate" in user_in else user_in.get("tax_rate")
            if raw_tax is not None:
                try:
                    resolved_tax_rate = float(raw_tax)
                    if resolved_tax_rate > 1.0:
                        resolved_tax_rate = resolved_tax_rate / 100.0
                except (ValueError, TypeError):
                    pass

        is_tax_exempt = bool(user_in.get("is_tax_exempt") or user_in.get("tax_exempt") or (resolved_tax_rate == 0.0))

        # Extract scheduled interest per projection year
        interest_by_year: Dict[int, Optional[float]] = {}
        has_schedule = repayment_schedule is not None and bool(repayment_schedule.monthly_schedule)

        if has_schedule:
            for row in repayment_schedule.monthly_schedule:
                y = (row.period - 1) // 12 + 1
                val = getattr(row, "interest_component", None)
                if val is None:
                    val = getattr(row, "interest_paid", None)
                
                if y in interest_by_year and interest_by_year[y] is None:
                    continue
                if val is None:
                    interest_by_year[y] = None
                else:
                    curr = interest_by_year.get(y)
                    interest_by_year[y] = round((curr if curr is not None else 0.0) + float(val), 2)
        elif sources_uses is not None and sources_uses.term_loan == 0.0:
            for y in range(1, len(revenue_projection.years) + 1):
                interest_by_year[y] = 0.0
        elif user_in.get("term_loan") == 0.0 or user_in.get("loan_amount") == 0.0:
            for y in range(1, len(revenue_projection.years) + 1):
                interest_by_year[y] = 0.0
        elif user_in.get("annual_interest_expense") is not None:
            exp_int = float(user_in["annual_interest_expense"])
            for y in range(1, len(revenue_projection.years) + 1):
                interest_by_year[y] = exp_int
        else:
            # Debt exists or is unevidenced, but repayment schedule cannot be resolved
            for y in range(1, len(revenue_projection.years) + 1):
                interest_by_year[y] = None

        years: List[ProfitLossYear] = []
        cost_map = {l.year: l for l in cost_projection.years}

        for r_line in revenue_projection.years:
            y = r_line.year
            rev = r_line.revenue
            c_line = cost_map.get(y)

            cogs = c_line.cogs if c_line else None
            opex = c_line.total_operating_expenses if c_line else None

            # 1. Gross Profit
            gross_profit: Optional[float] = None
            gross_margin: Optional[float] = None
            if rev is not None and cogs is not None:
                gross_profit = round(rev - cogs, 2)
                if rev > 0:
                    gross_margin = round((gross_profit / rev) * 100.0, 2)

            # 2. EBITDA
            ebitda: Optional[float] = None
            ebitda_margin: Optional[float] = None
            if gross_profit is not None and opex is not None:
                ebitda = round(gross_profit - opex, 2)
                if rev is not None and rev > 0:
                    ebitda_margin = round((ebitda / rev) * 100.0, 2)

            # 3. Depreciation
            depr_info = depreciation_schedule.get(y)
            depr: Optional[float] = None
            if depr_info is not None and depr_info.depreciation_amount is not None:
                depr = depr_info.depreciation_amount

            # 4. EBIT
            ebit: Optional[float] = None
            if ebitda is not None:
                if depr is not None:
                    ebit = round(ebitda - depr, 2)
                else:
                    # Depreciation unknown — EBIT cannot be fully resolved
                    ebit = None

            # 5. Interest Expense
            interest = interest_by_year.get(y)

            # 6. Profit Before Tax
            pbt: Optional[float] = None
            if ebit is not None and interest is not None:
                pbt = round(ebit - interest, 2)

            # 7. Tax & Profit After Tax
            tax_exp: Optional[float] = None
            tax_status = "NOT_MODELED"
            pat: Optional[float] = None
            net_margin: Optional[float] = None

            if is_tax_exempt or resolved_tax_rate == 0.0:
                tax_status = "EXEMPT"
                tax_exp = 0.0
                pat = pbt
            elif resolved_tax_rate is not None and resolved_tax_rate > 0.0:
                tax_status = "EXPLICIT_RATE_OVERRIDE"
                if pbt is not None:
                    tax_exp = round(max(0.0, pbt) * resolved_tax_rate, 2)
                    pat = round(pbt - tax_exp, 2)
                else:
                    tax_exp = None
                    pat = None
            elif pbt is not None:
                effective_biz = business_profile or user_in.get("business_profile") or {}
                raw_const = (
                    user_in.get("business_constitution")
                    or user_in.get("constitution")
                    or user_in.get("entity_type")
                    or user_in.get("registration_type")
                    or (effective_biz.get("business_constitution") if isinstance(effective_biz, dict) else getattr(effective_biz, "business_constitution", None))
                    or (effective_biz.get("constitution") if isinstance(effective_biz, dict) else getattr(effective_biz, "constitution", None))
                    or (effective_biz.get("entity_type") if isinstance(effective_biz, dict) else getattr(effective_biz, "entity_type", None))
                    or (effective_biz.get("registration_type") if isinstance(effective_biz, dict) else getattr(effective_biz, "registration_type", None))
                )
                if not raw_const:
                    # Entity constitution unevidenced: do not silently default to sole proprietorship or fabricate tax
                    tax_status = "PROVISIONAL_PENDING_REGISTRATION"
                    tax_exp = None
                    pat = None
                else:
                    # Automatically resolve statutory tax regime based on constitution + turnover + PBT
                    sec_name = user_in.get("sector") or (effective_biz.get("sector") if isinstance(effective_biz, dict) else getattr(effective_biz, "sector", None))
                    cat_name = user_in.get("category") or (effective_biz.get("category") if isinstance(effective_biz, dict) else getattr(effective_biz, "category", None))
                    subcat_name = user_in.get("subcategory") or (effective_biz.get("subcategory") if isinstance(effective_biz, dict) else getattr(effective_biz, "subcategory", None))
                    spec_name = user_in.get("specific_business") or (effective_biz.get("specific_business") if isinstance(effective_biz, dict) else getattr(effective_biz, "specific_business", None))

                    tax_res = tax_policy_resolver.resolve_tax(
                        pbt=pbt,
                        annual_revenue=rev,
                        business_constitution=raw_const,
                        sector=sec_name,
                        category=cat_name,
                        subcategory=subcat_name,
                        specific_business=spec_name,
                        user_inputs=user_in,
                    )
                    tax_exp = tax_res.annual_tax_expense
                    tax_status = tax_res.tax_regime
                    pat = round(pbt - tax_exp, 2)
            else:
                tax_status = "NOT_MODELED"
                tax_exp = None
                pat = None

            if rev is not None and rev > 0 and pat is not None:
                net_margin = round((pat / rev) * 100.0, 2)

            status = "RESOLVED" if (rev is not None and pat is not None) else "PARTIALLY_DERIVED"

            years.append(
                ProfitLossYear(
                    year=y,
                    revenue=rev,
                    cogs=cogs,
                    gross_profit=gross_profit,
                    gross_margin_percentage=gross_margin,
                    operating_expenses=opex,
                    ebitda=ebitda,
                    ebitda_margin_percentage=ebitda_margin,
                    depreciation=depr,
                    ebit=ebit,
                    interest_expense=interest,
                    profit_before_tax=pbt,
                    tax_expense=tax_exp,
                    tax_status=tax_status,
                    profit_after_tax=pat,
                    net_margin_percentage=net_margin,
                    status=status
                )
            )

        overall_status = "RESOLVED" if all(y.status == "RESOLVED" for y in years) else "PARTIALLY_DERIVED"
        return ProfitLossStatement(
            status=overall_status,
            years=years,
            notes=f"P&L projected over {len(years)} years with tax status '{tax_status}'."
        )


profit_loss_engine = ProfitLossEngine()
