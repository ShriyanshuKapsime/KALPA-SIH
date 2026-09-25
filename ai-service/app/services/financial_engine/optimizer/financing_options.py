"""
Financing Options Generator for Milestone 5.
Generates mathematically valid, scheme-compliant candidate financing structures.
Combines eligible schemes, tenure options, and promoter equity. Zero balancing plugs.
"""
from typing import Dict, Any, List, Optional
from app.services.financial_engine.loan_calculator import LoanCalculator
from app.services.financial_engine.optimizer.m5_config import (
    DSCR_RESILIENCE_MINIMUM,
    POLICY_STRESS_PARAMETERS
)
from app.services.financial_engine.optimizer.m5_schema import (
    SchemeRoutingOption,
    SchemeEligibilityStatus,
    FinancingStructureCandidate,
    StressScenarioResult,
    StressScenarioType
)
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder
from app.services.financial_engine.optimizer.reason_codes import M5ReasonCode


class FinancingOptionsGenerator:
    """
    Constructs candidate financing structures by pairing eligible schemes and permitted tenures.
    """

    def __init__(self) -> None:
        self.loan_calc = LoanCalculator()

    def generate_candidates(
        self,
        project_cost: Optional[float],
        available_promoter_contribution: Optional[float],
        scheme_options: List[SchemeRoutingOption],
        base_cads: Optional[float] = None,
        stress_scenarios: Optional[List[StressScenarioResult]] = None,
        stress_cads: Optional[float] = None,
        other_verified_financing: Optional[float] = None,
        provenance: Optional[M5ProvenanceBuilder] = None
    ) -> List[FinancingStructureCandidate]:
        prov = provenance or M5ProvenanceBuilder()
        candidates: List[FinancingStructureCandidate] = []

        if project_cost is None or project_cost <= 0:
            return []

        cost = float(project_cost)
        is_other_fin_known = (other_verified_financing is not None)

        # Extract actual stress scenario CADS
        rev_sc = next((s for s in (stress_scenarios or []) if s.scenario_type == StressScenarioType.REVENUE_DOWNSIDE and s.status == "RESOLVED"), None)
        cost_sc = next((s for s in (stress_scenarios or []) if s.scenario_type == StressScenarioType.VARIABLE_COST_INCREASE and s.status == "RESOLVED"), None)
        wc_sc = next((s for s in (stress_scenarios or []) if s.scenario_type == StressScenarioType.WORKING_CAPITAL_PRESSURE and s.status == "RESOLVED"), None)
        rate_sc = next((s for s in (stress_scenarios or []) if s.scenario_type == StressScenarioType.INTEREST_RATE_STRESS and s.status == "RESOLVED"), None)
        comb_sc = next((s for s in (stress_scenarios or []) if s.scenario_type == StressScenarioType.COMBINED_DOWNSIDE and s.status == "RESOLVED"), None)

        # Centralized rate stress hike
        rate_increase_pct_points = POLICY_STRESS_PARAMETERS["INTEREST_RATE_STRESS"]["rate_increase_pct_points"]
        rate_hike = rate_increase_pct_points / 100.0

        for sc in scheme_options:
            # Consider schemes that are ELIGIBLE or VERIFICATION_REQUIRED
            if sc.eligibility_status not in (SchemeEligibilityStatus.ELIGIBLE, SchemeEligibilityStatus.VERIFICATION_REQUIRED):
                continue

            # Strict non-fabrication: ALL critical numerical terms AND boundaries must be resolved
            if (
                sc.status == "UNRESOLVED" or
                sc.min_project_cost is None or
                sc.max_project_cost is None or
                sc.maximum_loan_limit is None or
                sc.max_financing_percentage is None or
                sc.required_margin_percentage is None or
                sc.interest_rate is None or
                sc.tenure_months is None or
                sc.moratorium_months is None or
                sc.max_loan is None
            ):
                continue

            max_loan = sc.max_loan
            req_margin_pct = sc.required_margin_percentage
            req_margin_amt = round(cost * (req_margin_pct / 100.0), 2)
            interest_rate = sc.interest_rate
            moratorium = sc.moratorium_months
            max_tenure = sc.tenure_months

            # Scheme-specific loan & promoter margin determination
            cand_status = "RESOLVED" if (available_promoter_contribution is not None and is_other_fin_known) else "UNRESOLVED"
            gap: Optional[float] = None
            surplus: Optional[float] = None
            is_gap_eliminated = False
            actual_loan: Optional[float] = None
            prom_contrib: Optional[float] = None
            margin_diff: Optional[float] = None
            is_margin_met = False

            if cand_status == "RESOLVED":
                other_fin = float(other_verified_financing)
                # Scheme margin requirement determines the minimum promoter margin invested in project
                ideal_loan = max(0.0, round(cost - req_margin_amt - other_fin, 2))
                actual_loan = min(ideal_loan, max_loan)
                # Promoter contribution required to balance project financing under this scheme
                prom_contrib = max(0.0, round(cost - actual_loan - other_fin, 2))
                total_fund = round(prom_contrib + actual_loan + other_fin, 2)
                gap = max(0.0, round(cost - total_fund, 2))
                surplus = max(0.0, round(total_fund - cost, 2))
                is_gap_eliminated = (gap <= 1.0)
                # Promoter margin check against available capital:
                # margin_diff represents surplus retained reserve (>0) or capital shortfall (<0)
                margin_diff = round(available_promoter_contribution - prom_contrib, 2)
                is_margin_met = (margin_diff >= -1.0)

            # Test standard tenures supported up to scheme max tenure
            test_tenures = [t for t in [36, 60, 84] if t <= max_tenure]
            if max_tenure not in test_tenures:
                test_tenures.append(max_tenure)
            test_tenures.sort()

            for t in test_tenures:
                cand_id = f"CAND_{sc.scheme_id}_{t}M"

                if cand_status == "RESOLVED":
                    lm = self.loan_calc.calculate_emi(
                        principal=actual_loan,
                        annual_rate=interest_rate,
                        tenure_months=t,
                        moratorium_months=moratorium
                    )
                    monthly_emi = lm.monthly_emi
                    total_interest = lm.total_interest
                    annual_ds = round(monthly_emi * 12.0, 2)

                    # Base DSCR
                    b_dscr: Optional[float] = None
                    if base_cads is not None and annual_ds > 0:
                        b_dscr = round(base_cads / annual_ds, 2) if base_cads > 0 else 0.0

                    # Actual Scenario-Derived DSCRs
                    rev_dscr: Optional[float] = None
                    if rev_sc and rev_sc.cads is not None and annual_ds > 0:
                        rev_dscr = round(rev_sc.cads / annual_ds, 2) if rev_sc.cads > 0 else 0.0

                    cost_dscr: Optional[float] = None
                    if cost_sc and cost_sc.cads is not None and annual_ds > 0:
                        cost_dscr = round(cost_sc.cads / annual_ds, 2) if cost_sc.cads > 0 else 0.0

                    wc_dscr: Optional[float] = None
                    if wc_sc and wc_sc.cads is not None and annual_ds > 0:
                        wc_dscr = round(wc_sc.cads / annual_ds, 2) if wc_sc.cads > 0 else 0.0

                    comb_dscr: Optional[float] = None
                    if comb_sc and comb_sc.cads is not None and annual_ds > 0:
                        comb_dscr = round(comb_sc.cads / annual_ds, 2) if comb_sc.cads > 0 else 0.0

                    rate_dscr: Optional[float] = None
                    stressed_rate = round(interest_rate + rate_hike, 4)
                    stressed_lm = self.loan_calc.calculate_emi(
                        principal=actual_loan,
                        annual_rate=stressed_rate,
                        tenure_months=t,
                        moratorium_months=moratorium
                    )
                    stressed_annual_ds = round(stressed_lm.monthly_emi * 12.0, 2)
                    rate_cads = rate_sc.cads if (rate_sc and rate_sc.cads is not None) else base_cads
                    if rate_cads is not None and stressed_annual_ds > 0:
                        rate_dscr = round(rate_cads / stressed_annual_ds, 2) if rate_cads > 0 else 0.0

                    # Min across resolved downside scenario DSCRs
                    resolved_dscrs = [d for d in [rev_dscr, cost_dscr, wc_dscr, rate_dscr, comb_dscr] if d is not None]
                    s_dscr: Optional[float] = None
                    if resolved_dscrs:
                        s_dscr = min(resolved_dscrs)
                    elif stress_cads is not None and annual_ds > 0:
                        s_dscr = round(stress_cads / annual_ds, 2) if stress_cads > 0 else 0.0

                    is_compliant = (
                        cost >= sc.min_project_cost and
                        cost <= sc.max_project_cost and
                        actual_loan <= max_loan and
                        t <= max_tenure
                    )

                    downside_dscr = comb_dscr if comb_dscr is not None else (s_dscr if s_dscr is not None else None)
                    if actual_loan == 0.0:
                        is_feasible = (
                            is_compliant and
                            is_gap_eliminated and
                            is_margin_met
                        )
                    else:
                        is_feasible = (
                            is_compliant and
                            is_gap_eliminated and
                            is_margin_met and
                            (b_dscr is not None and b_dscr >= 1.0)
                        )

                    reasons: List[M5ReasonCode] = []
                    if is_gap_eliminated:
                        reasons.append(M5ReasonCode.FINANCING_GAP_ELIMINATED)
                    if is_margin_met:
                        reasons.append(M5ReasonCode.MARGIN_REQUIREMENT_MET)
                    if actual_loan == 0.0:
                        reasons.append(M5ReasonCode.EXPLICIT_ZERO_DEBT)
                    else:
                        if b_dscr is not None and b_dscr >= 1.0:
                            reasons.append(M5ReasonCode.DEBT_SERVICE_FEASIBLE)
                        if downside_dscr is not None and downside_dscr >= DSCR_RESILIENCE_MINIMUM:
                            reasons.append(M5ReasonCode.DOWNSIDE_RESILIENT)

                    feas_status = "FEASIBLE" if is_feasible else "INELIGIBLE_OR_STRESSED"
                    prov.record(
                        metric=f"{cand_id}_feasibility",
                        value=feas_status,
                        source="DERIVED",
                        source_reference=f"Financing option {sc.scheme_name} at {t} months",
                        calculation_method="Multi-constraint feasibility check against base and stress coverage"
                    )
                else:
                    # Funding inputs unresolved: do not fabricate financial quantities
                    monthly_emi = None
                    total_interest = None
                    annual_ds = None
                    b_dscr = None
                    rev_dscr = None
                    cost_dscr = None
                    wc_dscr = None
                    rate_dscr = None
                    comb_dscr = None
                    s_dscr = None
                    downside_dscr = None
                    is_compliant = (
                        cost >= sc.min_project_cost and
                        cost <= sc.max_project_cost and
                        t <= max_tenure
                    )
                    is_feasible = False
                    feas_status = "UNRESOLVED"
                    reasons = [M5ReasonCode.INSUFFICIENT_DATA]
                    prov.record(
                        metric=f"{cand_id}_feasibility",
                        value="UNRESOLVED",
                        source="DERIVED",
                        source_reference=f"Financing option {sc.scheme_name} at {t} months",
                        calculation_method="Candidate generated with unresolved funding inputs"
                    )

                candidates.append(FinancingStructureCandidate(
                    candidate_id=cand_id,
                    scheme_id=sc.scheme_id,
                    scheme_name=sc.scheme_name,
                    total_project_cost=cost,
                    promoter_contribution=prom_contrib,
                    loan_amount=actual_loan,
                    other_financing=other_verified_financing,
                    interest_rate=interest_rate,
                    tenure_months=t,
                    moratorium_months=moratorium,
                    monthly_emi=monthly_emi,
                    total_interest=total_interest,
                    annual_debt_service=annual_ds,
                    financing_gap=gap,
                    financing_surplus=surplus,
                    required_margin_percentage=req_margin_pct,
                    required_margin_amount=req_margin_amt,
                    margin_surplus_or_gap=margin_diff,
                    is_scheme_compliant=is_compliant,
                    is_gap_eliminated=is_gap_eliminated,
                    is_margin_met=is_margin_met,
                    base_case_dscr=b_dscr,
                    revenue_downside_dscr=rev_dscr,
                    cost_downside_dscr=cost_dscr,
                    working_capital_stress_dscr=wc_dscr,
                    interest_rate_stress_dscr=rate_dscr,
                    combined_downside_dscr=comb_dscr,
                    stress_case_dscr=s_dscr,
                    feasibility_status=feas_status,
                    decision_rank=999,
                    selection_reasons=reasons,
                    status=cand_status
                ))

        return candidates


financing_options_generator = FinancingOptionsGenerator()
