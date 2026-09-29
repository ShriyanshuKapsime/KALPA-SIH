"""
Stage 14.2: Policy & Scheme Resolver.
Applies statutory rules, government subsidy policies, and nodal credit terms
from authoritative upstream scheme engines without silent defaults.
"""
import logging
from typing import Dict, Any, Optional

from app.services.dpr_stage2.dpr_enrichment_schemas import (
    EnrichmentSourceType,
    DerivationMethod,
)

logger = logging.getLogger(__name__)


class PolicySchemeResolver:
    """
    Resolves scheme subsidies, margin mandates, and moratorium guidelines with official provenance.
    """

    def resolve_policy_rules(
        self,
        scheme_context: Optional[Dict[str, Any]] = None,
        entrepreneur_profile: Optional[Dict[str, Any]] = None,
        location_profile: Optional[Dict[str, Any]] = None,
        project_cost: Optional[float] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Determines applicable statutory scheme parameters and records policy provenance.
        """
        s_ctx = scheme_context or {}
        e_prof = entrepreneur_profile or {}
        l_prof = location_profile or {}
        resolved_policy: Dict[str, Dict[str, Any]] = {}

        scheme_code = s_ctx.get("target_scheme_code") or s_ctx.get("scheme_code") or s_ctx.get("scheme_id")
        scheme_name = s_ctx.get("scheme_name") or scheme_code

        if not scheme_code:
            logger.info("[PolicySchemeResolver] No target scheme specified in upstream context.")
            return {}

        source_ref = f"Official Guidelines: {scheme_name or scheme_code}"

        # 1. Scheme Code & Name
        resolved_policy["target_scheme_code"] = {
            "value": scheme_code,
            "status": "RESOLVED_POLICY",
            "source_type": EnrichmentSourceType.POLICY_DERIVED,
            "source_id": scheme_code,
            "source_reference": source_ref,
            "confidence": 0.95,
            "derivation_method": DerivationMethod.STATUTORY_POLICY,
        }

        # 2. Scheme Subsidy Percentage
        subsidy_pct = s_ctx.get("subsidy_percentage") or s_ctx.get("scheme_subsidy_pct")
        if subsidy_pct is not None:
            resolved_policy["scheme_subsidy_percentage"] = {
                "value": float(subsidy_pct),
                "status": "RESOLVED_POLICY",
                "source_type": EnrichmentSourceType.POLICY_DERIVED,
                "source_id": f"{scheme_code}_SUBSIDY",
                "source_reference": f"{source_ref} — Capital Subsidy Matrix",
                "confidence": 0.95,
                "derivation_method": DerivationMethod.STATUTORY_POLICY,
            }

        # 3. Minimum Promoter Contribution Mandate
        margin_pct = s_ctx.get("promoter_margin_pct") or s_ctx.get("beneficiary_contribution_pct")
        if margin_pct is not None:
            resolved_policy["scheme_beneficiary_contribution_pct"] = {
                "value": float(margin_pct),
                "status": "RESOLVED_POLICY",
                "source_type": EnrichmentSourceType.POLICY_DERIVED,
                "source_id": f"{scheme_code}_MARGIN",
                "source_reference": f"{source_ref} — Minimum Equity Rule",
                "confidence": 0.95,
                "derivation_method": DerivationMethod.STATUTORY_POLICY,
            }

        # 4. Maximum Financeable Outlay / Ceiling
        max_limit = s_ctx.get("maximum_loan_limit") or s_ctx.get("max_project_cost")
        if max_limit is not None:
            resolved_policy["scheme_maximum_ceiling_inr"] = {
                "value": float(max_limit),
                "status": "RESOLVED_POLICY",
                "source_type": EnrichmentSourceType.POLICY_DERIVED,
                "source_id": f"{scheme_code}_CEILING",
                "source_reference": f"{source_ref} — Project Ceiling Limit",
                "confidence": 0.95,
                "derivation_method": DerivationMethod.STATUTORY_POLICY,
            }

        # 5. Collateral / CGTMSE Guarantee Coverage (Only if explicitly specified)
        if "cgtmse_eligible" in s_ctx and s_ctx["cgtmse_eligible"] is not None:
            cgtmse_covered = bool(s_ctx["cgtmse_eligible"])
            resolved_policy["credit_guarantee_cgtmse_status"] = {
                "value": "ELIGIBLE_FOR_CGTMSE_COVERAGE" if cgtmse_covered else "COLLATERAL_REQUIRED",
                "status": "RESOLVED_POLICY",
                "source_type": EnrichmentSourceType.POLICY_DERIVED,
                "source_id": "CGTMSE_TRUST_POLICY",
                "source_reference": "Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)",
                "confidence": 0.90,
                "derivation_method": DerivationMethod.STATUTORY_POLICY,
            }

        return resolved_policy


policy_scheme_resolver = PolicySchemeResolver()
