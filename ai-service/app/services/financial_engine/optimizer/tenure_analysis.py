"""
Tenure Analysis for Milestone 5.
Evaluates supported loan tenure alternatives deterministically using Stage 9
loan calculation mathematics. Zero arbitrary choices.
"""
from typing import Dict, Any, List, Optional
from app.services.financial_engine.loan_calculator import LoanCalculator
from app.services.financial_engine.optimizer.m5_config import DSCR_RESILIENCE_MINIMUM
from app.services.financial_engine.optimizer.m5_schema import TenureOptionResult
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode


class TenureAnalysisEngine:
    """
    Evaluates valid loan tenure alternatives under scheme constraints.
    """

    def __init__(self) -> None:
        self.loan_calc = LoanCalculator()

    def evaluate_tenures(
        self,
        loan_amount: Optional[float],
        annual_interest_rate: Optional[float],
        scheme_max_tenure_months: Optional[int],
        moratorium_months: Optional[int] = None,
        base_cads: Optional[float] = None,
        stress_cads: Optional[float] = None
    ) -> List[TenureOptionResult]:
        if (
            loan_amount is None or
            loan_amount <= 0 or
            annual_interest_rate is None or
            scheme_max_tenure_months is None or
            moratorium_months is None
        ):
            return []

        mor_months = moratorium_months

        # Candidate tenures supported up to scheme ceiling
        standard_tenures = [12, 24, 36, 48, 60, 72, 84]
        candidate_tenures = [t for t in standard_tenures if t <= scheme_max_tenure_months]
        if scheme_max_tenure_months not in candidate_tenures:
            candidate_tenures.append(scheme_max_tenure_months)
        candidate_tenures.sort()

        results: List[TenureOptionResult] = []

        for t in candidate_tenures:
            # Stage 9 loan calculation
            lm = self.loan_calc.calculate_emi(
                principal=loan_amount,
                annual_rate=annual_interest_rate,
                tenure_months=t,
                moratorium_months=mor_months
            )
            annual_ds = round(lm.monthly_emi * 12.0, 2)

            b_dscr: Optional[float] = None
            if base_cads is not None and annual_ds > 0:
                b_dscr = round(base_cads / annual_ds, 2) if base_cads > 0 else 0.0

            s_dscr: Optional[float] = None
            if stress_cads is not None and annual_ds > 0:
                s_dscr = round(stress_cads / annual_ds, 2) if stress_cads > 0 else 0.0

            rc_text = "ROBUST"
            if b_dscr is not None and b_dscr < 1.00:
                rc_text = "CRITICAL_DEFICIT"
            elif s_dscr is not None and s_dscr < DSCR_RESILIENCE_MINIMUM:
                rc_text = "TIGHT"

            results.append(TenureOptionResult(
                tenure_months=t,
                loan_amount=loan_amount,
                interest_rate=annual_interest_rate,
                moratorium_months=mor_months,
                monthly_emi=lm.monthly_emi,
                total_interest=lm.total_interest,
                annual_debt_service=annual_ds,
                base_dscr=b_dscr,
                stress_dscr=s_dscr,
                repayment_capacity_assessment=rc_text,
                is_scheme_compliant=(t <= scheme_max_tenure_months),
                status="RESOLVED",
                reason_code=M5ReasonCode.DEBT_SERVICE_FEASIBLE if (b_dscr is not None and b_dscr >= 1.0) else M5ReasonCode.DSCR_BELOW_THRESHOLD
            ))

        return results


tenure_analysis_engine = TenureAnalysisEngine()
