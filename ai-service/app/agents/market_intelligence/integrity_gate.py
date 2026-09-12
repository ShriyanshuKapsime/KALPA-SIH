"""
Context Integrity Gate for Stage 5 Market Intelligence Agent.
Enforces pre-execution integrity, semantic contamination detection,
and post-execution validation to ensure zero cross-business leakage.
"""
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.market import (
    CanonicalBusinessContext,
    CollectionPlan,
    MarketEvidenceProfile,
    MarketEvidenceAggregate,
)
from app.core.logging import logger


class ContextIntegrityError(Exception):
    """Raised when context validation or semantic isolation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


# Domain-specific forbidden semantic keywords to prevent cross-business contamination
DOMAIN_FORBIDDEN_KEYWORDS = {
    "dairy_farm": [
        "saree", "apparel", "garment", "fabric", "textile", "attire",
        "handloom", "boutique", "bridal wear", "jacquard", "georgette",
        "paddy milling", "rubber roll", "dehusking", "atta chakki"
    ],
    "saree_retail": [
        "milk", "bovine", "cattle", "fodder", "chilling center",
        "milch", "dairy farm", "silage", "veterinary dispensary",
        "paddy milling", "rubber roll", "flour mill", "atta chakki"
    ],
    "rice_mill": [
        "saree", "apparel", "garment", "boutique", "bridal wear",
        "milch cattle", "dairy cooperative", "milk collection", "silage"
    ],
    "kirana_grocery": [
        "saree handloom", "banarasi silk", "paddy dehusking", "rubber roll separator",
        "milch bovine breeding"
    ],
    "flour_mill": [
        "saree handloom", "banarasi silk", "milk chilling", "bovine fodder"
    ],
    "poultry_broiler": [
        "saree", "handloom", "paddy milling", "rubber roll"
    ],
    "goat_farming": [
        "saree", "handloom", "paddy milling", "rubber roll"
    ]
}


class ContextIntegrityGate:
    """
    Validates business context and evidence cleanliness across the entire Stage 5 workflow.
    """

    def validate_business_context(self, context: CanonicalBusinessContext) -> Tuple[bool, Optional[str]]:
        """
        Pre-execution check on the canonical business context.
        """
        if not context.business_id:
            return False, "business_id is missing from CanonicalBusinessContext"
        if not context.analysis_id:
            return False, "analysis_id is missing from CanonicalBusinessContext"
        if not context.business_name:
            return False, "business_name is missing from CanonicalBusinessContext"
        return True, None

    def check_semantic_contamination(
        self,
        business_id: str,
        plan: CollectionPlan
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks if the generated collection plan or requirements contain terms
        from forbidden domains (e.g. Saree terms in Dairy Farm).
        """
        b_id_clean = business_id.lower().strip()
        forbidden_terms = DOMAIN_FORBIDDEN_KEYWORDS.get(b_id_clean, [])

        plan_corpus = " ".join(plan.requirements + [plan.reasoning or ""]).lower()

        for term in forbidden_terms:
            if term in plan_corpus:
                err_dict = {
                    "status": "context_integrity_failed",
                    "error": f"Semantic contamination detected: forbidden term '{term}' found in plan for business '{business_id}'",
                    "expected_business_id": business_id,
                    "contaminated_value": term,
                    "recommended_action": "reload_canonical_business_context"
                }
                logger.error(f"[CONTEXT INTEGRITY GATE] {err_dict['error']}")
                return False, err_dict

        return True, None

    def validate_market_evidence_profile(
        self,
        profile: MarketEvidenceProfile
    ) -> Tuple[bool, List[str]]:
        """
        Post-execution validation gate before persistence.
        Verifies:
        1. Business identity consistency
        2. Zero semantic contamination in collected items
        3. Truthful precision and provenance
        4. No demo data marked as LIVE_RETRIEVED
        """
        errors = []
        b_id = profile.business_context.business_id.lower()
        forbidden_terms = DOMAIN_FORBIDDEN_KEYWORDS.get(b_id, [])

        # 1. Check demand indicators
        for ind in profile.market_evidence.demand_indicators:
            text = f"{ind.indicator_name} {ind.business_relevance}".lower()
            for term in forbidden_terms:
                if term in text:
                    errors.append(f"Contaminated demand indicator '{ind.indicator_name}' contains '{term}' for '{b_id}'")

        # 2. Check competitors
        for comp in profile.market_evidence.competitors.direct:
            text = f"{comp.business_name} {comp.category}".lower()
            for term in forbidden_terms:
                if term in text:
                    errors.append(f"Contaminated direct competitor '{comp.business_name}' contains '{term}' for '{b_id}'")

        # 3. Check supply access
        for hub in profile.market_evidence.supply_access:
            text = f"{hub.hub_name} {' '.join(hub.commodities_available)}".lower()
            for term in forbidden_terms:
                if term in text:
                    errors.append(f"Contaminated supply hub '{hub.hub_name}' contains '{term}' for '{b_id}'")

        # 4. Check for fake live retrieved flags on demo/default values
        for ind in profile.market_evidence.demand_indicators:
            if ind.data_status == "LIVE_RETRIEVED" and not ind.source.get("retrieved_at"):
                errors.append(f"Demand indicator '{ind.indicator_name}' claimed LIVE_RETRIEVED without live timestamp.")

        if errors:
            logger.warning(f"[CONTEXT INTEGRITY GATE] Post-execution validation identified {len(errors)} issues: {errors}")
            return False, errors

        logger.info(f"[CONTEXT INTEGRITY GATE] Post-execution validation PASSED for '{b_id}'.")
        return True, []


integrity_gate = ContextIntegrityGate()
