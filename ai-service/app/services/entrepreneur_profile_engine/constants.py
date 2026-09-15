"""
Constants and benchmark weights for Stage 10 Entrepreneur Profile Engine.
"""

WEIGHT_SKILLS = 0.30
WEIGHT_EXPERIENCE = 0.25
WEIGHT_TRAINING = 0.15
WEIGHT_RESOURCES = 0.15
WEIGHT_OPERATIONS = 0.15

READINESS_THRESHOLD_HIGH = 75.0
READINESS_THRESHOLD_MODERATE = 50.0
READINESS_THRESHOLD_DEVELOPING = 25.0

# Canonical skill keywords mapping for MSME domains
DOMAIN_SKILL_SYNONYMS = {
    "flour_milling_micro": [
        "chakki", "flour milling", "grain", "grinding", "stone dressing", "atta", "motor", "weighing", "milling"
    ],
    "oil_expeller_unit": [
        "oil extraction", "expeller", "mustard", "groundnut", "cold pressed", "filtration", "press", "oil"
    ],
    "spice_grinding_packaging": [
        "spice", "grinding", "masala", "pulverizer", "packaging", "fssai", "sealing", "blending"
    ],
    "dairy_micro_chilling_aggregator": [
        "dairy", "milk", "chilling", "fat testing", "lactometer", "veterinary", "cattle", "hygiene"
    ],
    "poultry_broiler_farm": [
        "poultry", "broiler", "chicks", "feed management", "vaccination", "shed ventilation", "bird care"
    ],
    "handloom_weaving_unit": [
        "weaving", "handloom", "yarn", "warp", "weft", "jacquard", "textile", "loom"
    ],
    "apparel_retail": [
        "garments", "clothing", "tailoring", "retail", "textile sales", "inventory", "customer service", "fabrics"
    ],
    "solar_pump_repair_service": [
        "solar", "inverter", "pump", "electrical", "wiring", "diagnostics", "motor rewinding", "multimeter"
    ],
    "organic_fertilizer_composting": [
        "vermicompost", "composting", "earthworms", "organic manure", "dung", "moisture control"
    ]
}

# Standard MSME support programs
STANDARD_SUPPORT_PROGRAMS = {
    "SKILLS": {
        "title": "PMKVY / RSETI Skill Upgradation Program",
        "description": "Enroll in a localized 10-day hands-on technical training program under Pradhan Mantri Kaushal Vikas Yojana (PMKVY) or Rural Self Employment Training Institute (RSETI).",
        "link": "https://www.pmkvyofficial.org/"
    },
    "TRAINING": {
        "title": "Mandatory Food Safety / Quality Certification (FoSTaC)",
        "description": "Complete online or hybrid FoSTaC supervisor certification by FSSAI for food processing micro-units.",
        "link": "https://fostac.fssai.gov.in/"
    },
    "INFRASTRUCTURE": {
        "title": "Power Discom 3-Phase Commercial Connection Enhancement",
        "description": "Apply for state electricity board industrial/commercial 3-phase load extension with subsidized MSME tariff.",
        "link": "https://www.msme.gov.in/"
    },
    "ADVISORY": {
        "title": "KVIC / DIC Entrepreneurship Mentorship Hub",
        "description": "Access localized District Industries Centre (DIC) mentoring on statutory registers, billing, and GST compliance.",
        "link": "https://www.kviconline.gov.in/"
    }
}
