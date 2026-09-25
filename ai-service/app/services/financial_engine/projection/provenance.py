"""
Provenance & Audit Record Builder for Milestone 3.
Constructs auditable provenance records for all major projection line items across all years.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    ProjectionProvenance,
    RevenueProjection,
    CostProjection,
    ProfitLossStatement,
    BalanceSheet,
    WorkingCapitalProjection,
)


class ProvenanceEngine:
    """
    Builds auditable provenance records for financial projection line items.
    """

    @staticmethod
    def build_records(
        revenue_projection: RevenueProjection,
        cost_projection: CostProjection,
        profit_loss: ProfitLossStatement,
        balance_sheet: BalanceSheet,
        working_capital_proj: WorkingCapitalProjection,
    ) -> List[ProjectionProvenance]:
        """
        Creates line-by-line provenance entries.
        """
        records: List[ProjectionProvenance] = []

        # Revenue lines
        for r in revenue_projection.years:
            growth_display = f"{r.growth_rate:.2%}" if r.growth_rate is not None else "UNKNOWN"
            records.append(
                ProjectionProvenance(
                    metric="Revenue",
                    year=r.year,
                    value=r.revenue,
                    source_type=r.growth_source or "BASELINE" if r.revenue is not None else "UNKNOWN",
                    source_ids=[r.growth_source or "BASELINE"] if r.growth_source else [],
                    formula=f"{revenue_projection.methodology} * (1 + {growth_display})" if r.revenue is not None else "Revenue unresolved",
                    driver_ids=[d for d in ["monthly_revenue", "expected_monthly_revenue", "expected_monthly_units", "expected_unit_price"] if d],
                    confidence=r.confidence,
                    status=r.status
                )
            )

        # P&L lines
        for pl in profit_loss.years:
            records.append(
                ProjectionProvenance(
                    metric="EBITDA",
                    year=pl.year,
                    value=pl.ebitda,
                    source_type="CALCULATED",
                    source_ids=["P&L_ENGINE"],
                    formula="Gross Profit - Operating Expenses",
                    driver_ids=["revenue", "cogs", "operating_expenses"],
                    confidence=0.90,
                    status=pl.status
                )
            )
            if pl.profit_after_tax is None:
                pat_formula = "PAT unresolved — tax not modeled" if pl.tax_status == "NOT_MODELED" else "PAT unresolved"
                pat_source = "UNKNOWN"
                pat_status = "PARTIALLY_DERIVED" if pl.tax_status == "NOT_MODELED" else pl.status
            else:
                pat_formula = "PBT - Tax" if pl.tax_status in ("CALCULATED", "ZERO_TAX") else "PBT"
                pat_source = "CALCULATED"
                pat_status = pl.status

            records.append(
                ProjectionProvenance(
                    metric="Profit_After_Tax",
                    year=pl.year,
                    value=pl.profit_after_tax,
                    source_type=pat_source,
                    source_ids=["P&L_ENGINE", pl.tax_status],
                    formula=pat_formula,
                    driver_ids=["ebit", "interest_expense", "income_tax_rate"],
                    confidence=0.85 if pl.profit_after_tax is not None else 0.50,
                    status=pat_status
                )
            )

        # Balance Sheet lines
        for bs in balance_sheet.years:
            bs_line_status = "RESOLVED" if bs.is_balanced else (bs.status if bs.status in ("PARTIALLY_DERIVED", "UNKNOWN", "INSUFFICIENT_DATA") else "FAILED")
            records.append(
                ProjectionProvenance(
                    metric="Total_Assets",
                    year=bs.year,
                    value=bs.total_assets,
                    source_type="CALCULATED" if bs.total_assets is not None else "UNKNOWN",
                    source_ids=["BALANCE_SHEET_ENGINE"],
                    formula="Net PPE + Current Assets (Inventory + Receivables + Cash)",
                    driver_ids=["capex", "inventory", "receivables", "cash"],
                    confidence=0.95 if bs.total_assets is not None else 0.50,
                    status=bs_line_status
                )
            )
            records.append(
                ProjectionProvenance(
                    metric="Total_Liabilities_Equity",
                    year=bs.year,
                    value=bs.total_liabilities_and_equity,
                    source_type="CALCULATED" if bs.total_liabilities_and_equity is not None else "UNKNOWN",
                    source_ids=["BALANCE_SHEET_ENGINE"],
                    formula="Closing Debt + Payables + Equity (Promoter Capital + Retained Earnings)",
                    driver_ids=["term_loan", "payables", "promoter_margin", "retained_earnings"],
                    confidence=0.95 if bs.total_liabilities_and_equity is not None else 0.50,
                    status=bs_line_status
                )
            )

        return records


provenance_engine = ProvenanceEngine()
