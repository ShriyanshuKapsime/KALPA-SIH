"""
Financing Optimizer for Milestone 5.
Deterministically selects the most appropriate financing structure using a transparent,
multi-tiered policy hierarchy. Zero machine-learning or black-box scores.
"""
from typing import List, Optional, Tuple
from app.services.financial_engine.optimizer.m5_config import (
    DSCR_RESILIENCE_BENCHMARK,
    DSCR_RESILIENCE_MINIMUM
)
from app.services.financial_engine.optimizer.m5_schema import FinancingStructureCandidate
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder


class FinancingOptimizer:
    """
    Applies a deterministic policy hierarchy to evaluate and select the recommended financing option.
    """

    def select_best_structure(
        self,
        candidates: List[FinancingStructureCandidate],
        provenance: Optional[M5ProvenanceBuilder] = None,
        preferred_scheme_id: Optional[str] = None,
        preferred_tenure_months: Optional[int] = None
    ) -> Tuple[Optional[FinancingStructureCandidate], List[M5ReasonCode]]:
        prov = provenance or M5ProvenanceBuilder()

        if not candidates:
            return None, [M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE]

        # Tier 1 Filter: Hard Eligibility, Non-Plug Feasibility & Repayment Gates
        feasible_candidates: List[FinancingStructureCandidate] = []
        for c in candidates:
            # 0. Candidate status gate: strictly reject non-RESOLVED candidates
            if c.status != "RESOLVED":
                continue

            # All required numerical fields must be fully resolved
            if (
                c.total_project_cost is None or c.total_project_cost <= 0 or
                c.promoter_contribution is None or
                c.loan_amount is None or
                c.financing_gap is None
            ):
                continue

            if c.loan_amount > 0:
                if (
                    c.interest_rate is None or
                    c.tenure_months is None or
                    c.moratorium_months is None or
                    (c.monthly_emi is None and c.annual_debt_service is None) or
                    c.total_interest is None
                ):
                    continue
                if c.monthly_emi is None and c.annual_debt_service is not None:
                    c.monthly_emi = round(c.annual_debt_service / 12.0, 2)

            # 1. Valid scheme & scheme compliance
            if not c.is_scheme_compliant:
                continue

            # 2. Promoter margin compliance
            if not c.is_margin_met:
                continue

            # 3. Financing gap eliminated
            if not c.is_gap_eliminated or c.financing_gap > 1.0:
                continue

            # 4. Zero-debt vs Borrowing Repayment Feasibility
            is_zero_loan = (c.loan_amount == 0.0)
            if not is_zero_loan:
                # Base-case repayment feasibility (DSCR >= 1.0)
                if c.base_case_dscr is None or c.base_case_dscr < 1.00:
                    continue

            feasible_candidates.append(c)

        if not feasible_candidates:
            # Do NOT force a selection if no candidate satisfies all gates
            return None, [M5ReasonCode.NO_FEASIBLE_FINANCING_STRUCTURE]

        # Tier 2 Filter: Robust Downside Stress Resilience (DSCR >= DSCR_RESILIENCE_MINIMUM)
        resilient_candidates: List[FinancingStructureCandidate] = [
            c for c in feasible_candidates
            if (c.loan_amount == 0.0) or
               (c.combined_downside_dscr is not None and c.combined_downside_dscr >= DSCR_RESILIENCE_MINIMUM) or
               (c.stress_case_dscr is not None and c.stress_case_dscr >= DSCR_RESILIENCE_MINIMUM)
        ]

        pool = resilient_candidates if resilient_candidates else feasible_candidates

        # Tier 3 Ranking: Scheme Alignment, Downside Resilience & Cost of Capital Efficiency
        def sort_key(cand: FinancingStructureCandidate):
            # 1. Preferred scheme alignment
            scheme_match = 1
            if preferred_scheme_id:
                pref_norm = preferred_scheme_id.lower().replace("_", "")
                cand_norm = cand.scheme_id.lower().replace("_", "")
                cand_name_norm = cand.scheme_name.lower().replace(" ", "")
                if pref_norm in cand_norm or cand_norm in pref_norm or pref_norm in cand_name_norm:
                    scheme_match = 0

            # 2. Preferred tenure alignment
            tenure_match = 1
            if preferred_tenure_months and cand.tenure_months == preferred_tenure_months:
                tenure_match = 0

            s_dscr = cand.combined_downside_dscr if cand.combined_downside_dscr is not None else (cand.stress_case_dscr if cand.stress_case_dscr is not None else 0.0)
            tot_int = cand.total_interest if cand.total_interest is not None else float("inf")
            emi = cand.monthly_emi if cand.monthly_emi is not None else float("inf")
            # Preferred scheme -> Preferred tenure -> Higher stress DSCR (negated) -> Lower total interest -> Lower EMI
            return (scheme_match, tenure_match, -s_dscr, tot_int, emi)

        sorted_pool = sorted(pool, key=sort_key)
        best = sorted_pool[0]

        # Assemble explicit policy decision reasons
        decision_reasons: List[M5ReasonCode] = []
        if best.loan_amount == 0.0:
            decision_reasons.append(M5ReasonCode.EXPLICIT_ZERO_DEBT)
        if best.is_gap_eliminated:
            decision_reasons.append(M5ReasonCode.FINANCING_GAP_ELIMINATED)
        if best.is_margin_met:
            decision_reasons.append(M5ReasonCode.MARGIN_REQUIREMENT_MET)
        if best.loan_amount > 0 and best.base_case_dscr is not None and best.base_case_dscr >= 1.0:
            decision_reasons.append(M5ReasonCode.DEBT_SERVICE_FEASIBLE)
        best_downside = best.combined_downside_dscr if best.combined_downside_dscr is not None else best.stress_case_dscr
        if best.loan_amount > 0 and best_downside is not None and best_downside >= DSCR_RESILIENCE_MINIMUM:
            decision_reasons.append(M5ReasonCode.DOWNSIDE_RESILIENT)

        if len(pool) > 1 and best.total_interest is not None:
            pool_interests = [c.total_interest for c in pool if c.total_interest is not None]
            if pool_interests and best.total_interest <= min(pool_interests) + 1.0:
                decision_reasons.append(M5ReasonCode.LOWER_TOTAL_INTEREST)

        best.decision_rank = 1
        best.selection_reasons = decision_reasons

        prov.record(
            metric="selected_financing_structure",
            value=best.candidate_id,
            source="POLICY_SCENARIO",
            source_reference=f"Selected scheme {best.scheme_name} ({best.tenure_months}M tenure)",
            calculation_method="Multi-tier deterministic policy selection (Eligibility -> Downside Resilience -> Lowest Cost of Capital)"
        )

        return best, decision_reasons


financing_optimizer = FinancingOptimizer()
