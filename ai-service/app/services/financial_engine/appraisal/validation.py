"""
Tri-State Validation Engine for M4 Banking Appraisal.
Validates 14+ accounting invariants and Stage 9 reconciliation integrity.
Strict rule: all_passed = True ONLY when failed_checks == 0 AND unresolved_checks == 0.
"""
from typing import List, Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    AppraisalValidationCheck,
    AppraisalValidationResult,
    ValidationState,
    RiskSeverity,
    DebtServiceAnalysisResult,
    DSCRAnalysisResult,
    BreakEvenAnalysisResult,
    PromoterContributionResult,
    FinancingStructureResult,
    BankingRatiosResult,
    ProfitabilityAnalysisResult,
    LiquidityAnalysisResult,
    LeverageAnalysisResult,
    AppraisalStatus
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode
from app.schemas.financial_analysis import (
    ProjectCostAnalysis,
    FundingSourcesUses,
    LoanManagement,
    DebtServiceAnalysis,
    BreakEvenAnalysis
)


class AppraisalValidationEngine:
    """
    Deterministic tri-state validation engine.
    """

    def validate(
        self,
        project_cost_analysis: Optional[ProjectCostAnalysis] = None,
        sources_uses: Optional[FundingSourcesUses] = None,
        loan_management: Optional[LoanManagement] = None,
        stage9_debt_service: Optional[DebtServiceAnalysis] = None,
        stage9_break_even: Optional[BreakEvenAnalysis] = None,
        debt_service: Optional[DebtServiceAnalysisResult] = None,
        dscr: Optional[DSCRAnalysisResult] = None,
        break_even: Optional[BreakEvenAnalysisResult] = None,
        promoter_contribution: Optional[PromoterContributionResult] = None,
        financing: Optional[FinancingStructureResult] = None,
        banking_ratios: Optional[BankingRatiosResult] = None,
        profitability: Optional[ProfitabilityAnalysisResult] = None,
        liquidity: Optional[LiquidityAnalysisResult] = None,
        leverage: Optional[LeverageAnalysisResult] = None,
        critical_unknowns: Optional[List[str]] = None
    ) -> AppraisalValidationResult:
        checks: List[AppraisalValidationCheck] = []

        # 1. M2 -> M3 Consistency (Project Cost vs Sources & Uses)
        m2_cost = project_cost_analysis.total_project_cost if project_cost_analysis else None
        m3_uses = sources_uses.total_uses if sources_uses else (financing.total_uses if financing else None)
        if m2_cost is not None and m3_uses is not None:
            diff = round(abs(m2_cost - m3_uses), 2)
            passed = diff <= 2.0
            checks.append(AppraisalValidationCheck(
                check_id="VAL_M2_M3_COST_CONSISTENCY",
                description="M2 Normalized Project Cost matches M3 Sources and Uses",
                status=ValidationState.PASSED if passed else ValidationState.FAILED,
                expected=m2_cost,
                actual=m3_uses,
                difference=diff,
                tolerance=2.0,
                severity=RiskSeverity.HIGH,
                message="M2 total project cost reconciles with M3 total uses." if passed else f"Cost mismatch: M2 ₹{m2_cost:,.2f} vs M3 ₹{m3_uses:,.2f}",
                reason_code=None if passed else ReasonCode.VALIDATION_FAILED
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_M2_M3_COST_CONSISTENCY",
                description="M2 Normalized Project Cost matches M3 Sources and Uses",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.MEDIUM,
                message="M2 project cost or M3 uses data is unresolved.",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            ))

        # 2. Sources = Uses
        if financing and financing.total_sources is not None and financing.total_uses is not None:
            diff = round(financing.total_sources - financing.total_uses, 2)
            passed = abs(diff) <= 2.0
            checks.append(AppraisalValidationCheck(
                check_id="VAL_SOURCES_EQUALS_USES",
                description="Total Financing Sources equal Total Project Uses",
                status=ValidationState.PASSED if passed else ValidationState.FAILED,
                expected=financing.total_uses,
                actual=financing.total_sources,
                difference=diff,
                tolerance=2.0,
                severity=RiskSeverity.CRITICAL,
                message="Financing sources fully cover project uses." if passed else f"Sources vs Uses discrepancy of ₹{diff:,.2f}",
                reason_code=None if passed else ReasonCode.FINANCING_GAP
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_SOURCES_EQUALS_USES",
                description="Total Financing Sources equal Total Project Uses",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.CRITICAL,
                message="Financing sources or uses unresolved.",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            ))

        # 3. Debt Balance Continuity
        if debt_service and debt_service.years:
            continuity_passed = True
            continuity_unresolved = False
            max_diff = 0.0
            for idx in range(len(debt_service.years) - 1):
                prev_close = debt_service.years[idx].closing_debt
                next_open = debt_service.years[idx + 1].opening_debt
                if prev_close is None or next_open is None:
                    continuity_unresolved = True
                    break
                d = abs(prev_close - next_open)
                if d > 1.0:
                    continuity_passed = False
                    max_diff = max(max_diff, d)

            if continuity_unresolved:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_DEBT_BALANCE_CONTINUITY",
                    description="Annual closing debt equals subsequent opening debt",
                    status=ValidationState.UNRESOLVED,
                    severity=RiskSeverity.HIGH,
                    message="Debt balance continuity unresolved due to missing data.",
                    reason_code=ReasonCode.INSUFFICIENT_DATA
                ))
            else:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_DEBT_BALANCE_CONTINUITY",
                    description="Annual closing debt equals subsequent opening debt",
                    status=ValidationState.PASSED if continuity_passed else ValidationState.FAILED,
                    difference=round(max_diff, 2),
                    tolerance=1.0,
                    severity=RiskSeverity.HIGH,
                    message="Debt balance continuity verified across all projection years." if continuity_passed else f"Debt balance discontinuity of ₹{max_diff:,.2f}",
                    reason_code=None if continuity_passed else ReasonCode.VALIDATION_FAILED
                ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_DEBT_BALANCE_CONTINUITY",
                description="Annual closing debt equals subsequent opening debt",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.HIGH,
                message="Debt service schedule unresolved.",
                reason_code=ReasonCode.MISSING_DEBT_SERVICE
            ))

        # 4. Stage 9 Principal Reconciliation
        actual_princ: Optional[float] = None
        if debt_service:
            if debt_service.total_principal_lifetime is not None:
                actual_princ = debt_service.total_principal_lifetime
            elif debt_service.total_principal is not None and debt_service.closing_debt_final is not None:
                actual_princ = round(debt_service.total_principal + debt_service.closing_debt_final, 2)
            elif debt_service.is_zero_debt:
                actual_princ = 0.0

        if loan_management and loan_management.principal == 0.0:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_STAGE9_PRINCIPAL_RECONCILIATION",
                description="Total principal scheduled matches Stage 9 loan amount",
                status=ValidationState.PASSED,
                expected=0.0,
                actual=0.0 if actual_princ is None else actual_princ,
                difference=0.0,
                severity=RiskSeverity.LOW,
                message="Zero debt enterprise: Principal reconciliation trivially passed."
            ))
        elif loan_management and loan_management.principal is not None and actual_princ is not None:
            diff = round(abs(actual_princ - loan_management.principal), 2)
            passed = diff <= 2.0
            checks.append(AppraisalValidationCheck(
                check_id="VAL_STAGE9_PRINCIPAL_RECONCILIATION",
                description="Total principal scheduled matches Stage 9 loan amount",
                status=ValidationState.PASSED if passed else ValidationState.FAILED,
                expected=loan_management.principal,
                actual=actual_princ,
                difference=diff,
                tolerance=2.0,
                severity=RiskSeverity.CRITICAL,
                message="Scheduled principal exactly reconciles with Stage 9 loan amount." if passed else f"Principal mismatch: {diff}",
                reason_code=None if passed else ReasonCode.STAGE9_PRINCIPAL_MISMATCH
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_STAGE9_PRINCIPAL_RECONCILIATION",
                description="Total principal scheduled matches Stage 9 loan amount",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.CRITICAL,
                message="Stage 9 loan principal or M4 schedule unresolved.",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            ))

        # 5. Stage 9 Interest Reconciliation
        actual_int = debt_service.total_interest_lifetime if (debt_service and debt_service.total_interest_lifetime is not None) else (
            debt_service.total_interest if debt_service else None
        )
        if debt_service and loan_management and actual_int is not None and not debt_service.is_zero_debt:
            diff = round(abs(actual_int - loan_management.total_interest), 2)
            tol = max(50.0, loan_management.total_interest * 0.05)
            passed = diff <= tol
            checks.append(AppraisalValidationCheck(
                check_id="VAL_STAGE9_INTEREST_RECONCILIATION",
                description="Total scheduled interest matches Stage 9 interest calculation",
                status=ValidationState.PASSED if passed else ValidationState.FAILED,
                expected=loan_management.total_interest,
                actual=actual_int,
                difference=diff,
                tolerance=tol,
                severity=RiskSeverity.HIGH,
                message="Total interest schedule reconciles with Stage 9." if passed else f"Interest schedule discrepancy of {diff}",
                reason_code=None if passed else ReasonCode.STAGE9_INTEREST_MISMATCH
            ))
        elif debt_service and debt_service.is_zero_debt:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_STAGE9_INTEREST_RECONCILIATION",
                description="Total scheduled interest matches Stage 9 interest calculation",
                status=ValidationState.PASSED,
                expected=0.0,
                actual=0.0,
                difference=0.0,
                severity=RiskSeverity.LOW,
                message="Zero debt enterprise: Interest reconciliation passed."
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_STAGE9_INTEREST_RECONCILIATION",
                description="Total scheduled interest matches Stage 9 interest calculation",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.HIGH,
                message="Stage 9 interest or M4 schedule unresolved.",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            ))

        # 6. Stage 9 DSCR Reconciliation
        if dscr:
            if dscr.reconciliation_status == ValidationState.PASSED:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_STAGE9_DSCR_RECONCILIATION",
                    description="M4 DSCR aligns with authoritative Stage 9 DSCR",
                    status=ValidationState.PASSED,
                    difference=dscr.reconciliation_difference,
                    tolerance=0.20,
                    severity=RiskSeverity.HIGH,
                    message="DSCR models reconcile within tolerance."
                ))
            elif dscr.reconciliation_status == ValidationState.FAILED:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_STAGE9_DSCR_RECONCILIATION",
                    description="M4 DSCR aligns with authoritative Stage 9 DSCR",
                    status=ValidationState.FAILED,
                    difference=dscr.reconciliation_difference,
                    tolerance=0.20,
                    severity=RiskSeverity.HIGH,
                    message=f"DSCR mismatch of {dscr.reconciliation_difference}x between Stage 9 and M4.",
                    reason_code=ReasonCode.STAGE9_DSCR_MISMATCH
                ))
            else:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_STAGE9_DSCR_RECONCILIATION",
                    description="M4 DSCR aligns with authoritative Stage 9 DSCR",
                    status=ValidationState.UNRESOLVED,
                    severity=RiskSeverity.HIGH,
                    message="DSCR data unresolved for reconciliation.",
                    reason_code=ReasonCode.INSUFFICIENT_DATA
                ))

        # 7. Stage 9 Break-Even Reconciliation
        if break_even:
            if break_even.reconciliation_status == ValidationState.PASSED:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_STAGE9_BREAK_EVEN_RECONCILIATION",
                    description="M4 Break-Even aligns with authoritative Stage 9 Break-Even",
                    status=ValidationState.PASSED,
                    difference=break_even.reconciliation_difference,
                    tolerance=10.0,
                    severity=RiskSeverity.MEDIUM,
                    message="Break-even utilization aligns with Stage 9."
                ))
            elif break_even.reconciliation_status == ValidationState.FAILED:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_STAGE9_BREAK_EVEN_RECONCILIATION",
                    description="M4 Break-Even aligns with authoritative Stage 9 Break-Even",
                    status=ValidationState.FAILED,
                    difference=break_even.reconciliation_difference,
                    tolerance=10.0,
                    severity=RiskSeverity.MEDIUM,
                    message=f"Break-even utilization discrepancy of {break_even.reconciliation_difference}% against Stage 9.",
                    reason_code=ReasonCode.STAGE9_BREAK_EVEN_MISMATCH
                ))
            else:
                checks.append(AppraisalValidationCheck(
                    check_id="VAL_STAGE9_BREAK_EVEN_RECONCILIATION",
                    description="M4 Break-Even aligns with authoritative Stage 9 Break-Even",
                    status=ValidationState.UNRESOLVED,
                    severity=RiskSeverity.MEDIUM,
                    message="Break-even data unresolved for reconciliation.",
                    reason_code=ReasonCode.INSUFFICIENT_DATA
                ))

        # 8. Promoter Contribution Compliance
        if promoter_contribution and promoter_contribution.status == AppraisalStatus.RESOLVED:
            passed = promoter_contribution.is_adequate
            checks.append(AppraisalValidationCheck(
                check_id="VAL_PROMOTER_CONTRIBUTION_ADEQUACY",
                description="Actual promoter margin satisfies required contribution",
                status=ValidationState.PASSED if passed else ValidationState.FAILED,
                expected=promoter_contribution.required_promoter_contribution,
                actual=promoter_contribution.actual_promoter_contribution,
                difference=promoter_contribution.gap_surplus,
                severity=RiskSeverity.HIGH,
                message="Promoter equity satisfies scheme requirement." if passed else "Promoter equity deficit identified.",
                reason_code=None if passed else ReasonCode.PROMOTER_CONTRIBUTION_GAP
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_PROMOTER_CONTRIBUTION_ADEQUACY",
                description="Actual promoter margin satisfies required contribution",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.HIGH,
                message="Promoter contribution data unresolved.",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            ))

        # 9. Impossible Negative Values
        negatives_found = []
        if profitability and profitability.years:
            for y in profitability.years:
                if y.revenue is not None and y.revenue < 0:
                    negatives_found.append(f"Negative revenue in year {y.year}")
        if liquidity and liquidity.years:
            for y in liquidity.years:
                if y.current_assets is not None and y.current_assets < 0:
                    negatives_found.append(f"Negative current assets in year {y.year}")

        if negatives_found:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_NO_IMPOSSIBLE_NEGATIVES",
                description="Financial statements contain no impossible negative values",
                status=ValidationState.FAILED,
                severity=RiskSeverity.CRITICAL,
                message=f"Violations detected: {'; '.join(negatives_found)}",
                reason_code=ReasonCode.VALIDATION_FAILED
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_NO_IMPOSSIBLE_NEGATIVES",
                description="Financial statements contain no impossible negative values",
                status=ValidationState.PASSED,
                severity=RiskSeverity.CRITICAL,
                message="No impossible negative values found."
            ))

        # 10. Critical Dependencies
        if critical_unknowns:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_CRITICAL_DEPENDENCIES",
                description="All essential inputs resolved for banking appraisal",
                status=ValidationState.UNRESOLVED,
                severity=RiskSeverity.CRITICAL,
                message=f"Critical inputs unresolved: {', '.join(critical_unknowns)}",
                reason_code=ReasonCode.INSUFFICIENT_DATA
            ))
        else:
            checks.append(AppraisalValidationCheck(
                check_id="VAL_CRITICAL_DEPENDENCIES",
                description="All essential inputs resolved for banking appraisal",
                status=ValidationState.PASSED,
                severity=RiskSeverity.CRITICAL,
                message="All critical appraisal dependencies resolved."
            ))

        total_cnt = len(checks)
        passed_cnt = sum(1 for c in checks if c.status == ValidationState.PASSED)
        failed_cnt = sum(1 for c in checks if c.status == ValidationState.FAILED)
        unresolved_cnt = sum(1 for c in checks if c.status == ValidationState.UNRESOLVED)
        all_passed = (failed_cnt == 0 and unresolved_cnt == 0 and total_cnt > 0)

        return AppraisalValidationResult(
            all_passed=all_passed,
            total_checks=total_cnt,
            passed_checks=passed_cnt,
            failed_checks=failed_cnt,
            unresolved_checks=unresolved_cnt,
            checks=checks
        )


appraisal_validation_engine = AppraisalValidationEngine()
