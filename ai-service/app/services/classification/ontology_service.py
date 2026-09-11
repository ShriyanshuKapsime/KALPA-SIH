import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from app.core.logging import logger

ONTOLOGY_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ontology", "business_ontology.json")

_ONTOLOGY_DATABASE: List[Dict[str, Any]] = []

# Generic ambiguous concepts requiring specific clarification
AMBIGUOUS_PATTERNS = [
    r"^(clothing|cloth|garment|apparel|textile)\s*(business|shop|store|work)?$",
    r"^(ಬಟ್ಟೆ|ಉಡುಪು)\s*(ವ್ಯಾಪಾರ|ಅಂಗಡಿ|ಉದ್ಯಮ)?$",
    r"^(कपड़े|वस्त्र)\s*(का\s*व्यापार|की\s*दुकान|का\s*काम)?$",
    r"^(shop|store|business|factory|farming|agriculture|service)$",
    r"^(ಅಂಗಡಿ|ವ್ಯಾಪಾರ|ಕೃಷಿ|ಉದ್ಯಮ)$",
    r"^(दुकान|व्यापार|खेती|उद्योग)$"
]


def load_ontology_data() -> List[Dict[str, Any]]:
    global _ONTOLOGY_DATABASE
    if _ONTOLOGY_DATABASE:
        return _ONTOLOGY_DATABASE
    try:
        if os.path.exists(ONTOLOGY_DATA_PATH):
            with open(ONTOLOGY_DATA_PATH, "r", encoding="utf-8") as f:
                _ONTOLOGY_DATABASE = json.load(f)
                logger.info(f"[ONTOLOGY SERVICE] Loaded {len(_ONTOLOGY_DATABASE)} KALPA Business Ontology nodes.")
        else:
            logger.warning(f"[ONTOLOGY SERVICE] Ontology data file not found at {ONTOLOGY_DATA_PATH}")
    except Exception as e:
        logger.error(f"[ONTOLOGY SERVICE] Failed to load Business Ontology: {e}")
        _ONTOLOGY_DATABASE = []
    return _ONTOLOGY_DATABASE


def is_ambiguous_concept(text: str) -> bool:
    clean = (text or "").strip().lower()
    for pattern in AMBIGUOUS_PATTERNS:
        if re.search(pattern, clean, re.IGNORECASE):
            return True
    return False


def normalize_business_concept(text: str, language_code: str = "en") -> str:
    """
    Normalizes vernacular phrases to standard business concepts.
    e.g. 'saree ki shop', 'ಸೀರೆ ಅಂಗಡಿ', 'साड़ी की दुकान' -> 'saree retail'
    """
    if not text:
        return ""
    
    clean = text.lower().strip()
    
    # Strip common filler prefixes / suffixes
    clean = re.sub(r"^(i want to (open|start|run|set up)|want to start|open a|start a)\s*", "", clean)
    clean = re.sub(r"^(ನಾನು|ನಾವು)\s*", "", clean)
    clean = re.sub(r"^(ಆರಂಭಿಸಲು|ಪ್ರಾರಂಭಿಸಲು|ಮಾಡಲು|ತೆರೆಯಲು)\s*(ಬಯಸುತ್ತೇನೆ|ಇಷ್ಟಪಡುತ್ತೇನೆ|ಆಶಿಸುತ್ತೇನೆ)?", "", clean)
    clean = re.sub(r"^(मैं|हम)\s*", "", clean)
    clean = re.sub(r"(शुरू करना चाहता हूं|खोलना चाहता हूं|करना चाहता हूं)$", "", clean)
    clean = clean.strip()
    
    # Direct vernacular normalization rules
    if any(k in clean for k in ["ಸೀರೆ", "साड़ी", "saree", "sari"]):
        return "saree retail"
    if any(k in clean for k in ["ಅಕ್ಕಿ ಗಿರಣಿ", "ರೈಸ್ ಮಿಲ್", "ಭತ್ತದ ಗಿರಣಿ", "ರಾಜ ಮುಡಿ", "राइस मिल", "चावल मिल", "धान मिल", "rice mill", "paddy mill"]):
        return "rice mill"
    if any(k in clean for k in ["ಹೈನುಗಾರಿಕೆ", "ಹಾಲು", "ಡೈರಿ", "ಹಸು ಸಾಕಾಣಿಕೆ", "डेयरी", "दूध", "पशुपालन", "dairy farm", "milk dairy"]):
        return "dairy farm"
    if any(k in clean for k in ["ಹಿಟ್ಟಿನ ಗಿರಣಿ", "ಆಟಾ ಚಕ್ಕಿ", "ರಾಗಿ ಹಿಟ್ಟು", "आटा चक्की", "पिसाई केंद्र", "flour mill", "atta chakki"]):
        return "flour mill"
    if any(k in clean for k in ["ಕೋಳಿ ಸಾಕಾಣಿಕೆ", "ಕೋಳಿ ಫಾರ್ಮ್", "ಮೊಟ್ಟೆ", "पोल्ट्री", "मुर्गी पालन", "poultry farm", "chicken farm"]):
        return "poultry farm"
    if any(k in clean for k in ["ಕಿರಾಣಿ", "ದವಸ ಧಾನ್ಯ", "ಪ್ರಾವಿಷನ್", "किराना", "राशन", "grocery", "kirana", "provision"]):
        return "kirana store"
    if any(k in clean for k in ["ಬೈಕ್ ರಿಪೇರಿ", "ದ್ವಿಚಕ್ರ ವಾಹನ", "ಗ್ಯಾರೇಜ್", "बाइक रिपेयर", "मोटरसाइकिल मैकेनिक", "two wheeler", "bike repair"]):
        return "two wheeler repair"
    if any(k in clean for k in ["ಟೈಲರಿಂಗ್", "ಬಟ್ಟೆ ಹೊಲಿಗೆ", "ಟೈಲರ್", "दर्जी", "सिलाई", "tailor", "tailoring"]):
        return "tailoring shop"
    if any(k in clean for k in ["ಮರಗೆಲಸ", "ಫರ್ನಿಚರ್", "ಬಡಗಿ", "बढ़ई", "फर्नीचर", "carpentry", "furniture"]):
        return "carpentry workshop"
    if any(k in clean for k in ["ವೆಲ್ಡಿಂಗ್", "ಫ್ಯಾಬ್ರಿಕೇಶನ್", "ಕಬ್ಬಿಣದ ಗ್ರಿಲ್", "वेल्डिंग", "लोहे का काम", "welding", "fabrication"]):
        return "welding workshop"
    if any(k in clean for k in ["ಬೇಕರಿ", "ಕೇಕ್", "ಬ್ರೆಡ್", "बेकरी", "केक", "bakery", "cake shop"]):
        return "bakery"
    if any(k in clean for k in ["ಹೋಟೆಲ್", "ಖಾನಾವಳಿ", "ಊಟದ ಹೋಟೆಲ್", "होटल", "ढाबा", "भोजनालय", "restaurant", "dhaba"]):
        return "restaurant"
    if any(k in clean for k in ["ಟೀ ಸ್ಟಾಲ್", "ಚಹಾ ಅಂಗಡಿ", "ಕಾಫಿ", "चाय की दुकान", "टी स्टॉल", "tea stall", "chai shop"]):
        return "tea stall"
    if any(k in clean for k in ["ಎಣ್ಣೆ ಗಾಣ", "ಕೊಬ್ಬರಿ ಎಣ್ಣೆ", "ಶೇಂಗಾ ಎಣ್ಣೆ", "तेल मिल", "कोल्हू", "घाणी", "oil mill", "oil expeller"]):
        return "oil mill"
    if any(k in clean for k in ["ಕೃಷಿ ಸೇವಾ ಕೇಂದ್ರ", "ಗೊಬ್ಬರ ಅಂಗಡಿ", "ಬೀಜ ಗೊಬ್ಬರ", "खाद बीज", "fertilizer shop", "seeds store"]):
        return "fertilizer seeds store"
    if any(k in clean for k in ["ಮೆಡಿಕಲ್ ಸ್ಟೋರ್", "ಔಷಧಿ ಅಂಗಡಿ", "दवा की दुकान", "मेडिकल", "medical store", "pharmacy"]):
        return "pharmacy"
    if any(k in clean for k in ["ಜೆರಾಕ್ಸ್", "ಗ್ರಾಮ ಒನ್", "ಸಿಎಸ್‌ಸಿ", "फोटोकॉपी", "साइबर कैफे", "xerox", "csc center", "cyber cafe"]):
        return "cyber csc center"
    if any(k in clean for k in ["ಬ್ಯೂಟಿ ಪಾರ್ಲರ್", "ಕ್ಷೌರದ ಅಂಗಡಿ", "ಸಲೂನ್", "ब्यूटी पार्लर", "नाई", "beauty parlour", "salon"]):
        return "beauty parlour"
    if any(k in clean for k in ["ಮಸಾಲೆ ಪುಡಿ", "ಖಾರದ ಪುಡಿ", "ಅರಿಶಿನ", "मसाला", "हल्दी", "spice grinding", "masala"]):
        return "spice grinding unit"
    
    return clean


def search_ontology_candidates(
    query_text: str,
    normalized_concept: str = "",
    product_service: str = "",
    limit: int = 5
) -> List[Dict[str, Any]]:
    nodes = load_ontology_data()
    if not nodes:
        return []

    norm_concept = (normalized_concept or "").lower().strip()
    full_text = f"{query_text} {norm_concept} {product_service}".lower().strip()
    
    scored_candidates = []

    for node in nodes:
        score = 0.0
        aliases = [a.lower().strip() for a in node.get("aliases", [])]
        keywords = [k.lower().strip() for k in node.get("keywords", [])]
        products = [p.lower().strip() for p in node.get("products", [])]
        services = [s.lower().strip() for s in node.get("services", [])]
        spec_bus = node.get("specific_business", "").lower()
        sub_cat = node.get("sub_category", "").lower()

        # 1. Exact alias match (highest confidence)
        for alias in aliases:
            if alias == norm_concept or alias == query_text.lower().strip():
                score += 0.90
                break
            elif alias in full_text:
                score += 0.70
                break

        # 2. Specific Business & Sub-Category match
        if spec_bus and (spec_bus in full_text or norm_concept in spec_bus):
            score += 0.60
        if sub_cat and sub_cat in full_text:
            score += 0.40

        # 3. Keyword matches
        for kw in keywords:
            if kw and kw in full_text:
                score += 0.30

        # 4. Products / Services match
        for prod in products:
            if prod and (prod in full_text or prod in norm_concept):
                score += 0.35
        for srv in services:
            if srv and srv in full_text:
                score += 0.25

        if score > 0.20:
            candidate_item = {
                "id": node.get("id"),
                "sector": node.get("sector"),
                "category": node.get("category"),
                "sub_category": node.get("sub_category"),
                "specific_business": node.get("specific_business"),
                "products": node.get("products", []),
                "services": node.get("services", []),
                "nic_candidates": node.get("nic_candidates", []),
                "score": round(min(score, 1.0), 3)
            }
            scored_candidates.append(candidate_item)

    scored_candidates.sort(key=lambda x: x["score"], reverse=True)
    return scored_candidates[:limit]
