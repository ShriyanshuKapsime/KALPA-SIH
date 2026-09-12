"""
Loan Calculator for Stage 9 Financial Engine.
Implements deterministic scheme routing, loan cap enforcement,
interest rates, moratorium interest, and EMI computation using standard financial formulas.
"""
import math
from typing import Dict, Any, Tuple, Optional
from app.services.financial_engine.constants import (
    SCHEME_RULES,
    MAX_SUPPORTED_PROJECT_COST,
    DEFAULT_MORATORIUM_MODE,
    MORATORIUM_MODES
)
from app.schemas.financial_analysis import (
    SchemeResult,
    SchemeType,
    ProjectFinancing,
    LoanManagement,
    MoratoriumInterestMode
)


class LoanCalculator:
    """
    Deterministic loan calculation and scheme routing engine.
    """

    @staticmethod
    def calculate_project_financing(
        available_margin_capital: float,
        preferred_project_cost: Optional[float] = None
    ) -> Tuple[SchemeResult, ProjectFinancing, Dict[str, Any]]:
        """
        Determines theoretical project cost, scheme match, loan caps, and financeable loan.
        """
        available_margin = max(0.0, float(available_margin_capital))

        # 1. Calculate theoretical project cost and loan requirement
        if preferred_project_cost is not None and preferred_project_cost > 0:
            theoretical_project_cost = float(preferred_project_cost)
            required_margin = theoretical_project_cost * 0.10
            theoretical_loan_req = theoretical_project_cost * 0.90
        else:
            theoretical_project_cost = available_margin / 0.10
            required_margin = available_margin
            theoretical_loan_req = theoretical_project_cost * 0.90

        # Round to 2 decimal places for standard financial currency precision
        theoretical_project_cost = round(theoretical_project_cost, 2)
        required_margin = round(required_margin, 2)
        theoretical_loan_req = round(theoretical_loan_req, 2)

        # 2. Match Scheme based on project cost
        if theoretical_project_cost <= SCHEME_RULES["MICRO_FINANCE_SCHEME"]["max_project_cost"]:
            scheme_type = SchemeType.MICRO_FINANCE_SCHEME
            scheme_config = SCHEME_RULES["MICRO_FINANCE_SCHEME"]
            scheme_status = "MATCHED"
            eligibility_status = "ELIGIBILITY_REQUIRES_VERIFICATION"
            notes = [
                "Matched to Micro Enterprise Finance Scheme based on project cost <= ₹1,40,000.",
                "Requires valid entrepreneur KYC and non-farm micro enterprise classification."
            ]
        elif theoretical_project_cost <= SCHEME_RULES["TERM_LOAN_SCHEME"]["max_project_cost"]:
            scheme_type = SchemeType.TERM_LOAN_SCHEME
            scheme_config = SCHEME_RULES["TERM_LOAN_SCHEME"]
            scheme_status = "MATCHED"
            eligibility_status = "ELIGIBILITY_REQUIRES_VERIFICATION"
            notes = [
                "Matched to MSME Term Loan Facility based on project cost between ₹1.40L and ₹50L.",
                "Requires Udyam registration and verified business premises lease/ownership."
            ]
        else:
            scheme_type = SchemeType.NO_SUPPORTED_SCHEME
            scheme_config = None
            scheme_status = "NO_SUPPORTED_SCHEME"
            eligibility_status = "EXCEEDS_SUPPORTED_LIMIT"
            notes = [
                "Calculated project cost exceeds the configured maximum scheme limit of ₹50,00,000.",
                "Large commercial industrial financing schemes are not configured in current benchmark policy."
            ]

        # 3. Apply Scheme Loan Caps and Calculate Financeable Loan
        if scheme_config:
            scheme_max_loan = scheme_config["maximum_loan"]
            scheme_limited_loan = min(theoretical_loan_req, scheme_max_loan)
            scheme_limited_loan = round(scheme_limited_loan, 2)
            
            # If loan was capped, calculate maximum financeable project cost with 10% margin
            maximum_financeable_project_cost = round(scheme_limited_loan / 0.90, 2)
            actual_margin_needed = round(maximum_financeable_project_cost * 0.10, 2)
            excess_margin = max(0.0, round(available_margin - actual_margin_needed, 2))
            estimated_financeable_loan = scheme_limited_loan
            scheme_name = scheme_config["scheme_name"]
            scheme_id = scheme_config["scheme_id"]
        else:
            scheme_max_loan = SCHEME_RULES["TERM_LOAN_SCHEME"]["maximum_loan"]
            scheme_limited_loan = 0.0
            maximum_financeable_project_cost = MAX_SUPPORTED_PROJECT_COST
            excess_margin = available_margin
            estimated_financeable_loan = 0.0
            scheme_name = "No Supported Scheme (Exceeds Limit)"
            scheme_id = "NO_SUPPORTED_SCHEME"

        scheme_result = SchemeResult(
            status=scheme_status,
            recommended_scheme=scheme_type,
            scheme_name=scheme_name,
            scheme_id=scheme_id,
            eligibility_status=eligibility_status,
            eligibility_notes=notes
        )

        project_financing = ProjectFinancing(
            available_margin=available_margin,
            theoretical_project_cost=theoretical_project_cost,
            required_margin=required_margin,
            theoretical_loan_requirement=theoretical_loan_req,
            scheme_maximum_loan=scheme_max_loan,
            scheme_limited_loan=scheme_limited_loan,
            estimated_financeable_loan=estimated_financeable_loan,
            maximum_financeable_project_cost=maximum_financeable_project_cost,
            excess_margin=excess_margin
        )

        return scheme_result, project_financing, (scheme_config or {})

    @staticmethod
    def determine_scheme_and_financing(
        available_margin_capital: float,
        preferred_project_cost: Optional[float] = None
    ) -> Tuple[SchemeResult, ProjectFinancing, Dict[str, Any]]:
        return LoanCalculator.calculate_project_financing(available_margin_capital, preferred_project_cost)

    @staticmethod
    def calculate_emi(
        principal: float,
        annual_rate: float,
        tenure_months: int,
        moratorium_months: int = 0,
        moratorium_interest_mode: MoratoriumInterestMode = MoratoriumInterestMode.INTEREST_ONLY
    ) -> LoanManagement:
        """
        Calculates exact EMI, Moratorium Interest, and Total Repayments.
        Formula:
            EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where:
            P = Principal loan amount
            r = Monthly interest rate (annual_rate / 12)
            n = Repayment periods (tenure_months - moratorium_months)
        """
        P = max(0.0, float(principal))
        annual_rate = max(0.0, float(annual_rate))
        r = annual_rate / 12.0
        T = max(1, int(tenure_months))
        m = max(0, min(int(moratorium_months), T - 1))
        repayment_months = T - m

        if P == 0.0:
            return LoanManagement(
                principal=0.0,
                annual_interest_rate=annual_rate,
                monthly_interest_rate=r,
                tenure_months=T,
                moratorium_months=m,
                moratorium_interest_mode=moratorium_interest_mode,
                moratorium_interest_total=0.0,
                monthly_emi=0.0,
                total_interest=0.0,
                total_repayment=0.0,
                assumption_statement="Principal loan amount is zero."
            )

        # 1. Moratorium calculations (Default: INTEREST_ONLY)
        if moratorium_interest_mode == MoratoriumInterestMode.INTEREST_ONLY:
            monthly_moratorium_payment = round(P * r, 2)
            total_moratorium_interest = round(monthly_moratorium_payment * m, 2)
            effective_principal_for_repayment = P
        elif moratorium_interest_mode == MoratoriumInterestMode.INTEREST_CAPITALIZED:
            # Compound interest during moratorium added to principal
            effective_principal_for_repayment = round(P * ((1.0 + r) ** m), 2)
            total_moratorium_interest = round(effective_principal_for_repayment - P, 2)
        else: # FULL_PAYMENT_HOLIDAY
            effective_principal_for_repayment = round(P * (1.0 + (r * m)), 2)
            total_moratorium_interest = round(effective_principal_for_repayment - P, 2)

        # 2. Standard Annuity EMI calculation
        n = max(1, repayment_months)
        if r == 0.0:
            emi = round(effective_principal_for_repayment / n, 2)
            repayment_phase_interest = 0.0
        else:
            compounding_factor = (1.0 + r) ** n
            numerator = effective_principal_for_repayment * r * compounding_factor
            denominator = compounding_factor - 1.0
            emi = round(numerator / denominator, 2)
            repayment_phase_interest = round((emi * n) - effective_principal_for_repayment, 2)

        total_interest = round(total_moratorium_interest + repayment_phase_interest, 2)
        total_repayment = round(P + total_interest, 2)

        assumption_statement = (
            f"Moratorium calculation assumption: {MORATORIUM_MODES.get(moratorium_interest_mode.value, 'Interest-Only during moratorium')}"
        )

        return LoanManagement(
            principal=P,
            annual_interest_rate=round(annual_rate, 4),
            monthly_interest_rate=round(r, 6),
            tenure_months=T,
            moratorium_months=m,
            moratorium_interest_mode=moratorium_interest_mode,
            moratorium_interest_total=total_moratorium_interest,
            monthly_emi=emi,
            total_interest=total_interest,
            total_repayment=total_repayment,
            assumption_statement=assumption_statement
        )


# Global singleton instance
loan_calculator = LoanCalculator()
