"""
Canonical Business Context Normalizer for Stage 5 Market Intelligence Agent.
Normalizes raw business profile input against Stage 4.5 Canonical Business Profiles.
Guarantees consistent, unambiguous business identity without fallback cross-contamination.
"""
import uuid
import re
from typing import Dict, Any, Optional
from app.schemas.market import CanonicalBusinessContext
from app.knowledge.services.knowledge_service import KnowledgeService
from app.core.logging import logger


CANONICAL_BUSINESS_ALIASES = {
    "dairy_farm": ["dairy farm", "commercial dairy", "dairy", "milk production", "bovine farming", "cow farm", "buffalo farm", "ont_dairy_farm"],
    "saree_retail": ["saree retail", "saree", "traditional apparel", "saree shop", "women's clothing", "handloom retail", "ont_saree_retail", "textile retail"],
    "rice_mill": ["rice mill", "mini rice mill", "modern rice mill", "paddy mill", "paddy dehusking", "ont_rice_mill", "paddy processing"],
    "kirana_grocery": ["kirana grocery", "grocery store", "kirana", "super-kirana", "general store", "grocery", "provision store", "ont_kirana_grocery"],
    "flour_mill": ["flour mill", "atta chakki", "grain grinding", "flour milling", "grain mill", "ont_flour_mill"],
    "spice_grinding": ["spice grinding", "masala grinding", "spice processing", "spice unit", "ont_spice_grinding"],
    "oil_expeller": ["oil expeller", "mustard oil mill", "edible oil extraction", "tel ghan", "oil mill", "ont_oil_expeller"],
    "bakery": ["bakery", "micro bakery", "biscuit manufacturing", "bread bakery", "confectionery", "ont_bakery"],
    "poultry_broiler": ["poultry broiler", "broiler farm", "poultry farm", "chicken rearing", "broiler poultry", "ont_poultry_broiler"],
    "goat_farming": ["goat farming", "stall fed goat", "goat rearing", "mutton goat unit", "goat breeding", "ont_goat_farming"],
    "garment_retail": ["garment retail", "readymade garments", "menswear store", "kids apparel", "clothing retail", "ont_garment_retail"],
    "two_wheeler_repair": ["two wheeler repair", "bike servicing", "motorcycle workshop", "two wheeler garage", "ont_two_wheeler_repair"],
    "welding_fabrication": ["welding fabrication", "steel fabrication", "grill welding", "metal fabrication", "ont_welding_fabrication"],
    "beauty_parlour": ["beauty parlour", "women salon", "beauty salon", "cosmetology unit", "ont_beauty_parlour"],
    "cold_storage": ["cold storage", "micro cold room", "solar cold storage", "agro cold storage", "ont_cold_storage"],
}


class BusinessContextNormalizer:
    """
    Normalizes any input business representation to a strict CanonicalBusinessContext.
    """

    def __init__(self, knowledge_service: Optional[KnowledgeService] = None):
        self.ks = knowledge_service or KnowledgeService()

    @classmethod
    def normalize(
        cls,
        raw_profile: Dict[str, Any],
        analysis_id: Optional[str] = None,
        session_id: Optional[str] = None,
        knowledge_service: Optional[KnowledgeService] = None
    ) -> CanonicalBusinessContext:
        """
        Extracts and normalizes business parameters to CanonicalBusinessContext.
        """
        ks = knowledge_service or KnowledgeService()
        analysis_id = analysis_id or raw_profile.get("analysis_id") or str(uuid.uuid4())
        session_id = session_id or raw_profile.get("session_id") or str(uuid.uuid4())

        bus_sec = raw_profile.get("business_profile") or {}
        if not isinstance(bus_sec, dict):
            bus_sec = {}

        # Extract candidates
        explicit_id = (
            raw_profile.get("business_id") or
            bus_sec.get("business_id") or
            bus_sec.get("business_node_id") or
            raw_profile.get("business_node_id") or
            ""
        ).strip().lower()

        specific_business = (
            bus_sec.get("specific_business") or
            bus_sec.get("business_name") or
            raw_profile.get("specific_business") or
            raw_profile.get("business_name") or
            ""
        ).strip()

        normalized_concept = (
            bus_sec.get("normalized_concept") or
            raw_profile.get("normalized_concept") or
            ""
        ).strip()

        nic_code = (
            bus_sec.get("nic", {}).get("code") if isinstance(bus_sec.get("nic"), dict) else
            bus_sec.get("nic_code") or
            raw_profile.get("nic_code") or
            ""
        )
        if nic_code:
            nic_code = str(nic_code).strip()

        sector = (
            bus_sec.get("sector") or
            raw_profile.get("sector") or
            "General Enterprise"
        ).strip()

        category = (
            bus_sec.get("category") or
            raw_profile.get("category") or
            specific_business or
            "Rural Enterprise"
        ).strip()

        # Step 1: Check against known alias table
        matched_canonical_id = None
        search_corpus = f"{explicit_id} {specific_business} {normalized_concept} {category}".lower()

        for c_id, aliases in CANONICAL_BUSINESS_ALIASES.items():
            if explicit_id == c_id or explicit_id.replace("ont_", "") == c_id:
                matched_canonical_id = c_id
                break
            for alias in aliases:
                # Match whole words or clean tokens
                if alias in search_corpus or re.search(r'\b' + re.escape(alias) + r'\b', search_corpus):
                    matched_canonical_id = c_id
                    break
            if matched_canonical_id:
                break

        # Step 2: Query Stage 4.5 Knowledge Base for exact profile
        known_profile = None
        if matched_canonical_id:
            known_profile = ks.business_repo.get_profile(matched_canonical_id)
        elif explicit_id:
            known_profile = ks.business_repo.get_profile(explicit_id)
        elif specific_business:
            known_profile = ks.business_repo.get_profile(specific_business)
        elif nic_code:
            known_profile = ks.business_repo.get_profile_by_nic(nic_code)

        if known_profile:
            canonical_id = getattr(known_profile, "business_node_id", None) or getattr(known_profile, "business_id", None) or matched_canonical_id
            b_name = getattr(known_profile, "business_title", None) or getattr(known_profile, "business_name", None) or specific_business
            b_cat = getattr(known_profile, "category", None) or category
            b_sector = getattr(known_profile, "sector", None) or sector
            b_nic = getattr(known_profile, "nic_code", None) or nic_code
            b_aliases = getattr(known_profile, "aliases", []) or []

            logger.info(f"[CONTEXT NORMALIZER] Successfully mapped '{specific_business or explicit_id}' -> Stage 4.5 canonical ID '{canonical_id}'")

            return CanonicalBusinessContext(
                business_id=canonical_id,
                business_name=b_name,
                business_category=b_cat or category,
                analysis_id=analysis_id,
                session_id=session_id,
                profile_version="1.0",
                classification_source="STAGE_4.5_CANONICAL",
                knowledge_profile_version="2026.1",
                specific_business=specific_business or b_name,
                normalized_concept=normalized_concept or canonical_id.replace("_", " "),
                sector=b_sector or sector,
                nic_code=b_nic or nic_code,
                aliases=b_aliases
            )

        # Step 3: Uncurated / Custom Business Context (Explicitly preserved without defaulting to Saree/Dairy)
        fallback_id = explicit_id or re.sub(r'[^a-z0-9]+', '_', specific_business.lower()).strip('_') or "uncurated_enterprise"
        logger.info(f"[CONTEXT NORMALIZER] Input '{specific_business or explicit_id}' is uncurated; normalized as '{fallback_id}'")

        return CanonicalBusinessContext(
            business_id=fallback_id,
            business_name=specific_business or fallback_id.replace("_", " ").title(),
            business_category=category or "Uncurated Category",
            analysis_id=analysis_id,
            session_id=session_id,
            profile_version="1.0",
            classification_source="UNCURATED_INTAKE",
            knowledge_profile_version="2026.1",
            specific_business=specific_business or fallback_id.replace("_", " ").title(),
            normalized_concept=normalized_concept or fallback_id.replace("_", " "),
            sector=sector,
            nic_code=nic_code,
            aliases=[]
        )


context_normalizer = BusinessContextNormalizer()
