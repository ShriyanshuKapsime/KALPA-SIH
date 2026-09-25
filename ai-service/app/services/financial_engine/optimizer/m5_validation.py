"""
Tri-State Validation Engine for Milestone 5.
Validates all financial accounting invariants, scheme compliance, financing gaps,
stress scenario arithmetic, and optimization integrity.
States: PASSED, FAILED, UNRESOLVED.
`all_passed = True` ONLY when failed_checks == 0 AND unresolved_checks == 0.
Strict non-fabrication: UNKNOWN values never converted to zero or default fallbacks.
"""
from typing import List, Optional
from app.services.financial_engine.loan_calculator import LoanCalculator
from app.services.financial_engine.optimizer.m5_schema import (
    M5ValidationCheck,
    M5ValidationResult,
    M5ValidationState,
    StressScenarioResult,
    FinancingStructureCandidate,
    FinancingGapAnalysisResult,
    PromoterContributionAnalysisResult
)
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode


class M5ValidationEngine:
    """
    Enforces deterministic validation gates for Milestone 5.
    """

    def __init__(self) -> None:
        self.loan_calc = LoanCalculator()

    def validate(
        self,
        project_cost: Optional[float],
        financing_gap_analysis: Optional[FinancingGapAnalysisResult],
        promoter_analysis: Optional[PromoterContributionAnalysisResult],
        selected_structure: Optional[FinancingStructureCandidate],
        stress_scenarios: Optional[List[StressScenarioResult]],
        financing_options: Optional[List[FinancingStructureCandidate]] = None,
        is_zero_debt: bool = False
    ) -> M5ValidationResult:
        checks: List[M5ValidationCheck] = []

        # ---------------------------------------------------------------------
        # 1. Sources & Uses / Financing Feasibility Balance
        # ---------------------------------------------------------------------
        if (
            financing_gap_analysis and
            financing_gap_analysis.total_project_cost is not None and
            financing_gap_analysis.total_funding is not None and
            financing_gap_analysis.funding_gap is not None
        ):
            diff = round(abs(financing_gap_analysis.total_project_cost - financing_gap_analysis.total_funding), 2)
            gap = financing_gap_analysis.funding_gap

            # Consistency check: if gap == 0, total funding >= total project cost
            if gap == 0.0:
                is_consistent = (financing_gap_analysis.total_funding >= financing_gap_analysis.total_project_cost - 1.0)
            else:
                is_consistent = abs(gap - diff) <= 1.0

            checks.append(M5ValidationCheck(
                check_id="VAL_M5_SOURCES_USES_CONSISTENCY",
                description="Total funding and funding gap strictly reconcile with project cost",
                status=M5ValidationState.PASSED if is_consistent else M5ValidationState.FAILED,
                expected=financing_gap_analysis.total_project_cost,
                actual=financing_gap_analysis.total_funding,
                difference=diff,
                tolerance=1.0,
                message="Funding gap arithmetic strictly verified." if is_consistent else f"Gap arithmetic mismatch: diff={diff}",
                reason_code=None if is_consistent else M5ReasonCode.VALIDATION_FAILED
            ))
        else:
            checks.append(M5ValidationCheck(
                check_id="VAL_M5_SOURCES_USES_CONSISTENCY",
                description="Total funding and funding gap strictly reconcile with project cost",
                status=M5ValidationState.UNRESOLVED,
                message="Project cost, funding sources, or funding gap unresolved.",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            ))

        # ---------------------------------------------------------------------
        # 2. Promoter Contribution Consistency
        # ---------------------------------------------------------------------
        if (
            promoter_analysis and
            promoter_analysis.total_project_cost is not None and
            promoter_analysis.required_promoter_contribution is not None and
            promoter_analysis.available_promoter_contribution is not None and
            promoter_analysis.gap_surplus is not None
        ):
            calc_diff = round(promoter_analysis.available_promoter_contribution - promoter_analysis.required_promoter_contribution, 2)
            rep_diff = promoter_analysis.gap_surplus
            is_match = abs(calc_diff - rep_diff) <= 1.0
            checks.append(M5ValidationCheck(
                check_id="VAL_M5_PROMOTER_CONTRIBUTION_CONSISTENCY",
                description="Promoter contribution gap/surplus reconciles with required margin",
                status=M5ValidationState.PASSED if is_match else M5ValidationState.FAILED,
                expected=calc_diff,
                actual=rep_diff,
                difference=abs(calc_diff - rep_diff),
                tolerance=1.0,
                message="Promoter margin arithmetic verified." if is_match else "Promoter margin arithmetic mismatch.",
                reason_code=None if is_match else M5ReasonCode.VALIDATION_FAILED
            ))
        else:
            checks.append(M5ValidationCheck(
                check_id="VAL_M5_PROMOTER_CONTRIBUTION_CONSISTENCY",
                description="Promoter contribution gap/surplus reconciles with required margin",
                status=M5ValidationState.UNRESOLVED,
                message="Promoter contribution or required margin parameters unresolved.",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            ))

        # ---------------------------------------------------------------------
        # 3. Selected Financing Structure Feasibility & EMI Consistency
        # ---------------------------------------------------------------------
        if selected_structure:
            # Check for unresolved terms (including moratorium_months)
            if (
                selected_structure.loan_amount is None or
                selected_structure.interest_rate is None or
                selected_structure.tenure_months is None or
                selected_structure.moratorium_months is None or
                selected_structure.monthly_emi is None
            ):
                checks.append(M5ValidationCheck(
                    check_id="VAL_M5_SELECTED_STRUCTURE_EMI_CONSISTENCY",
                    description="Selected financing structure EMI reconciles with Stage 9 loan calculator",
                    status=M5ValidationState.UNRESOLVED,
                    message="Selected structure has unresolved loan amount, rate, tenure, moratorium, or EMI.",
                    reason_code=M5ReasonCode.INSUFFICIENT_DATA
                ))
            else:
                moratorium = selected_structure.moratorium_months
                calc_lm = self.loan_calc.calculate_emi(
                    principal=selected_structure.loan_amount,
                    annual_rate=selected_structure.interest_rate,
                    tenure_months=selected_structure.tenure_months,
                    moratorium_months=moratorium
                )
                emi_diff = round(abs(selected_structure.monthly_emi - calc_lm.monthly_emi), 2)
                emi_passed = emi_diff <= 2.0

                checks.append(M5ValidationCheck(
                    check_id="VAL_M5_SELECTED_STRUCTURE_EMI_CONSISTENCY",
                    description="Selected financing structure EMI reconciles with Stage 9 loan calculator",
                    status=M5ValidationState.PASSED if emi_passed else M5ValidationState.FAILED,
                    expected=calc_lm.monthly_emi,
                    actual=selected_structure.monthly_emi,
                    difference=emi_diff,
                    tolerance=2.0,
                    message="EMI exactly matches loan calculator mathematics." if emi_passed else f"EMI mismatch: {emi_diff}",
                    reason_code=None if emi_passed else M5ReasonCode.VALIDATION_FAILED
                ))

            # Feasibility Check: Status, Compliance, Margin, Gap, and DSCR
            if selected_structure.status != "RESOLVED" or selected_structure.financing_gap is None:
                checks.append(M5ValidationCheck(
                    check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                    description="Selected structure eliminates financing gap and satisfies scheme constraints",
                    status=M5ValidationState.UNRESOLVED,
                    message="Selected structure status is unresolved or financing gap is unresolved.",
                    reason_code=M5ReasonCode.INSUFFICIENT_DATA
                ))
            else:
                is_loan_positive = selected_structure.loan_amount is not None and selected_structure.loan_amount > 0
                gap_elim = selected_structure.is_gap_eliminated and selected_structure.financing_gap <= 1.0
                downside_dscr = selected_structure.combined_downside_dscr if selected_structure.combined_downside_dscr is not None else selected_structure.stress_case_dscr

                if not selected_structure.is_scheme_compliant:
                    status = M5ValidationState.FAILED
                    msg = "Selected structure violates scheme eligibility or boundary constraints."
                elif not selected_structure.is_margin_met:
                    status = M5ValidationState.FAILED
                    msg = "Selected structure does not meet required promoter margin."
                elif not gap_elim:
                    status = M5ValidationState.FAILED
                    msg = "Selected structure leaves an unresolved funding gap."
                elif is_loan_positive:
                    if selected_structure.base_case_dscr is None:
                        status = M5ValidationState.UNRESOLVED
                        msg = "Selected structure has debt but coverage ratios are unresolved."
                    elif selected_structure.base_case_dscr < 1.0:
                        status = M5ValidationState.FAILED
                        msg = f"Selected structure coverage ratio below threshold (Base DSCR: {selected_structure.base_case_dscr} < 1.0)."
                    else:
                        status = M5ValidationState.PASSED
                        msg = "Selected financing structure is fully funded, compliant, and coverage-feasible."
                else:
                    status = M5ValidationState.PASSED
                    msg = "Selected zero-debt financing structure is fully funded, compliant, and margin-adequate."

                checks.append(M5ValidationCheck(
                    check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                    description="Selected structure eliminates financing gap and satisfies scheme constraints",
                    status=status,
                    message=msg,
                    reason_code=None if status == M5ValidationState.PASSED else (M5ReasonCode.INSUFFICIENT_DATA if status == M5ValidationState.UNRESOLVED else M5ReasonCode.VALIDATION_FAILED)
                ))
        else:
            # Truthful classification when no financing structure is selected
            if is_zero_debt:
                # Case A: Genuine zero-debt project (100% equity / no borrowing needed)
                # Must be verified against financing_gap_analysis
                if (
                    financing_gap_analysis is None or
                    financing_gap_analysis.status != "RESOLVED" or
                    financing_gap_analysis.funding_gap is None or
                    financing_gap_analysis.total_project_cost is None or
                    financing_gap_analysis.total_funding is None
                ):
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.UNRESOLVED,
                        message="Zero-debt project: Funding completeness or financing gap is unresolved.",
                        reason_code=M5ReasonCode.INSUFFICIENT_DATA
                    ))
                elif not financing_gap_analysis.is_balanced or financing_gap_analysis.funding_gap > 1.0:
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.FAILED,
                        message=f"Zero-debt project has an unresolved funding gap of {financing_gap_analysis.funding_gap}.",
                        reason_code=M5ReasonCode.VALIDATION_FAILED
                    ))
                else:
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.PASSED,
                        message="Zero-debt project: Fully funded through verified equity/non-debt sources.",
                        reason_code=None
                    ))
            else:
                # No selected structure for debt-bearing project
                opts = financing_options or []
                resolved_candidates = [c for c in opts if c.status == "RESOLVED"]
                unresolved_candidates = [c for c in opts if c.status == "UNRESOLVED"]

                if not opts:
                    # Rule 5: financing_options is empty -> UNRESOLVED
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.UNRESOLVED,
                        message="No financing options available or evaluated.",
                        reason_code=M5ReasonCode.INSUFFICIENT_DATA
                    ))
                elif resolved_candidates:
                    # Rule 3 & 6: resolved_candidates exists AND none is feasible -> FAILED
                    # Do not let an unrelated unresolved candidate override independently evaluated resolved candidates
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.FAILED,
                        message="No feasible financing structure found that satisfies all scheme and risk constraints.",
                        reason_code=M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE
                    ))
                elif unresolved_candidates:
                    # Rule 4: no resolved_candidates AND unresolved_candidates exist -> UNRESOLVED
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.UNRESOLVED,
                        message="Financing options generation incomplete due to unresolved parameters.",
                        reason_code=M5ReasonCode.INSUFFICIENT_DATA
                    ))
                else:
                    checks.append(M5ValidationCheck(
                        check_id="VAL_M5_SELECTED_STRUCTURE_FEASIBILITY",
                        description="Selected structure eliminates financing gap and satisfies scheme constraints",
                        status=M5ValidationState.UNRESOLVED,
                        message="No financing structure selected due to unresolved financing parameters.",
                        reason_code=M5ReasonCode.INSUFFICIENT_DATA
                    ))

        # ---------------------------------------------------------------------
        # 4. Stress Scenario Arithmetic Consistency (Full Identity Reconciliation)
        # ---------------------------------------------------------------------
        if stress_scenarios:
            sc_failures = 0
            sc_checked = 0
            sc_unresolved = 0
            for sc in stress_scenarios:
                if sc.status == "RESOLVED":
                    # Check if all components for full identity reconciliation are present
                    has_all_inputs = (
                        sc.revenue is not None and
                        sc.cogs is not None and
                        sc.gross_profit is not None and
                        sc.operating_expenses is not None and
                        sc.ebitda is not None and
                        sc.depreciation is not None and
                        sc.interest_expense is not None and
                        sc.profit_before_tax is not None and
                        sc.tax_expense is not None and
                        sc.pat is not None and
                        sc.working_capital_movement is not None and
                        sc.operating_cash_flow is not None
                    )

                    if not has_all_inputs:
                        # An input is unknown, so full identity cannot be verified
                        sc_unresolved += 1
                        continue

                    sc_checked += 1
                    # 1. Revenue - COGS = Gross Profit
                    if abs((sc.revenue - sc.cogs) - sc.gross_profit) > 1.0:
                        sc_failures += 1
                    # 2. Gross Profit - OPEX = EBITDA
                    if abs((sc.gross_profit - sc.operating_expenses) - sc.ebitda) > 1.0:
                        sc_failures += 1
                    # 3. EBITDA - Depreciation = EBIT
                    ebit = sc.ebitda - sc.depreciation
                    # 4. EBIT - Interest = PBT
                    if abs((ebit - sc.interest_expense) - sc.profit_before_tax) > 1.0:
                        sc_failures += 1
                    # 5. PBT - Tax = PAT
                    if abs((sc.profit_before_tax - sc.tax_expense) - sc.pat) > 1.0:
                        sc_failures += 1
                    # 6. PAT + Depreciation - WC movement = Operating Cash Flow
                    wc_mov = sc.working_capital_movement
                    expected_ocf = sc.pat + sc.depreciation - wc_mov
                    if abs(expected_ocf - sc.operating_cash_flow) > 1.0:
                        sc_failures += 1
                else:
                    sc_unresolved += 1

            if sc_failures > 0:
                check_status = M5ValidationState.FAILED
                msg = f"Stress scenario accounting identity violation detected in {sc_failures} scenario(s)."
                rc = M5ReasonCode.VALIDATION_FAILED
            elif sc_checked > 0 and sc_unresolved == 0:
                check_status = M5ValidationState.PASSED
                msg = "All evaluated stress scenarios strictly reconcile across full P&L, tax, and cash-flow identities."
                rc = None
            else:
                # If an identity cannot be verified because an input is UNKNOWN, validation state must be UNRESOLVED, not PASSED.
                check_status = M5ValidationState.UNRESOLVED
                msg = "Stress scenario accounting identities unresolved due to missing financial drivers."
                rc = M5ReasonCode.INSUFFICIENT_DATA

            checks.append(M5ValidationCheck(
                check_id="VAL_M5_STRESS_SCENARIOS_ARITHMETIC",
                description="Stress scenarios satisfy deterministic accounting identities",
                status=check_status,
                message=msg,
                reason_code=rc
            ))
        else:
            checks.append(M5ValidationCheck(
                check_id="VAL_M5_STRESS_SCENARIOS_ARITHMETIC",
                description="Stress scenarios satisfy deterministic accounting identities",
                status=M5ValidationState.UNRESOLVED,
                message="No stress scenarios available for validation.",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            ))

        # ---------------------------------------------------------------------
        # Summary Gate: all_passed only if failed==0 and unresolved==0
        # ---------------------------------------------------------------------
        total = len(checks)
        passed = sum(1 for c in checks if c.status == M5ValidationState.PASSED)
        failed = sum(1 for c in checks if c.status == M5ValidationState.FAILED)
        unresolved = sum(1 for c in checks if c.status == M5ValidationState.UNRESOLVED)
        all_passed = (failed == 0 and unresolved == 0)

        return M5ValidationResult(
            all_passed=all_passed,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            unresolved_checks=unresolved,
            checks=checks
        )


m5_validation_engine = M5ValidationEngine()
