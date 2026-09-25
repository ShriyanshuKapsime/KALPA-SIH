"""
Financing Feasibility & Funding Gap Analysis for Milestone 5.
Deterministically compares Total Project Cost against Total Available Funding
(Promoter Capital + Scheme Loan + Verified Other Financing).
Never uses fabricated plugs. Strictly enforces UNKNOWN != 0.
"""
from typing import Optional
from app.services.financial_engine.optimizer.m5_schema import FinancingGapAnalysisResult
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder


class FinancingFeasibilityEngine:
    """
    Evaluates mathematical funding feasibility without fabricating plugs or assuming zero.
    """

    def evaluate(
        self,
        total_project_cost: Optional[float],
        available_promoter_contribution: Optional[float],
        scheme_loan: Optional[float],
        other_verified_financing: Optional[float] = None,
        provenance: Optional[M5ProvenanceBuilder] = None
    ) -> FinancingGapAnalysisResult:
        prov = provenance or M5ProvenanceBuilder()

        # If project cost is missing or <= 0
        if total_project_cost is None or total_project_cost <= 0:
            return FinancingGapAnalysisResult(
                total_project_cost=None,
                available_promoter_contribution=available_promoter_contribution,
                scheme_loan=scheme_loan,
                other_verified_financing=other_verified_financing,
                total_funding=None,
                funding_gap=None,
                funding_surplus=None,
                is_balanced=False,
                status="UNRESOLVED",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            )

        # If any essential funding source is None (unresolved)
        if available_promoter_contribution is None or scheme_loan is None or other_verified_financing is None:
            return FinancingGapAnalysisResult(
                total_project_cost=total_project_cost,
                available_promoter_contribution=available_promoter_contribution,
                scheme_loan=scheme_loan,
                other_verified_financing=other_verified_financing,
                total_funding=None,
                funding_gap=None,
                funding_surplus=None,
                is_balanced=False,
                status="UNRESOLVED",
                reason_code=M5ReasonCode.INSUFFICIENT_DATA
            )

        total_funding = round(available_promoter_contribution + scheme_loan + other_verified_financing, 2)
        diff = round(total_funding - total_project_cost, 2)

        gap: Optional[float] = None
        surplus: Optional[float] = None
        is_balanced = False

        if abs(diff) <= 1.0:
            # Perfectly balanced within 1 rupee tolerance
            gap = 0.0
            surplus = 0.0
            is_balanced = True
            rc = M5ReasonCode.FINANCING_BALANCED
        elif diff < 0:
            # Funding shortfall
            gap = round(abs(diff), 2)
            surplus = 0.0
            is_balanced = False
            rc = M5ReasonCode.FINANCING_GAP
        else:
            # Excess funding available
            gap = 0.0
            surplus = round(diff, 2)
            is_balanced = True
            rc = M5ReasonCode.FINANCING_SURPLUS

        prov.record(
            metric="total_funding_available",
            value=total_funding,
            source="DERIVED",
            source_reference="Sum of promoter contribution, scheme loan, and verified other financing",
            calculation_method="promoter_contribution + scheme_loan + other_financing"
        )
        prov.record(
            metric="funding_gap",
            value=gap,
            source="DERIVED",
            source_reference="Shortfall between project cost and total funding",
            calculation_method="max(0.0, total_project_cost - total_funding)"
        )

        return FinancingGapAnalysisResult(
            total_project_cost=total_project_cost,
            available_promoter_contribution=available_promoter_contribution,
            scheme_loan=scheme_loan,
            other_verified_financing=other_verified_financing,
            total_funding=total_funding,
            funding_gap=gap,
            funding_surplus=surplus,
            is_balanced=is_balanced,
            status="RESOLVED",
            reason_code=rc
        )


financing_feasibility_engine = FinancingFeasibilityEngine()
