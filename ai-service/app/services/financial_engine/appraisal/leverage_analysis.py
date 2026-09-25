"""
Leverage & Capital Structure Analysis Engine for M4 Banking Appraisal.
Deterministically computes Debt-Equity Ratio (DER), TOL/TNW, Debt-to-Assets,
and evaluates leverage reduction trends over the projection horizon.
Strict rule: Does not fabricate Tangible Net Worth or leverage metrics when equity is missing.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    LeverageYear,
    LeverageAnalysisResult,
    AppraisalStatus,
    MetricSource,
    CoverageTrend
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import BalanceSheet, FundingSourcesUses


class LeverageAnalysisEngine:
    """
    Deterministic leverage and solvency appraisal engine.
    """

    def evaluate(
        self,
        balance_sheet: Optional[BalanceSheet] = None,
        sources_uses: Optional[FundingSourcesUses] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> LeverageAnalysisResult:
        prov = provenance or ProvenanceBuilder()

        if not balance_sheet or not balance_sheet.years:
            return LeverageAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                initial_der=None,
                closing_der=None,
                initial_tol_tnw=None,
                leverage_trend=CoverageTrend.NOT_APPLICABLE,
                debt_proportion_of_financing=None,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        years: List[LeverageYear] = []
        valid_der: List[float] = []
        has_unresolved = False

        for bs_y in balance_sheet.years:
            debt = bs_y.term_loan_outstanding
            tnw = bs_y.total_equity
            # Strict non-fabrication: If trade_payables is known but other_current_liabilities is None,
            # current liabilities must remain None. Explicit 0.0 remains 0.0.
            if bs_y.trade_payables is None or bs_y.other_current_liabilities is None:
                cl = None
            else:
                cl = round(bs_y.trade_payables + bs_y.other_current_liabilities, 2)

            if debt is not None and cl is not None:
                tol = round(debt + cl, 2)
            else:
                tol = None
            prom_cap = bs_y.promoter_capital
            tot_assets = bs_y.total_assets

            # DER
            der_val = None
            rc = None

            if tnw is None:
                has_unresolved = True
                rc = ReasonCode.MISSING_NET_WORTH
            elif tnw <= 0.0:
                rc = ReasonCode.ZERO_DENOMINATOR
            elif debt is None:
                has_unresolved = True
                rc = ReasonCode.MISSING_DEBT_SERVICE
            else:
                der_val = round(debt / tnw, 2)
                valid_der.append(der_val)

            # TOL / TNW
            tol_tnw_val = None
            if tol is not None and tnw is not None and tnw > 0:
                tol_tnw_val = round(tol / tnw, 2)

            # Debt to Assets
            d_to_a = None
            if debt is not None and tot_assets is not None and tot_assets > 0:
                d_to_a = round(debt / tot_assets, 2)

            # Promoter contribution ratio
            prom_ratio = None
            if prom_cap is not None and tot_assets is not None and tot_assets > 0:
                prom_ratio = round(prom_cap / tot_assets, 2)

            y_status = AppraisalStatus.RESOLVED if der_val is not None else AppraisalStatus.UNRESOLVED

            years.append(LeverageYear(
                year=bs_y.year,
                total_debt=debt,
                tangible_net_worth=tnw,
                total_outside_liabilities=tol,
                total_assets=tot_assets,
                debt_equity_ratio=der_val,
                tol_tnw_ratio=tol_tnw_val,
                debt_to_assets_ratio=d_to_a,
                promoter_capital=prom_cap,
                promoter_contribution_ratio=prom_ratio,
                status=y_status,
                reason_code=rc
            ))

        init_der = valid_der[0] if valid_der else None
        close_der = valid_der[-1] if valid_der else None
        init_tol_tnw = years[0].tol_tnw_ratio if years and years[0].tol_tnw_ratio is not None else None

        # Trend (reducing DER is IMPROVING)
        if len(valid_der) >= 2:
            if close_der is not None and init_der is not None:
                if close_der < init_der - 0.05:
                    trend = CoverageTrend.IMPROVING
                elif close_der > init_der + 0.05:
                    trend = CoverageTrend.DETERIORATING
                else:
                    trend = CoverageTrend.STABLE
            else:
                trend = CoverageTrend.STABLE
        else:
            trend = CoverageTrend.STABLE

        # Debt proportion of total financing
        debt_prop = None
        if sources_uses and sources_uses.total_sources and sources_uses.total_sources > 0:
            if sources_uses.term_loan is not None:
                debt_prop = round(sources_uses.term_loan / sources_uses.total_sources, 4)

        prov.record(
            metric="initial_debt_equity_ratio",
            value=init_der,
            source=MetricSource.DERIVED,
            source_reference="BalanceSheet Year 1 (Total Debt / Tangible Net Worth)",
            calculation_method="Year 1 DER",
            status=AppraisalStatus.RESOLVED if init_der is not None else AppraisalStatus.UNRESOLVED,
            dependencies=["balance_sheet"]
        )

        overall_status = AppraisalStatus.RESOLVED if (years and years[0].status == AppraisalStatus.RESOLVED) else (
            AppraisalStatus.PARTIALLY_DERIVED if has_unresolved else AppraisalStatus.UNRESOLVED
        )

        return LeverageAnalysisResult(
            status=overall_status,
            years=years,
            initial_der=init_der,
            closing_der=close_der,
            initial_tol_tnw=init_tol_tnw,
            leverage_trend=trend,
            debt_proportion_of_financing=debt_prop,
            reason_code=ReasonCode.MISSING_NET_WORTH if not valid_der else None
        )


leverage_analysis_engine = LeverageAnalysisEngine()
