"""
Scheme Router for Milestone 5.
Routes the business through all applicable government schemes in the centralized
Stage 9 schemes database. Strictly enforces cost limits, loan ceilings, margin rules,
and documentation requirements without duplicating scheme data.
"""
from typing import Dict, Any, List, Optional
from app.services.financial_engine.government_financing_schemes import GOVERNMENT_SCHEMES_DATABASE
from app.services.financial_engine.optimizer.m5_schema import (
    SchemeRoutingOption,
    SchemeEligibilityStatus
)
from app.services.financial_engine.optimizer.m5_provenance import M5ProvenanceBuilder


class SchemeRouter:
    """
    Evaluates business eligibility across the curated government financing schemes database.
    """

    def evaluate_schemes(
        self,
        project_cost: Optional[float],
        available_promoter_contribution: Optional[float] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
        provenance: Optional[M5ProvenanceBuilder] = None
    ) -> List[SchemeRoutingOption]:
        prov = provenance or M5ProvenanceBuilder()
        user_in = user_inputs or {}
        options: List[SchemeRoutingOption] = []

        if project_cost is None or project_cost <= 0:
            # Cannot route unknown project cost
            for s_id, s_data in GOVERNMENT_SCHEMES_DATABASE.items():
                options.append(SchemeRoutingOption(
                    scheme_id=s_id,
                    scheme_name=s_data.get("scheme_name", s_id),
                    eligibility_status=SchemeEligibilityStatus.INSUFFICIENT_DATA,
                    eligibility_reasons=["Total project cost is unresolved or invalid."],
                    status="UNRESOLVED"
                ))
            return options

        cost = float(project_cost)

        for s_id, s_data in GOVERNMENT_SCHEMES_DATABASE.items():
            name = s_data.get("scheme_name", s_id)
            min_cost: Optional[float] = s_data.get("min_project_cost")
            max_cost: Optional[float] = s_data.get("max_project_cost")
            max_loan_limit: Optional[float] = s_data.get("maximum_loan_limit")
            min_margin_pct: Optional[float] = s_data.get("min_margin_percentage")
            max_fin_pct: Optional[float] = s_data.get("max_financing_percentage")
            interest_rate: Optional[float] = s_data.get("annual_interest_rate")
            tenure_months: Optional[int] = s_data.get("repayment_tenure_months")
            moratorium_months: Optional[int] = s_data.get("moratorium_months")

            reasons: List[str] = []
            rejections: List[str] = []
            status = SchemeEligibilityStatus.ELIGIBLE

            # Check missing critical numerical boundaries and terms
            missing_terms_list: List[str] = []
            if min_cost is None:
                missing_terms_list.append("min_project_cost")
            if max_cost is None:
                missing_terms_list.append("max_project_cost")
            if max_loan_limit is None:
                missing_terms_list.append("maximum_loan_limit")
            if min_margin_pct is None:
                missing_terms_list.append("margin percentage")
            if max_fin_pct is None:
                missing_terms_list.append("max financing percentage")
            if interest_rate is None:
                missing_terms_list.append("interest rate")
            if tenure_months is None:
                missing_terms_list.append("repayment tenure")
            if moratorium_months is None:
                missing_terms_list.append("moratorium period")

            has_missing_terms = len(missing_terms_list) > 0

            # 1. Project Cost Eligibility
            if min_cost is None or max_cost is None:
                status = SchemeEligibilityStatus.VERIFICATION_REQUIRED
                reasons.append(f"Scheme project cost boundaries missing ({'min_project_cost' if min_cost is None else ''} {'max_project_cost' if max_cost is None else ''}). Verification required.")
            elif cost < min_cost:
                status = SchemeEligibilityStatus.INELIGIBLE
                rejections.append(f"Project cost ₹{cost:,.2f} is below scheme minimum ₹{min_cost:,.2f}.")
            elif cost > max_cost:
                status = SchemeEligibilityStatus.INELIGIBLE
                rejections.append(f"Project cost ₹{cost:,.2f} exceeds scheme ceiling ₹{max_cost:,.2f}.")
            else:
                reasons.append(f"Project cost ₹{cost:,.2f} is within eligible range (₹{min_cost:,.0f} - ₹{max_cost:,.0f}).")

            # 2. Maximum Loan Capacity Under Scheme
            supported_loan: Optional[float] = None
            if max_fin_pct is not None and max_loan_limit is not None:
                loan_by_pct = round(cost * (max_fin_pct / 100.0), 2)
                supported_loan = min(loan_by_pct, max_loan_limit)

            # 3. Required Promoter Contribution
            req_promoter: Optional[float] = None
            if min_margin_pct is not None:
                req_promoter = round(cost * (min_margin_pct / 100.0), 2)

            # 4. Check missing critical financing terms or boundaries
            if has_missing_terms:
                if status == SchemeEligibilityStatus.ELIGIBLE:
                    status = SchemeEligibilityStatus.VERIFICATION_REQUIRED
                reasons.append(f"Financing terms or boundaries missing in scheme rules ({', '.join(missing_terms_list)}). Verification required.")

            # 5. Beneficiary Verification Checks
            req_fields = s_data.get("required_verification_fields", [])
            has_unverified = False
            for f in req_fields:
                if f not in user_in or user_in[f] is None:
                    has_unverified = True
                    break

            if status == SchemeEligibilityStatus.ELIGIBLE and has_unverified:
                status = SchemeEligibilityStatus.VERIFICATION_REQUIRED
                reasons.append(f"Statutory beneficiary documentation verification required ({', '.join(req_fields[:2])}).")

            # 6. Financing Gap / Surplus Calculation
            gap: Optional[float] = None
            surplus: Optional[float] = None
            opt_status = "RESOLVED"

            if has_missing_terms:
                opt_status = "UNRESOLVED"
            elif available_promoter_contribution is not None and supported_loan is not None:
                total_pot = available_promoter_contribution + supported_loan
                if total_pot < cost:
                    gap = round(cost - total_pot, 2)
                    surplus = 0.0
                else:
                    gap = 0.0
                    surplus = round(total_pot - cost, 2)
            else:
                opt_status = "PARTIALLY_DERIVED"

            prov.record(
                metric=f"scheme_{s_id}_eligibility",
                value=status.value,
                source="SCHEME_RULE",
                source_reference=f"{name} guidelines",
                calculation_method="Boundary evaluation against project cost and beneficiary documentation"
            )

            options.append(SchemeRoutingOption(
                scheme_id=s_id,
                scheme_name=name,
                eligibility_status=status,
                eligibility_reasons=reasons,
                min_project_cost=min_cost,
                max_project_cost=max_cost,
                max_supported_project_cost=max_cost,
                maximum_loan_limit=max_loan_limit,
                max_loan=supported_loan,
                max_financing_percentage=max_fin_pct,
                required_margin_percentage=min_margin_pct,
                required_promoter_contribution=req_promoter,
                interest_rate=interest_rate,
                tenure_months=tenure_months,
                moratorium_months=moratorium_months,
                financing_gap=gap,
                financing_surplus=surplus,
                status=opt_status,
                rejection_reasons=rejections
            ))

        return options


scheme_router = SchemeRouter()
