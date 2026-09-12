"""
Amortization Schedule Engine for Stage 9 Financial Engine.
Generates full month-by-month amortization schedules and aggregated quarterly repayment tables.
Ensures zero penny drift so the final closing balance strictly equals 0.0.
"""
import math
from typing import List, Dict, Any
from app.schemas.financial_analysis import (
    AmortizationRow,
    QuarterlyRepaymentRow,
    RepaymentSchedule,
    MoratoriumInterestMode
)


class AmortizationEngine:
    """
    Deterministic amortization table generator.
    """

    @staticmethod
    def generate_schedule(
        principal: float,
        annual_rate: float,
        tenure_months: int,
        moratorium_months: int = 0,
        monthly_emi: float = 0.0,
        moratorium_interest_mode: MoratoriumInterestMode = MoratoriumInterestMode.INTEREST_ONLY
    ) -> RepaymentSchedule:
        """
        Builds full monthly amortization and quarterly aggregation.
        """
        P = max(0.0, float(principal))
        annual_rate = max(0.0, float(annual_rate))
        r = annual_rate / 12.0
        T = max(1, int(tenure_months))
        m = max(0, min(int(moratorium_months), T - 1))
        
        monthly_rows: List[AmortizationRow] = []

        if P == 0.0:
            return RepaymentSchedule(
                monthly_schedule=[],
                quarterly_schedule=[],
                first_repayment_month=1,
                total_periods=T
            )

        current_balance = P

        # -------------------------------------------------------------------------
        # 1. Month-by-Month Generation
        # -------------------------------------------------------------------------
        for period in range(1, T + 1):
            opening_balance = round(current_balance, 2)

            if period <= m:
                # Phase 1: Moratorium
                phase = "MORATORIUM"
                if moratorium_interest_mode == MoratoriumInterestMode.INTEREST_ONLY:
                    interest_comp = round(opening_balance * r, 2)
                    principal_comp = 0.0
                    payment = interest_comp
                    closing_balance = opening_balance
                elif moratorium_interest_mode == MoratoriumInterestMode.INTEREST_CAPITALIZED:
                    interest_comp = round(opening_balance * r, 2)
                    principal_comp = 0.0
                    payment = 0.0
                    closing_balance = round(opening_balance + interest_comp, 2)
                else: # FULL_PAYMENT_HOLIDAY
                    interest_comp = round(opening_balance * r, 2)
                    principal_comp = 0.0
                    payment = 0.0
                    closing_balance = opening_balance
            else:
                # Phase 2: Repayment
                phase = "REPAYMENT"
                interest_comp = round(opening_balance * r, 2)
                
                # Check if this is the final period or balance is less than standard principal reduction
                if period == T:
                    # Final period: exactly payoff remaining balance
                    principal_comp = opening_balance
                    payment = round(principal_comp + interest_comp, 2)
                    closing_balance = 0.0
                else:
                    payment = monthly_emi
                    principal_comp = round(payment - interest_comp, 2)
                    
                    if principal_comp >= opening_balance:
                        # Loan pays off early
                        principal_comp = opening_balance
                        payment = round(principal_comp + interest_comp, 2)
                        closing_balance = 0.0
                    else:
                        closing_balance = round(opening_balance - principal_comp, 2)

            monthly_rows.append(
                AmortizationRow(
                    period=period,
                    phase=phase,
                    opening_balance=opening_balance,
                    payment=payment,
                    principal_component=principal_comp,
                    interest_component=interest_comp,
                    closing_balance=closing_balance
                )
            )

            current_balance = closing_balance
            if current_balance <= 0.0 and period >= m:
                # Fill remaining periods with zero rows if paid off early
                for remaining_period in range(period + 1, T + 1):
                    monthly_rows.append(
                        AmortizationRow(
                            period=remaining_period,
                            phase="REPAYMENT",
                            opening_balance=0.0,
                            payment=0.0,
                            principal_component=0.0,
                            interest_component=0.0,
                            closing_balance=0.0
                        )
                    )
                break

        # -------------------------------------------------------------------------
        # 2. Quarterly Aggregation
        # -------------------------------------------------------------------------
        quarterly_rows: List[QuarterlyRepaymentRow] = []
        quarter_num = 1
        
        for i in range(0, len(monthly_rows), 3):
            chunk = monthly_rows[i:i+3]
            if not chunk:
                continue
            
            q_months = [row.period for row in chunk]
            q_opening = chunk[0].opening_balance
            q_closing = chunk[-1].closing_balance
            q_payment = round(sum(row.payment for row in chunk), 2)
            q_principal = round(sum(row.principal_component for row in chunk), 2)
            q_interest = round(sum(row.interest_component for row in chunk), 2)

            quarterly_rows.append(
                QuarterlyRepaymentRow(
                    quarter=quarter_num,
                    months=q_months,
                    opening_balance=q_opening,
                    total_payment=q_payment,
                    principal_paid=q_principal,
                    interest_paid=q_interest,
                    closing_balance=q_closing
                )
            )
            quarter_num += 1

        first_repayment = m + 1 if m < T else T

        return RepaymentSchedule(
            monthly_schedule=monthly_rows,
            quarterly_schedule=quarterly_rows,
            first_repayment_month=first_repayment,
            total_periods=T
        )


# Global singleton instance
amortization_engine = AmortizationEngine()
