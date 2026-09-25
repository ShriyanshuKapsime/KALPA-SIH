"""
Accounting Invariants & Validation Engine for Milestone 3.
Validates the 12 mandatory accounting checks across all projection years.
Reports check_id, status, expected, actual, difference, tolerance, severity, and message.
"""
from typing import Dict, Any, List, Optional
from app.schemas.financial_analysis import (
    ProjectionValidation,
    ProjectionValidationCheck,
    FundingSourcesUses,
    BalanceSheet,
    CashFlowStatement,
    ProfitLossStatement,
    WorkingCapitalProjection,
    FinancialRatioSet,
    RepaymentSchedule,
)


class ValidationEngine:
    """
    Validates institutional accounting invariants across projection statements.
    """

    @staticmethod
    def validate(
        sources_uses: FundingSourcesUses,
        balance_sheet: BalanceSheet,
        cash_flow: CashFlowStatement,
        profit_loss: ProfitLossStatement,
        working_capital_proj: WorkingCapitalProjection,
        financial_ratios: FinancialRatioSet,
        repayment_schedule: Optional[RepaymentSchedule] = None,
        tolerance: float = 1.0,
    ) -> ProjectionValidation:
        """
        Executes Checks 1 through 12.
        """
        checks: List[ProjectionValidationCheck] = []

        # ---------------------------------------------------------------------
        # CHECK 1: Sources = Uses
        # ---------------------------------------------------------------------
        diff_1: Optional[float] = None
        if sources_uses.total_sources is not None and sources_uses.total_uses is not None:
            diff_1 = round(abs(sources_uses.total_sources - sources_uses.total_uses), 2)
            passed_1 = diff_1 <= tolerance
            status_1 = "PASSED" if passed_1 else "FAILED"
            msg_1 = "Funding sources perfectly equal project uses." if passed_1 else f"Sources ({sources_uses.total_sources}) != Uses ({sources_uses.total_uses})"
        else:
            status_1 = "UNRESOLVED"
            msg_1 = "Funding sources or uses incomplete / unresolvable."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_1_SOURCES_USES",
                status=status_1,
                expected=sources_uses.total_uses,
                actual=sources_uses.total_sources,
                difference=diff_1,
                tolerance=tolerance,
                severity="CRITICAL",
                message=msg_1
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 2: Assets = Liabilities + Equity (for every year)
        # ---------------------------------------------------------------------
        has_bs_failure = False
        has_bs_unresolved = False
        max_bs_diff = 0.0
        if not balance_sheet.years:
            has_bs_unresolved = True
        for bs_y in balance_sheet.years:
            diff_val = bs_y.reconciliation_difference
            if diff_val is None and bs_y.total_assets is not None and bs_y.total_liabilities_and_equity is not None:
                diff_val = round(bs_y.total_assets - bs_y.total_liabilities_and_equity, 2)

            if diff_val is not None:
                diff = abs(diff_val)
                if diff > max_bs_diff:
                    max_bs_diff = diff
                if diff > tolerance:
                    has_bs_failure = True
            else:
                has_bs_unresolved = True

        if has_bs_failure:
            status_2 = "FAILED"
            bs_msg = f"Balance sheet mismatch detected (max diff: ₹{max_bs_diff:,.2f})"
        elif has_bs_unresolved:
            status_2 = "UNRESOLVED"
            bs_msg = "Balance sheet contains unresolvable years due to missing components."
        else:
            status_2 = "PASSED"
            bs_msg = "Balance sheet balances across all projection years."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_2_BALANCE_SHEET_EQUALITY",
                status=status_2,
                expected="Total Assets",
                actual="Total Liabilities + Equity",
                difference=round(max_bs_diff, 2) if not has_bs_unresolved else None,
                tolerance=tolerance,
                severity="CRITICAL",
                message=bs_msg
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 3: Opening Cash + Net Cash Flow = Closing Cash
        # ---------------------------------------------------------------------
        has_cf_failure = False
        has_cf_unresolved = False
        max_cf_diff = 0.0
        if not cash_flow.years:
            has_cf_unresolved = True
        for cf_y in cash_flow.years:
            if cf_y.opening_cash_balance is not None and cf_y.net_change_in_cash is not None and cf_y.closing_cash_balance is not None:
                calc_closing = round(cf_y.opening_cash_balance + cf_y.net_change_in_cash, 2)
                diff = round(abs(calc_closing - cf_y.closing_cash_balance), 2)
                if diff > max_cf_diff:
                    max_cf_diff = diff
                if diff > 0.05:
                    has_cf_failure = True
            else:
                has_cf_unresolved = True

        if has_cf_failure:
            status_3 = "FAILED"
            msg_3 = f"Cash continuity mismatch (max diff: ₹{max_cf_diff:,.2f})"
        elif has_cf_unresolved:
            status_3 = "UNRESOLVED"
            msg_3 = "Cash flow continuity unresolved due to missing cash components."
        else:
            status_3 = "PASSED"
            msg_3 = "Cash flow equation holds for all years."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_3_CASH_FLOW_CONTINUITY",
                status=status_3,
                expected="Opening Cash + Net Change",
                actual="Closing Cash",
                difference=round(max_cf_diff, 2) if not has_cf_unresolved else None,
                tolerance=0.05,
                severity="CRITICAL",
                message=msg_3
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 4: Opening Debt - Principal Repaid = Closing Debt
        # ---------------------------------------------------------------------
        has_debt_failure = False
        has_debt_unresolved = False
        max_debt_diff = 0.0
        cf_repaid_map = {c.year: c.principal_repayment for c in cash_flow.years}
        prev_debt = sources_uses.term_loan

        is_structurally_zero_debt = (
            sources_uses.term_loan == 0.0
            and all(getattr(b, "term_loan_outstanding", 0.0) in (0.0, None) for b in balance_sheet.years)
        )
        if is_structurally_zero_debt:
            status_4 = "PASSED"
            msg_4 = "No term debt present; debt schedule is structurally zero."
        elif not balance_sheet.years or prev_debt is None:
            status_4 = "UNRESOLVED"
            msg_4 = "Debt reduction unresolvable due to missing opening debt or projection years."
        else:
            for bs_y in balance_sheet.years:
                repaid = cf_repaid_map.get(bs_y.year)
                cur_debt = bs_y.term_loan_outstanding
                if prev_debt is not None and cur_debt is not None and repaid is not None:
                    expected_debt = round(max(0.0, prev_debt - repaid), 2)
                    diff = round(abs(cur_debt - expected_debt), 2)
                    if diff > max_debt_diff:
                        max_debt_diff = diff
                    if diff > tolerance:
                        has_debt_failure = True
                    prev_debt = cur_debt
                elif cur_debt is not None and repaid is None:
                    has_debt_unresolved = True
                    prev_debt = cur_debt
                else:
                    has_debt_unresolved = True

            if has_debt_failure:
                status_4 = "FAILED"
                msg_4 = f"Debt reconciliation diff (max diff: ₹{max_debt_diff:,.2f})"
            elif has_debt_unresolved:
                status_4 = "UNRESOLVED"
                msg_4 = "Debt reduction unresolved due to missing debt or repayment values."
            else:
                status_4 = "PASSED"
                msg_4 = "Debt reduction reconciles with principal repayments."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_4_DEBT_REDUCTION",
                status=status_4,
                expected="Opening Debt - Principal Repaid",
                actual="Closing Debt",
                difference=round(max_debt_diff, 2) if not has_debt_unresolved and not is_structurally_zero_debt else (0.0 if is_structurally_zero_debt else None),
                tolerance=tolerance,
                severity="CRITICAL",
                message=msg_4
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 5: Stage 9 loan schedule reconciles with M3 interest/principal
        # ---------------------------------------------------------------------
        is_zero_debt = (sources_uses.term_loan == 0.0)
        loan_diff: Optional[float] = None

        if is_zero_debt:
            status_5 = "PASSED"
            msg_5 = "No term debt present; loan reconciliation holds trivially."
            loan_diff = 0.0
        elif repayment_schedule is None or not repayment_schedule.monthly_schedule:
            status_5 = "UNRESOLVED"
            msg_5 = "Stage 9 repayment schedule unavailable to reconcile debt/interest."
        else:
            if any(p.interest_expense is None for p in profit_loss.years):
                status_5 = "UNRESOLVED"
                msg_5 = "P&L interest expense contains unmodeled or unresolved years."
            else:
                total_m3_interest = sum(float(p.interest_expense) for p in profit_loss.years)
                m3_years = len(profit_loss.years)
                sched_components = []
                sched_has_unresolved = False
                for r in repayment_schedule.monthly_schedule:
                    if (r.period - 1) // 12 + 1 <= m3_years:
                        val = getattr(r, "interest_component", None)
                        if val is None:
                            val = getattr(r, "interest_paid", None)
                        if val is None:
                            sched_has_unresolved = True
                            break
                        sched_components.append(float(val))

                if sched_has_unresolved:
                    status_5 = "UNRESOLVED"
                    msg_5 = "Stage 9 repayment schedule contains unresolved interest rows."
                else:
                    sched_interest_m3_period = sum(sched_components)
                    loan_diff = round(abs(total_m3_interest - sched_interest_m3_period), 2)
                    if loan_diff > tolerance:
                        status_5 = "FAILED"
                        msg_5 = f"Interest mismatch with Stage 9 (diff: ₹{loan_diff:,.2f})"
                    else:
                        status_5 = "PASSED"
                        msg_5 = "M3 interest expense matches Stage 9 amortization schedule."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_5_STAGE9_LOAN_RECONCILIATION",
                status=status_5,
                expected="Stage 9 Scheduled Interest",
                actual="M3 P&L Interest Expense",
                difference=loan_diff,
                tolerance=tolerance,
                severity="CRITICAL",
                message=msg_5
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 6: Gross Profit = Revenue - COGS
        # ---------------------------------------------------------------------
        has_gp_failure = False
        has_gp_unresolved = False
        max_gp_diff = 0.0
        if not profit_loss.years:
            has_gp_unresolved = True
        for pl_y in profit_loss.years:
            if pl_y.revenue is not None and pl_y.cogs is not None and pl_y.gross_profit is not None:
                calc_gp = round(pl_y.revenue - pl_y.cogs, 2)
                diff = round(abs(calc_gp - pl_y.gross_profit), 2)
                if diff > max_gp_diff:
                    max_gp_diff = diff
                if diff > 0.05:
                    has_gp_failure = True
            else:
                has_gp_unresolved = True

        if has_gp_failure:
            status_6 = "FAILED"
            msg_6 = f"Gross profit identity failure (max diff: ₹{max_gp_diff:,.2f})"
        elif has_gp_unresolved:
            status_6 = "UNRESOLVED"
            msg_6 = "Gross profit unresolved due to missing revenue or COGS."
        else:
            status_6 = "PASSED"
            msg_6 = "Gross profit equals Revenue minus COGS."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_6_GROSS_PROFIT_IDENTITY",
                status=status_6,
                expected="Revenue - COGS",
                actual="Gross Profit",
                difference=round(max_gp_diff, 2) if not has_gp_unresolved else None,
                tolerance=0.05,
                severity="CRITICAL",
                message=msg_6
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 7: EBITDA = Gross Profit - Operating Expenses
        # ---------------------------------------------------------------------
        has_ebitda_failure = False
        has_ebitda_unresolved = False
        max_ebitda_diff = 0.0
        if not profit_loss.years:
            has_ebitda_unresolved = True
        for pl_y in profit_loss.years:
            if pl_y.gross_profit is not None and pl_y.operating_expenses is not None and pl_y.ebitda is not None:
                calc_ebitda = round(pl_y.gross_profit - pl_y.operating_expenses, 2)
                diff = round(abs(calc_ebitda - pl_y.ebitda), 2)
                if diff > max_ebitda_diff:
                    max_ebitda_diff = diff
                if diff > 0.05:
                    has_ebitda_failure = True
            else:
                has_ebitda_unresolved = True

        if has_ebitda_failure:
            status_7 = "FAILED"
            msg_7 = f"EBITDA identity failure (max diff: ₹{max_ebitda_diff:,.2f})"
        elif has_ebitda_unresolved:
            status_7 = "UNRESOLVED"
            msg_7 = "EBITDA unresolved due to missing gross profit or operating expenses."
        else:
            status_7 = "PASSED"
            msg_7 = "EBITDA equals Gross Profit minus Operating Expenses."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_7_EBITDA_IDENTITY",
                status=status_7,
                expected="Gross Profit - Operating Expenses",
                actual="EBITDA",
                difference=round(max_ebitda_diff, 2) if not has_ebitda_unresolved else None,
                tolerance=0.05,
                severity="CRITICAL",
                message=msg_7
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 8: EBIT = EBITDA - Depreciation
        # ---------------------------------------------------------------------
        has_ebit_failure = False
        has_ebit_unresolved = False
        max_ebit_diff = 0.0
        if not profit_loss.years:
            has_ebit_unresolved = True
        for pl_y in profit_loss.years:
            if pl_y.ebitda is not None and pl_y.depreciation is not None and pl_y.ebit is not None:
                calc_ebit = round(pl_y.ebitda - pl_y.depreciation, 2)
                diff = round(abs(calc_ebit - pl_y.ebit), 2)
                if diff > max_ebit_diff:
                    max_ebit_diff = diff
                if diff > 0.05:
                    has_ebit_failure = True
            else:
                has_ebit_unresolved = True

        if has_ebit_failure:
            status_8 = "FAILED"
            msg_8 = f"EBIT identity failure (max diff: ₹{max_ebit_diff:,.2f})"
        elif has_ebit_unresolved:
            status_8 = "UNRESOLVED"
            msg_8 = "EBIT unresolved due to missing EBITDA or depreciation."
        else:
            status_8 = "PASSED"
            msg_8 = "EBIT equals EBITDA minus Depreciation."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_8_EBIT_IDENTITY",
                status=status_8,
                expected="EBITDA - Depreciation",
                actual="EBIT",
                difference=round(max_ebit_diff, 2) if not has_ebit_unresolved else None,
                tolerance=0.05,
                severity="CRITICAL",
                message=msg_8
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 9: PBT = EBIT - Interest
        # ---------------------------------------------------------------------
        has_pbt_failure = False
        has_pbt_unresolved = False
        max_pbt_diff = 0.0
        if not profit_loss.years:
            has_pbt_unresolved = True
        for pl_y in profit_loss.years:
            if pl_y.ebit is not None and pl_y.profit_before_tax is not None and pl_y.interest_expense is not None:
                calc_pbt = round(pl_y.ebit - pl_y.interest_expense, 2)
                diff = round(abs(calc_pbt - pl_y.profit_before_tax), 2)
                if diff > max_pbt_diff:
                    max_pbt_diff = diff
                if diff > 0.05:
                    has_pbt_failure = True
            else:
                has_pbt_unresolved = True

        if has_pbt_failure:
            status_9 = "FAILED"
            msg_9 = f"PBT identity failure (max diff: ₹{max_pbt_diff:,.2f})"
        elif has_pbt_unresolved:
            status_9 = "UNRESOLVED"
            msg_9 = "PBT unresolved due to missing EBIT, interest, or PBT."
        else:
            status_9 = "PASSED"
            msg_9 = "PBT equals EBIT minus Interest."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_9_PBT_IDENTITY",
                status=status_9,
                expected="EBIT - Interest",
                actual="PBT",
                difference=round(max_pbt_diff, 2) if not has_pbt_unresolved else None,
                tolerance=0.05,
                severity="CRITICAL",
                message=msg_9
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 10: PAT = PBT - Tax when tax is modeled
        # ---------------------------------------------------------------------
        has_pat_failure = False
        has_pat_unresolved = False
        max_pat_diff = 0.0
        if not profit_loss.years:
            has_pat_unresolved = True
        for pl_y in profit_loss.years:
            if pl_y.profit_before_tax is not None and pl_y.profit_after_tax is not None:
                if pl_y.tax_status in ("CALCULATED", "EXEMPT", "ESTIMATED"):
                    tax_val = pl_y.tax_expense if pl_y.tax_expense is not None else 0.0
                    calc_pat = round(pl_y.profit_before_tax - tax_val, 2)
                    diff = round(abs(calc_pat - pl_y.profit_after_tax), 2)
                    if diff > max_pat_diff:
                        max_pat_diff = diff
                    if diff > 0.05:
                        has_pat_failure = True
                else:
                    has_pat_unresolved = True
            else:
                has_pat_unresolved = True

        if has_pat_failure:
            status_10 = "FAILED"
            msg_10 = f"PAT identity failure (max diff: ₹{max_pat_diff:,.2f})"
        elif has_pat_unresolved:
            status_10 = "UNRESOLVED"
            msg_10 = "PAT unresolved because tax is unmodeled or values are missing."
        else:
            status_10 = "PASSED"
            msg_10 = "PAT properly reflects PBT minus tax."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_10_PAT_IDENTITY",
                status=status_10,
                expected="PBT - Tax",
                actual="PAT",
                difference=round(max_pat_diff, 2) if not has_pat_unresolved else None,
                tolerance=0.05,
                severity="CRITICAL",
                message=msg_10
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 11: Cash conversion cycle = Inventory Days + Receivable Days - Payable Days
        # ---------------------------------------------------------------------
        has_ccc_failure = False
        has_ccc_unresolved = False
        if not financial_ratios.years:
            has_ccc_unresolved = True
        for r_y in financial_ratios.years:
            if r_y.inventory_days is not None and r_y.receivable_days is not None and r_y.payable_days is not None and r_y.cash_conversion_cycle is not None:
                expected_ccc = round(r_y.inventory_days + r_y.receivable_days - r_y.payable_days, 1)
                diff = abs(expected_ccc - r_y.cash_conversion_cycle)
                if diff > 0.2:
                    has_ccc_failure = True
            else:
                has_ccc_unresolved = True

        if has_ccc_failure:
            status_11 = "FAILED"
            msg_11 = "CCC calculation mismatch with component turnover days."
        elif has_ccc_unresolved:
            status_11 = "UNRESOLVED"
            msg_11 = "Cash conversion cycle unresolved due to missing turnover days."
        else:
            status_11 = "PASSED"
            msg_11 = "Cash Conversion Cycle matches turnover days."

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_11_CASH_CONVERSION_CYCLE",
                status=status_11,
                expected="Inv Days + Rec Days - Pay Days",
                actual="Cash Conversion Cycle",
                difference=0.0 if status_11 == "PASSED" else (1.0 if status_11 == "FAILED" else None),
                tolerance=0.2,
                severity="WARNING",
                message=msg_11
            )
        )

        # ---------------------------------------------------------------------
        # CHECK 12: No negative impossible values
        # ---------------------------------------------------------------------
        no_negative_impossible = True
        bad_values: List[str] = []
        if not profit_loss.years and not balance_sheet.years:
            status_12 = "UNRESOLVED"
            msg_12 = "No statement data available to check for negative values."
        else:
            for pl_y in profit_loss.years:
                if pl_y.revenue is not None and pl_y.revenue < 0:
                    no_negative_impossible = False
                    bad_values.append(f"Year {pl_y.year} Revenue < 0")
                if pl_y.cogs is not None and pl_y.cogs < 0:
                    no_negative_impossible = False
                    bad_values.append(f"Year {pl_y.year} COGS < 0")

            for bs_y in balance_sheet.years:
                if bs_y.total_assets is not None and bs_y.total_assets < 0:
                    no_negative_impossible = False
                    bad_values.append(f"Year {bs_y.year} Total Assets < 0")
                if bs_y.inventory is not None and bs_y.inventory < 0:
                    no_negative_impossible = False
                    bad_values.append(f"Year {bs_y.year} Inventory < 0")

            status_12 = "PASSED" if no_negative_impossible else "FAILED"
            msg_12 = "No impossible negative values found." if no_negative_impossible else f"Impossible negative values: {', '.join(bad_values)}"

        checks.append(
            ProjectionValidationCheck(
                check_id="CHECK_12_NO_IMPOSSIBLE_NEGATIVE_VALUES",
                status=status_12,
                expected=">= 0.0",
                actual="All non-negative" if status_12 == "PASSED" else "Negative values present",
                difference=0.0 if status_12 == "PASSED" else (float(len(bad_values)) if bad_values else None),
                tolerance=0.0,
                severity="CRITICAL",
                message=msg_12
            )
        )

        total_checks = len(checks)
        passed_checks = sum(1 for c in checks if c.status == "PASSED")
        failed_checks = sum(1 for c in checks if c.status == "FAILED")
        unresolved_checks = sum(1 for c in checks if c.status in ("UNRESOLVED", "INSUFFICIENT_DATA"))

        all_passed = (failed_checks == 0 and unresolved_checks == 0 and total_checks > 0)

        return ProjectionValidation(
            all_passed=all_passed,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            unresolved_checks=unresolved_checks,
            checks=checks
        )


validation_engine = ValidationEngine()
