"""
Debt Service Analysis Engine for M4 Banking Appraisal.
Deterministically computes year-wise opening debt, principal repayment, interest repayment,
total debt service, closing debt, and EMI burden ratio.
Handles explicit zero-debt enterprises structurally without failure.
"""
from typing import List, Optional, Dict, Any
from app.services.financial_engine.appraisal.appraisal_schema import (
    DebtServiceYear,
    DebtServiceAnalysisResult,
    AppraisalStatus,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.services.financial_engine.appraisal.provenance import ProvenanceBuilder
from app.schemas.financial_analysis import (
    RepaymentSchedule,
    LoanManagement,
    ProfitLossStatement,
    BalanceSheet,
    RevenueProjection
)


class DebtServiceEngine:
    """
    Deterministic debt service evaluation engine.
    """

    def evaluate(
        self,
        projection_years: int = 5,
        loan_management: Optional[LoanManagement] = None,
        repayment_schedule: Optional[RepaymentSchedule] = None,
        profit_loss: Optional[ProfitLossStatement] = None,
        balance_sheet: Optional[BalanceSheet] = None,
        revenue_projection: Optional[RevenueProjection] = None,
        provenance: Optional[ProvenanceBuilder] = None
    ) -> DebtServiceAnalysisResult:
        prov = provenance or ProvenanceBuilder()

        # Case 1: Explicit Zero Debt
        if loan_management is not None and loan_management.principal == 0.0:
            years: List[DebtServiceYear] = []
            for y in range(1, projection_years + 1):
                years.append(DebtServiceYear(
                    year=y,
                    opening_debt=0.0,
                    principal_repayment=0.0,
                    interest_repayment=0.0,
                    total_debt_service=0.0,
                    closing_debt=0.0,
                    emi_burden_ratio=0.0,
                    status=AppraisalStatus.RESOLVED,
                    reason_code=ReasonCode.ZERO_DEBT
                ))
            prov.record(
                metric="total_debt_service",
                value=0.0,
                source=MetricSource.STAGE9,
                source_reference="loan_management.principal == 0",
                calculation_method="Zero debt enterprise",
                status=AppraisalStatus.RESOLVED
            )
            return DebtServiceAnalysisResult(
                status=AppraisalStatus.RESOLVED,
                years=years,
                total_principal=0.0,
                total_interest=0.0,
                total_debt_service=0.0,
                average_annual_debt_service=0.0,
                opening_debt_total=0.0,
                closing_debt_final=0.0,
                is_zero_debt=True,
                reason_code=ReasonCode.ZERO_DEBT
            )

        # Case 2: Authoritative Stage 9 Repayment Schedule available
        if repayment_schedule and repayment_schedule.monthly_schedule:
            monthly_rows = repayment_schedule.monthly_schedule
            years = []
            total_princ = 0.0
            total_int = 0.0
            total_ds = 0.0
            initial_opening = monthly_rows[0].opening_balance if monthly_rows else 0.0

            rev_by_year: Dict[int, float] = {}
            if revenue_projection and revenue_projection.years:
                for ry in revenue_projection.years:
                    if ry.revenue is not None:
                        rev_by_year[ry.year] = ry.revenue

            for y in range(1, projection_years + 1):
                start_m = (y - 1) * 12 + 1
                end_m = y * 12
                y_months = [r for r in monthly_rows if start_m <= r.period <= end_m]

                if y_months:
                    y_open = y_months[0].opening_balance
                    y_princ = sum(r.principal_component for r in y_months)
                    y_int = sum(r.interest_component for r in y_months)
                    y_tot = y_princ + y_int
                    y_close = y_months[-1].closing_balance
                else:
                    # Beyond loan tenure
                    y_open = 0.0
                    y_princ = 0.0
                    y_int = 0.0
                    y_tot = 0.0
                    y_close = 0.0

                rev = rev_by_year.get(y)
                burden = round(y_tot / rev, 4) if (rev is not None and rev > 0) else None

                years.append(DebtServiceYear(
                    year=y,
                    opening_debt=round(y_open, 2),
                    principal_repayment=round(y_princ, 2),
                    interest_repayment=round(y_int, 2),
                    total_debt_service=round(y_tot, 2),
                    closing_debt=round(y_close, 2),
                    emi_burden_ratio=burden,
                    status=AppraisalStatus.RESOLVED
                ))

                total_princ += y_princ
                total_int += y_int
                total_ds += y_tot

            final_closing = years[-1].closing_debt if years else 0.0
            avg_ds = round(total_ds / projection_years, 2) if projection_years > 0 else 0.0

            lifetime_princ = round(sum(r.principal_component for r in monthly_rows), 2)
            lifetime_int = round(sum(r.interest_component for r in monthly_rows), 2)

            prov.record(
                metric="total_debt_service",
                value=round(total_ds, 2),
                source=MetricSource.STAGE9,
                source_reference="repayment_schedule.monthly_schedule",
                calculation_method="Sum of monthly principal + interest",
                status=AppraisalStatus.RESOLVED,
                dependencies=["loan_management", "repayment_schedule"]
            )

            return DebtServiceAnalysisResult(
                status=AppraisalStatus.RESOLVED,
                years=years,
                total_principal=round(total_princ, 2),
                total_interest=round(total_int, 2),
                total_debt_service=round(total_ds, 2),
                total_principal_lifetime=lifetime_princ,
                total_interest_lifetime=lifetime_int,
                average_annual_debt_service=avg_ds,
                opening_debt_total=round(initial_opening, 2),
                closing_debt_final=round(final_closing, 2),
                is_zero_debt=False
            )

        # Case 3: Missing Debt Schedule and Positive Loan
        return DebtServiceAnalysisResult(
            status=AppraisalStatus.UNRESOLVED,
            years=[],
            total_principal=None,
            total_interest=None,
            total_debt_service=None,
            average_annual_debt_service=None,
            opening_debt_total=None,
            closing_debt_final=None,
            is_zero_debt=False,
            reason_code=ReasonCode.MISSING_DEBT_SERVICE
        )


debt_service_engine = DebtServiceEngine()
