"""
Profitability Analysis Engine for M4 Banking Appraisal.
Deterministically computes year-wise margins (Gross, EBITDA, EBIT, Net),
ROCE, ROE, and ROA strictly from resolved M3 statements.
Strict rule: Does not force ratios when denominators are zero or unresolved.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    ProfitabilityYear,
    ProfitabilityAnalysisResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import ProfitLossStatement, BalanceSheet


class ProfitabilityAnalysisEngine:
    """
    Deterministic profitability appraisal engine.
    """

    def evaluate(
        self,
        profit_loss: Optional[ProfitLossStatement] = None,
        balance_sheet: Optional[BalanceSheet] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> ProfitabilityAnalysisResult:
        prov = provenance or ProvenanceBuilder()

        if not profit_loss or not profit_loss.years:
            return ProfitabilityAnalysisResult(
                status=AppraisalStatus.UNRESOLVED,
                years=[],
                average_gross_margin_pct=None,
                average_ebitda_margin_pct=None,
                average_ebit_margin_pct=None,
                average_net_profit_margin_pct=None,
                average_roce_pct=None,
                average_roe_pct=None,
                average_roa_pct=None,
                reason_code=ReasonCode.INSUFFICIENT_DATA
            )

        bs_years_map = {y.year: y for y in balance_sheet.years} if balance_sheet and balance_sheet.years else {}

        years: List[ProfitabilityYear] = []
        valid_gm: List[float] = []
        valid_ebitda_m: List[float] = []
        valid_ebit_m: List[float] = []
        valid_npm: List[float] = []
        valid_roce: List[float] = []
        valid_roe: List[float] = []
        valid_roa: List[float] = []
        has_unresolved = False

        for pl_y in profit_loss.years:
            rev = pl_y.revenue
            gp = pl_y.gross_profit
            ebitda = pl_y.ebitda
            ebit = pl_y.ebit
            pat = pl_y.profit_after_tax

            bs_y = bs_years_map.get(pl_y.year)
            tot_assets = bs_y.total_assets if bs_y else None
            equity = bs_y.total_equity if bs_y else None
            debt = bs_y.term_loan_outstanding if bs_y else None

            # 1. Margins
            gm_pct = None
            ebitda_pct = None
            ebit_pct = None
            npm_pct = None
            rc = None

            if rev is None:
                has_unresolved = True
                rc = ReasonCode.MISSING_REVENUE
            elif rev <= 0:
                rc = ReasonCode.ZERO_DENOMINATOR
            else:
                if gp is not None:
                    gm_pct = round((gp / rev) * 100.0, 2)
                    valid_gm.append(gm_pct)
                if ebitda is not None:
                    ebitda_pct = round((ebitda / rev) * 100.0, 2)
                    valid_ebitda_m.append(ebitda_pct)
                if ebit is not None:
                    ebit_pct = round((ebit / rev) * 100.0, 2)
                    valid_ebit_m.append(ebit_pct)
                if pat is not None:
                    npm_pct = round((pat / rev) * 100.0, 2)
                    valid_npm.append(npm_pct)

            # 2. Return Ratios
            roce_pct = None
            if ebit is not None and equity is not None and debt is not None:
                cap_employed = equity + debt
                if cap_employed > 0:
                    roce_pct = round((ebit / cap_employed) * 100.0, 2)
                    valid_roce.append(roce_pct)

            roe_pct = None
            if pat is not None and equity is not None:
                if equity > 0:
                    roe_pct = round((pat / equity) * 100.0, 2)
                    valid_roe.append(roe_pct)

            roa_pct = None
            if pat is not None and tot_assets is not None:
                if tot_assets > 0:
                    roa_pct = round((pat / tot_assets) * 100.0, 2)
                    valid_roa.append(roa_pct)

            y_status = AppraisalStatus.RESOLVED if rev is not None and rev > 0 else (
                AppraisalStatus.NOT_APPLICABLE if rev is not None else AppraisalStatus.UNRESOLVED
            )

            years.append(ProfitabilityYear(
                year=pl_y.year,
                revenue=rev,
                gross_profit=gp,
                gross_margin_pct=gm_pct,
                ebitda=ebitda,
                ebitda_margin_pct=ebitda_pct,
                ebit=ebit,
                ebit_margin_pct=ebit_pct,
                pat=pat,
                net_profit_margin_pct=npm_pct,
                roce_pct=roce_pct,
                roe_pct=roe_pct,
                roa_pct=roa_pct,
                status=y_status,
                reason_code=rc
            ))

        avg_gm = round(sum(valid_gm) / len(valid_gm), 2) if valid_gm else None
        avg_ebitda = round(sum(valid_ebitda_m) / len(valid_ebitda_m), 2) if valid_ebitda_m else None
        avg_ebit = round(sum(valid_ebit_m) / len(valid_ebit_m), 2) if valid_ebit_m else None
        avg_npm = round(sum(valid_npm) / len(valid_npm), 2) if valid_npm else None
        avg_roce = round(sum(valid_roce) / len(valid_roce), 2) if valid_roce else None
        avg_roe = round(sum(valid_roe) / len(valid_roe), 2) if valid_roe else None
        avg_roa = round(sum(valid_roa) / len(valid_roa), 2) if valid_roa else None

        prov.record(
            metric="average_net_profit_margin_pct",
            value=avg_npm,
            source=MetricSource.DERIVED,
            source_reference="ProfitLossStatement (PAT / Revenue)",
            calculation_method="Average Net Profit Margin",
            status=AppraisalStatus.RESOLVED if avg_npm is not None else AppraisalStatus.UNRESOLVED,
            dependencies=["profit_loss_statement"]
        )

        overall_status = AppraisalStatus.RESOLVED if (years and years[0].status == AppraisalStatus.RESOLVED) else (
            AppraisalStatus.PARTIALLY_DERIVED if has_unresolved else AppraisalStatus.UNRESOLVED
        )

        return ProfitabilityAnalysisResult(
            status=overall_status,
            years=years,
            average_gross_margin_pct=avg_gm,
            average_ebitda_margin_pct=avg_ebitda,
            average_ebit_margin_pct=avg_ebit,
            average_net_profit_margin_pct=avg_npm,
            average_roce_pct=avg_roce,
            average_roe_pct=avg_roe,
            average_roa_pct=avg_roa,
            reason_code=ReasonCode.INSUFFICIENT_DATA if not valid_npm else None
        )


profitability_analysis_engine = ProfitabilityAnalysisEngine()
