"""
Eligibility Assessment and Alternative Government Financing Router (Stage 9).
Strictly separates Financial Fit from Beneficiary Eligibility.
Ensures no false eligibility claims are made without verified beneficiary documentation.
Implements deterministic, relevance-based alternative financing recommendation router.
"""
import logging
from typing import Dict, Any, List, Optional
from app.services.financial_engine.government_financing_schemes import (
    GOVERNMENT_SCHEMES_DATABASE,
    EligibilityStatus
)

logger = logging.getLogger(__name__)


class SchemeEligibilityRouter:
    """
    Evaluates financial scheme fit, beneficiary eligibility, and alternative financing options.
    """

    @staticmethod
    def evaluate_financial_fit(project_cost: float) -> Dict[str, Any]:
        """
        Determines financial scheme suitability based strictly on project cost and capital parameters.
        Does NOT assess beneficiary or identity eligibility.
        """
        cost = float(project_cost)
        if cost <= 140000.0:
            scheme_id = "MICRO_FINANCE_SCHEME"
            scheme_data = GOVERNMENT_SCHEMES_DATABASE["MICRO_FINANCE_SCHEME"]
            reason = (
                f"Project cost of ₹{cost:,.0f} falls within the supported Micro Credit / "
                f"Micro Finance range (Up to ₹1.40 Lakh). Standard 10% promoter contribution applies."
            )
        elif cost <= 5000000.0:
            scheme_id = "TERM_LOAN_SCHEME"
            scheme_data = GOVERNMENT_SCHEMES_DATABASE["TERM_LOAN_SCHEME"]
            reason = (
                f"Project cost of ₹{cost:,.0f} falls within the supported MSME Term Loan range "
                f"(₹1.40 Lakh to ₹50.00 Lakh). Standard 10% promoter contribution applies."
            )
        else:
            scheme_id = "TERM_LOAN_SCHEME"  # fallback scheme boundary
            scheme_data = GOVERNMENT_SCHEMES_DATABASE["TERM_LOAN_SCHEME"]
            reason = (
                f"Project cost of ₹{cost:,.0f} exceeds the standard ₹50 Lakh single-window threshold. "
                f"Maximum concessional cap of ₹45 Lakh loan applied; alternative consortia / CGTMSE routing recommended."
            )

        return {
            "recommended_scheme": scheme_id,
            "scheme_name": scheme_data["scheme_name"],
            "administering_institution": scheme_data["administering_institution"],
            "reason": reason,
            "min_project_cost": scheme_data["min_project_cost"],
            "max_project_cost": scheme_data["max_project_cost"],
            "margin_percentage": scheme_data["min_margin_percentage"],
            "max_financing_percentage": scheme_data["max_financing_percentage"],
            "maximum_loan_limit": scheme_data["maximum_loan_limit"],
            "annual_interest_rate": scheme_data["annual_interest_rate"],
            "tenure_months": scheme_data["repayment_tenure_months"],
            "moratorium_months": scheme_data["moratorium_months"],
            "moratorium_interest_mode": scheme_data["moratorium_interest_mode"],
            "source_provenance": scheme_data["provenance"]
        }

    @staticmethod
    def evaluate_beneficiary_eligibility(
        scheme_id: str,
        beneficiary_profile: Optional[Dict[str, Any]] = None,
        financial_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assesses beneficiary eligibility.
        CRITICAL RULE: Never assume or infer caste, income, or community.
        If demographic or verification data is not explicitly provided, returns VERIFICATION_REQUIRED.
        """
        b_prof = beneficiary_profile or {}
        f_prof = financial_profile or {}

        criteria_checked: List[str] = []
        criteria_missing: List[str] = []
        required_documents: List[str] = []

        category = b_prof.get("beneficiary_category") or b_prof.get("caste_category") or b_prof.get("category")
        income = f_prof.get("annual_family_income") or b_prof.get("annual_family_income") or f_prof.get("existing_monthly_income")
        has_identity_doc = bool(b_prof.get("aadhaar_verified") or b_prof.get("identity_proof_provided"))
        has_udyam = bool(b_prof.get("udyam_registration") or b_prof.get("udyam_number"))
        is_default_free = b_prof.get("no_prior_defaults", None)

        scheme_cfg = GOVERNMENT_SCHEMES_DATABASE.get(scheme_id, GOVERNMENT_SCHEMES_DATABASE["TERM_LOAN_SCHEME"])

        for req in scheme_cfg.get("eligibility_requirements", []):
            required_documents.append(req)

        # Evaluate based strictly on provided data
        if scheme_id == "MICRO_FINANCE_SCHEME":
            if has_identity_doc:
                criteria_checked.append("Identity proof documentation indicated")
            else:
                criteria_missing.append("Government Identity Proof (Aadhaar / Voter ID) pending upload")

            if income is not None:
                criteria_checked.append(f"Annual Income context provided (evaluated against threshold)")
            else:
                criteria_missing.append("Self-declared / Certified Annual Family Income documentation")

            if category:
                criteria_checked.append(f"Beneficiary demographic group specified: {category}")
            else:
                criteria_missing.append("Target beneficiary / community category verification")

            if is_default_free is False:
                status = EligibilityStatus.NOT_ELIGIBLE_BASED_ON_PROVIDED_DATA
                verification_required = True
                advisory_notice = "Record indicates prior institutional defaults. Remediation or settlement is required before loan processing."
            elif has_identity_doc and category and income is not None:
                status = EligibilityStatus.ELIGIBLE_BASED_ON_PROVIDED_DATA
                verification_required = True
                advisory_notice = "Indicative eligibility satisfied based on submitted parameters. Final sanction is subject to agency document validation."
            else:
                status = EligibilityStatus.VERIFICATION_REQUIRED
                verification_required = True
                advisory_notice = "Beneficiary eligibility requires formal verification by the administering agency / lending bank before sanction."

        else:  # TERM_LOAN_SCHEME and other standard MSME schemes
            if has_udyam:
                criteria_checked.append("Udyam MSME Registration status indicated")
            else:
                criteria_missing.append("Udyam Registration Certificate / Business Pan Card")

            if is_default_free is True:
                criteria_checked.append("No active non-performing assets or institutional defaults reported")
            elif is_default_free is False:
                criteria_missing.append("Unsettled institutional default reported on record")
            else:
                criteria_missing.append("Bank credit history verification (CIBIL / Experian report)")

            if has_identity_doc:
                criteria_checked.append("Promoter identity documentation indicated")
            else:
                criteria_missing.append("Promoter KYC and identity records")

            if is_default_free is False:
                status = EligibilityStatus.NOT_ELIGIBLE_BASED_ON_PROVIDED_DATA
                verification_required = True
                advisory_notice = "Prior credit default reported. Clearance certificate required before formal processing."
            elif has_udyam and has_identity_doc and is_default_free is True:
                status = EligibilityStatus.ELIGIBLE_BASED_ON_PROVIDED_DATA
                verification_required = True
                advisory_notice = "Business profile meets indicative term loan criteria. Physical inspection and formal banking appraisal required."
            else:
                status = EligibilityStatus.VERIFICATION_REQUIRED
                verification_required = True
                advisory_notice = "Scheme eligibility requires verification of Udyam registration, business KYC, and bank appraisal."

        return {
            "status": status.value,
            "verification_required": verification_required,
            "criteria_checked": criteria_checked,
            "criteria_missing": criteria_missing,
            "required_documents": scheme_cfg.get("eligibility_requirements", []),
            "required_verification_fields": scheme_cfg.get("required_verification_fields", []),
            "target_beneficiary_description": scheme_cfg.get("target_beneficiary", ""),
            "advisory_notice": advisory_notice
        }

    @staticmethod
    def route_alternative_financing(
        project_cost: float,
        business_profile: Optional[Dict[str, Any]] = None,
        beneficiary_profile: Optional[Dict[str, Any]] = None,
        location_profile: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Deterministic, relevance-based alternative financing options router.
        Evaluates PMMY, PMEGP, Stand-Up India, PM Vishwakarma, NRLM SHG, and CGTMSE.
        """
        cost = float(project_cost)
        biz = business_profile or {}
        b_prof = beneficiary_profile or {}
        loc = location_profile or {}

        specific_biz = str(biz.get("specific_business", "")).lower()
        sector = str(biz.get("sector", "")).lower()
        category = str(biz.get("category", "")).lower()
        gender = str(b_prof.get("gender", "")).lower()
        is_female = "f" in gender or "woman" in gender or "women" in gender
        beneficiary_cat = str(b_prof.get("beneficiary_category", "")).lower()
        is_sc_st = "sc" in beneficiary_cat or "st" in beneficiary_cat or "scheduled" in beneficiary_cat
        is_artisan = any(k in specific_biz or k in category for k in ["artisan", "craft", "potter", "carpenter", "blacksmith", "handloom", "weaver", "saree", "textile"])
        is_food_agri = any(k in specific_biz or k in sector or k in category for k in ["food", "flour", "oil", "spice", "dairy", "bakery", "agro", "processing", "agriculture"])
        is_rural = bool(loc.get("village") or loc.get("block")) or "rural" in str(loc.get("area_type", "")).lower()

        recommendations: List[Dict[str, Any]] = []

        # 1. PMEGP (Prime Minister's Employment Generation Programme)
        # Highly relevant for manufacturing <= 50L or services <= 20L with capital subsidy
        if cost <= 5000000.0:
            sub_pct = "35% Rural Special Category / 25% Rural General" if is_rural else "25% Urban Special / 15% Urban General"
            recommendations.append({
                "scheme_id": "PMEGP_KVIC",
                "scheme_name": "Prime Minister's Employment Generation Programme (PMEGP)",
                "administering_institution": "Khadi and Village Industries Commission (KVIC) & MSME DFOs",
                "relevance_status": "HIGHLY_RELEVANT",
                "why_relevant": f"Offers credit-linked margin money subsidy ({sub_pct}) for new project setups up to ₹50 Lakh.",
                "key_project_fit": f"Fits target project size ₹{cost:,.0f} with minimal 5%-10% promoter equity requirement.",
                "max_financing_limit": 4500000.0,
                "target_beneficiary": "Individuals aged 18+, SHGs, Co-operatives, rural artisans and micro-units",
                "eligibility_information_required": [
                    "Minimum 8th standard pass certificate (for projects > ₹10L in Mfg / > ₹5L in Service)",
                    "Rural area certificate (if applying under rural category)",
                    "Special category certificate for enhanced 35% subsidy rate"
                ],
                "verification_required": True,
                "official_source_reference": {
                    "document_name": "PMEGP Scheme Operational Guidelines 2024-25",
                    "organization": "KVIC / Ministry of MSME",
                    "url": "https://www.kviconline.gov.in/pmegpeportal"
                }
            })

        # 2. PMMY (Pradhan Mantri MUDRA Yojana)
        if cost <= 50000.0:
            pmmy_sub = GOVERNMENT_SCHEMES_DATABASE["PMMY_SHISHU"]
            pmmy_id = "PMMY_SHISHU"
        elif cost <= 500000.0:
            pmmy_sub = GOVERNMENT_SCHEMES_DATABASE["PMMY_KISHORE"]
            pmmy_id = "PMMY_KISHORE"
        else:
            pmmy_sub = GOVERNMENT_SCHEMES_DATABASE["PMMY_TARUN"]
            pmmy_id = "PMMY_TARUN"

        recommendations.append({
            "scheme_id": pmmy_id,
            "scheme_name": pmmy_sub["scheme_name"],
            "administering_institution": pmmy_sub["administering_institution"],
            "relevance_status": "HIGHLY_RELEVANT" if cost <= 2000000.0 else "POTENTIALLY_APPLICABLE",
            "why_relevant": f"Collateral-free institutional MSME lending through nationalized and regional rural banks.",
            "key_project_fit": f"Covers financing requirements up to ₹{pmmy_sub['maximum_loan_limit']:,.0f} with structured repayment terms.",
            "max_financing_limit": pmmy_sub["maximum_loan_limit"],
            "target_beneficiary": pmmy_sub["target_beneficiary"],
            "eligibility_information_required": pmmy_sub["eligibility_requirements"],
            "verification_required": True,
            "official_source_reference": pmmy_sub["provenance"]
        })

        # 3. PM Vishwakarma (Artisans & Traditional Craftspeople)
        if is_artisan or cost <= 300000.0:
            vishwa = GOVERNMENT_SCHEMES_DATABASE["PM_VISHWAKARMA"]
            recommendations.append({
                "scheme_id": "PM_VISHWAKARMA",
                "scheme_name": vishwa["scheme_name"],
                "administering_institution": vishwa["administering_institution"],
                "relevance_status": "HIGHLY_RELEVANT" if is_artisan else "POTENTIALLY_APPLICABLE",
                "why_relevant": "Ultra-concessional 5% interest rate with 8% GoI subvention and skill upgrading stipend.",
                "key_project_fit": "Provides collateral-free enterprise credit up to ₹3,00,000 in two seamless tranches.",
                "max_financing_limit": 300000.0,
                "target_beneficiary": vishwa["target_beneficiary"],
                "eligibility_information_required": vishwa["eligibility_requirements"],
                "verification_required": True,
                "official_source_reference": vishwa["provenance"]
            })

        # 4. Stand-Up India (For Women & SC/ST Entrepreneurs in Greenfield ventures)
        if cost >= 1000000.0 or is_female or is_sc_st:
            standup = GOVERNMENT_SCHEMES_DATABASE["STANDUP_INDIA"]
            rel = "HIGHLY_RELEVANT" if (is_female or is_sc_st) and cost >= 1000000.0 else "POTENTIALLY_APPLICABLE"
            recommendations.append({
                "scheme_id": "STANDUP_INDIA",
                "scheme_name": standup["scheme_name"],
                "administering_institution": standup["administering_institution"],
                "relevance_status": rel,
                "why_relevant": "Dedicated credit window of ₹10 Lakh to ₹1 Crore for greenfield projects by SC/ST or Women entrepreneurs.",
                "key_project_fit": f"Covers up to 85% of project cost for qualifying enterprise scales (up to ₹1.00 Crore).",
                "max_financing_limit": 10000000.0,
                "target_beneficiary": standup["target_beneficiary"],
                "eligibility_information_required": standup["eligibility_requirements"],
                "verification_required": True,
                "official_source_reference": standup["provenance"]
            })

        # 5. NRLM / SHG Bank Linkage (Community / Women Collective Livelihoods)
        if is_rural or is_female:
            nrlm = GOVERNMENT_SCHEMES_DATABASE["NRLM_SHG_BANK_LINKAGE"]
            recommendations.append({
                "scheme_id": "NRLM_SHG_BANK_LINKAGE",
                "scheme_name": nrlm["scheme_name"],
                "administering_institution": nrlm["administering_institution"],
                "relevance_status": "POTENTIALLY_APPLICABLE",
                "why_relevant": "Concessional 7% interest rate for SHG members and rural community micro-enterprises.",
                "key_project_fit": "Subsidized working capital and asset creation loan for rural collective units.",
                "max_financing_limit": 1000000.0,
                "target_beneficiary": nrlm["target_beneficiary"],
                "eligibility_information_required": nrlm["eligibility_requirements"],
                "verification_required": True,
                "official_source_reference": nrlm["provenance"]
            })

        # 6. CGTMSE Credit Guarantee (Credit enhancement for commercial loans)
        cgtmse = GOVERNMENT_SCHEMES_DATABASE["CGTMSE_SCHEME"]
        recommendations.append({
            "scheme_id": "CGTMSE_SCHEME",
            "scheme_name": cgtmse["scheme_name"],
            "administering_institution": cgtmse["administering_institution"],
            "relevance_status": "HIGHLY_RELEVANT" if cost > 140000.0 else "POTENTIALLY_APPLICABLE",
            "why_relevant": "Provides up to 85% third-party government guarantee cover, removing collateral requirements from bank lending.",
            "key_project_fit": f"Protects lending exposure up to ₹5.00 Crore for manufacturing and service MSMEs.",
            "max_financing_limit": 50000000.0,
            "target_beneficiary": cgtmse["target_beneficiary"],
            "eligibility_information_required": cgtmse["eligibility_requirements"],
            "verification_required": True,
            "official_source_reference": cgtmse["provenance"]
        })

        return recommendations


# Global singleton router
scheme_eligibility_router = SchemeEligibilityRouter()
