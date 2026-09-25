"""
Financial Archetype Registry.
Maps Stage 2/3 canonical business profiles to financial modelling archetypes.
These are FINANCIAL archetypes only — NOT a second business classification.
"""
import logging
from enum import Enum
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class FinancialArchetype(str, Enum):
    INVENTORY_RETAIL = "INVENTORY_RETAIL"
    SMALL_MANUFACTURING = "SMALL_MANUFACTURING"
    FOOD_PROCESSING = "FOOD_PROCESSING"
    SERVICE = "SERVICE"
    TRADING = "TRADING"
    AGRICULTURE = "AGRICULTURE"
    LIVESTOCK = "LIVESTOCK"
    CRAFT = "CRAFT"
    REPAIR = "REPAIR"
    OTHER = "OTHER"


# Deterministic mapping from Stage 2/3 sector+category to financial archetype.
# Finance does NOT re-classify the business. It maps the already-classified
# business identity to a financial modelling template.
_SECTOR_CATEGORY_MAP: Dict[str, Dict[str, FinancialArchetype]] = {
    "retail": {
        "_default": FinancialArchetype.INVENTORY_RETAIL,
        "apparel": FinancialArchetype.INVENTORY_RETAIL,
        "grocery": FinancialArchetype.INVENTORY_RETAIL,
        "general store": FinancialArchetype.INVENTORY_RETAIL,
        "electronics": FinancialArchetype.INVENTORY_RETAIL,
        "hardware": FinancialArchetype.INVENTORY_RETAIL,
        "stationery": FinancialArchetype.INVENTORY_RETAIL,
        "medical": FinancialArchetype.INVENTORY_RETAIL,
        "pharmacy": FinancialArchetype.INVENTORY_RETAIL,
    },
    "manufacturing": {
        "_default": FinancialArchetype.SMALL_MANUFACTURING,
        "food": FinancialArchetype.FOOD_PROCESSING,
        "food processing": FinancialArchetype.FOOD_PROCESSING,
        "agro-processing": FinancialArchetype.FOOD_PROCESSING,
        "agro processing": FinancialArchetype.FOOD_PROCESSING,
        "textiles": FinancialArchetype.SMALL_MANUFACTURING,
        "handicraft": FinancialArchetype.CRAFT,
        "handicrafts": FinancialArchetype.CRAFT,
        "woodwork": FinancialArchetype.CRAFT,
    },
    "services": {
        "_default": FinancialArchetype.SERVICE,
        "repair": FinancialArchetype.REPAIR,
        "maintenance": FinancialArchetype.REPAIR,
        "salon": FinancialArchetype.SERVICE,
        "beauty": FinancialArchetype.SERVICE,
        "transport": FinancialArchetype.SERVICE,
        "education": FinancialArchetype.SERVICE,
        "healthcare": FinancialArchetype.SERVICE,
        "tailoring": FinancialArchetype.SERVICE,
    },
    "service": {
        "_default": FinancialArchetype.SERVICE,
        "repair": FinancialArchetype.REPAIR,
    },
    "trading": {
        "_default": FinancialArchetype.TRADING,
    },
    "agriculture": {
        "_default": FinancialArchetype.AGRICULTURE,
        "dairy": FinancialArchetype.LIVESTOCK,
        "poultry": FinancialArchetype.LIVESTOCK,
        "fishery": FinancialArchetype.LIVESTOCK,
        "livestock": FinancialArchetype.LIVESTOCK,
        "animal husbandry": FinancialArchetype.LIVESTOCK,
    },
    "food & beverage": {
        "_default": FinancialArchetype.FOOD_PROCESSING,
        "restaurant": FinancialArchetype.SERVICE,
        "catering": FinancialArchetype.SERVICE,
    },
}

# Keyword fallback for specific_business name matching
_KEYWORD_MAP: List[tuple] = [
    (["saree", "garment", "cloth", "apparel", "boutique", "readymade"], FinancialArchetype.INVENTORY_RETAIL),
    (["grocery", "kirana", "general store", "provision"], FinancialArchetype.INVENTORY_RETAIL),
    (["pharmacy", "medical", "medicine"], FinancialArchetype.INVENTORY_RETAIL),
    (["electronics", "mobile", "hardware"], FinancialArchetype.INVENTORY_RETAIL),
    (["flour", "mill", "rice", "dal", "oil", "pickle", "papad", "masala", "spice"], FinancialArchetype.FOOD_PROCESSING),
    (["bakery", "sweet", "confectionery", "snack"], FinancialArchetype.FOOD_PROCESSING),
    (["dairy", "milk", "paneer", "ghee", "curd"], FinancialArchetype.LIVESTOCK),
    (["poultry", "chicken", "egg", "fish", "goat", "cattle"], FinancialArchetype.LIVESTOCK),
    (["weaving", "handloom", "pottery", "handicraft", "embroidery", "block print"], FinancialArchetype.CRAFT),
    (["carpentry", "woodwork", "furniture"], FinancialArchetype.CRAFT),
    (["repair", "mechanic", "welding", "plumbing", "electrician"], FinancialArchetype.REPAIR),
    (["salon", "beauty", "parlour", "parlor", "barber"], FinancialArchetype.SERVICE),
    (["tailoring", "stitching", "alteration"], FinancialArchetype.SERVICE),
    (["restaurant", "dhaba", "eatery", "canteen", "tiffin", "catering"], FinancialArchetype.SERVICE),
    (["coaching", "tuition", "training", "school"], FinancialArchetype.SERVICE),
    (["transport", "auto", "taxi", "logistics"], FinancialArchetype.SERVICE),
    (["farming", "cultivation", "horticulture", "nursery", "mushroom", "vermicompost"], FinancialArchetype.AGRICULTURE),
    (["trading", "wholesale", "export", "import", "distribution"], FinancialArchetype.TRADING),
    (["manufacturing", "production", "factory", "unit"], FinancialArchetype.SMALL_MANUFACTURING),
]


class ArchetypeRegistry:
    """
    Resolves a Stage 2/3 canonical business profile to a financial archetype.
    Does NOT modify or re-classify the business.
    """

    def resolve(
        self,
        specific_business: Optional[str] = None,
        sector: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        nic_code: Optional[str] = None,
    ) -> FinancialArchetype:
        """
        Deterministic archetype resolution.
        Priority: sector+category map → keyword match on specific_business → OTHER.
        """
        # 1. Try sector + category map
        if sector:
            sector_key = sector.strip().lower()
            cat_key = (category or "").strip().lower()
            subcat_key = (subcategory or "").strip().lower()

            if sector_key in _SECTOR_CATEGORY_MAP:
                cat_map = _SECTOR_CATEGORY_MAP[sector_key]
                # Try subcategory first, then category, then default
                for lookup in [subcat_key, cat_key]:
                    if lookup and lookup in cat_map:
                        result = cat_map[lookup]
                        logger.info(f"[FINANCE FOUNDATION] Resolved archetype={result.value} via sector={sector_key}, match={lookup}")
                        return result
                if "_default" in cat_map:
                    result = cat_map["_default"]
                    logger.info(f"[FINANCE FOUNDATION] Resolved archetype={result.value} via sector={sector_key} default")
                    return result

        # 2. Keyword match on specific_business
        if specific_business:
            biz_lower = specific_business.strip().lower()
            for keywords, archetype in _KEYWORD_MAP:
                if any(kw in biz_lower for kw in keywords):
                    logger.info(f"[FINANCE FOUNDATION] Resolved archetype={archetype.value} via keyword match on '{specific_business}'")
                    return archetype

        # 3. Fallback
        logger.info(f"[FINANCE FOUNDATION] No archetype mapping for specific_business='{specific_business}', sector='{sector}'. Defaulting to OTHER.")
        return FinancialArchetype.OTHER


# Global singleton
archetype_registry = ArchetypeRegistry()
