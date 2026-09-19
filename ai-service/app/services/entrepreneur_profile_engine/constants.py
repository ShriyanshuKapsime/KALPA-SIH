"""
Constants, benchmark weights, and verified institutional support catalogs for Stage 10 Entrepreneur Profile Engine.
"""

WEIGHT_SKILLS = 0.30
WEIGHT_EXPERIENCE = 0.25
WEIGHT_TRAINING = 0.15
WEIGHT_RESOURCES = 0.15
WEIGHT_OPERATIONS = 0.15

READINESS_THRESHOLD_HIGH = 75.0
READINESS_THRESHOLD_MODERATE = 50.0
READINESS_THRESHOLD_DEVELOPING = 25.0

# Normalized skill keywords mapping for MSME domains
DOMAIN_SKILL_SYNONYMS = {
    "saree_retail": [
        "retail_sales", "saree_retail", "customer_handling", "inventory_management", "fabric_inspection",
        "draping_presentation", "bookkeeping", "khata_management", "textile_sales", "customer_negotiation"
    ],
    "garment_store": [
        "retail_sales", "apparel_retailing", "customer_service", "stock_procurement", "visual_merchandising",
        "size_inventory_management", "billing", "customer_handling"
    ],
    "flour_milling_micro": [
        "chakki", "flour milling", "grain", "grinding", "stone dressing", "atta", "motor", "weighing",
        "milling", "stone_dressing", "grain_cleaning", "machine_maintenance"
    ],
    "oil_expeller_unit": [
        "oil extraction", "expeller", "mustard", "groundnut", "cold pressed", "filtration", "press",
        "oil", "oil_expeller_operation", "seed_cleaning", "oil_filtration", "cake_handling"
    ],
    "spice_grinding_packaging": [
        "spice", "grinding", "masala", "pulverizer", "packaging", "fssai", "sealing", "blending",
        "spice_grinding", "moisture_inspection", "hygienic_packaging", "fssai_compliance"
    ],
    "dairy_micro_chilling_aggregator": [
        "dairy", "milk", "chilling", "fat testing", "lactometer", "veterinary", "cattle", "hygiene",
        "livestock_handling", "milk_testing", "dairy_aggregation", "feed_management", "amcu_operation"
    ],
    "dairy_farm": [
        "dairy", "milk", "chilling", "fat testing", "lactometer", "veterinary", "cattle", "hygiene",
        "livestock_handling", "milk_testing", "feed_management", "animal_health_monitoring", "milking_hygiene"
    ],
    "poultry_farm": [
        "poultry", "broiler", "chicks", "feed management", "vaccination", "shed ventilation", "bird care",
        "poultry_broiler_management", "feed_rationing", "biosecurity_maintenance", "disease_monitoring"
    ],
    "grocery_store": [
        "retail_sales", "inventory_procurement", "bookkeeping", "customer_credit_management",
        "fmcg_merchandising", "stock_tracking", "electronic_weighing"
    ],
    "tailoring_shop": [
        "garment_stitching", "pattern_cutting", "fabric_handling", "sewing_machine_maintenance",
        "blouse_tailoring", "embroidery", "measurement_taking"
    ],
    "solar_pump_repair_service": [
        "solar", "inverter", "pump", "electrical", "wiring", "diagnostics", "motor rewinding", "multimeter",
        "solar_pump_diagnostics", "inverter_maintenance", "electrical_wiring", "borewell_troubleshooting"
    ],
    "organic_fertilizer_composting": [
        "vermicompost", "composting", "earthworms", "organic manure", "dung", "moisture control",
        "bed_moisture_maintenance", "pre_decomposition", "worm_separation"
    ],
    "goat_farming": [
        "goat_husbandry", "feed_management", "disease_monitoring", "shelter_management",
        "kid_rearing", "vaccination_schedule"
    ],
    "rice_mill": [
        "paddy_processing", "milling_machinery_operations", "moisture_testing", "grain_grading",
        "rubber_roll_adjustment", "broken_grain_tuning"
    ]
}

# Contextual Institutional Support Programs Catalog (Gap -> Capability -> Program -> Resource)
CONTEXTUAL_SUPPORT_CATALOG = {
    "INVENTORY_MANAGEMENT": {
        "gap": "Inventory Management & Stock Turnover",
        "priority": "HIGH",
        "why_it_matters": "Poor inventory control can increase dead stock, stock-outs during festival peaks, and tied-up working capital.",
        "recommended_action": "Complete short-term practical module on stock registers, minimum reorder points, and seasonal demand planning.",
        "resource_type": "LESSON",
        "resource_title": "MSME Stock Control & Reorder Level Practice Guide",
        "summary": "Step-by-step practical guide on daily stock register maintenance, fast vs slow moving categorization, and working capital optimization.",
        "provider": "National Institute for Micro, Small and Medium Enterprises (ni-msme)",
        "official_url": "https://www.nimsme.org",
        "estimated_duration": "1 week (Self-paced, 5 modules)",
        "eligibility": "Open to all retail & trading micro-entrepreneurs",
        "source": "KNOWLEDGE_DATABASE"
    },
    "RETAIL_SALES_SKILLS": {
        "gap": "Retail Merchandising & Customer Sales Conversion",
        "priority": "HIGH",
        "why_it_matters": "Active customer engagement and visual merchandising directly enhance store conversion and average basket size.",
        "recommended_action": "Enroll in the PMKVY Retail Sales Associate short-term certification program.",
        "resource_type": "GOVERNMENT_SCHEME",
        "resource_title": "PMKVY 4.0 Retail Sales Associate Certification",
        "summary": "Government-sponsored vocational training on customer service, digital payments, and visual store merchandising with recognized certification.",
        "provider": "National Skill Development Corporation (NSDC) / PMKVY",
        "official_url": "https://www.pmkvyofficial.org",
        "estimated_duration": "2 weeks (Hybrid / Classroom)",
        "eligibility": "Aadhaar-linked MSME founders & retail staff",
        "source": "KNOWLEDGE_DATABASE"
    },
    "FOOD_SAFETY_COMPLIANCE": {
        "gap": "Mandatory Food Safety Certification (FoSTaC)",
        "priority": "HIGH",
        "why_it_matters": "FSSAI compliance is legally required prior to commercial processing or food handling to prevent statutory penalties and food adulteration.",
        "recommended_action": "Complete the online FoSTaC Basic Food Safety Supervisor training and obtain certification.",
        "resource_type": "CERTIFICATION",
        "resource_title": "FSSAI FoSTaC Food Safety Supervisor Training",
        "summary": "Official FSSAI certification covering hygienic processing, storage standards, pest management, and statutory record-keeping for food micro-units.",
        "provider": "Food Safety and Standards Authority of India (FSSAI)",
        "official_url": "https://fostac.fssai.gov.in",
        "estimated_duration": "1 day (Online / Accredited Training Center)",
        "eligibility": "All food business operators (FBOs)",
        "source": "KNOWLEDGE_DATABASE"
    },
    "DAIRY_LIVESTOCK_MANAGEMENT": {
        "gap": "Scientific Livestock Management & Animal Health",
        "priority": "HIGH",
        "why_it_matters": "Improper feeding and delayed disease detection can reduce daily milk yield by 20-30% and cause high veterinary expenses.",
        "recommended_action": "Attend a 5-day hands-on dairy husbandry workshop at the district Krishi Vigyan Kendra (KVK).",
        "resource_type": "LESSON",
        "resource_title": "NDDB Scientific Dairy Farming & Ration Balancing Guide",
        "summary": "Hands-on guidelines on Total Mixed Ration (TMR), silage preparation, clean milk production, and early mastitis screening.",
        "provider": "National Dairy Development Board (NDDB)",
        "official_url": "https://www.nddb.coop",
        "estimated_duration": "5 days (Practical Field Training)",
        "eligibility": "Dairy farmers and micro-chilling operators",
        "source": "KNOWLEDGE_DATABASE"
    },
    "COMMERCIAL_POWER_UPGRADE": {
        "gap": "Commercial Power Sanction & Load Enhancement",
        "priority": "HIGH",
        "why_it_matters": "Operating heavy commercial machinery on domestic or single-phase lines leads to immediate motor burnout and supply disruption.",
        "recommended_action": "Submit online application for dedicated 3-Phase Commercial / Industrial LT load sanction through state Discom portal.",
        "resource_type": "GOVERNMENT_SCHEME",
        "resource_title": "State Electricity Discom Commercial MSME Load Sanction",
        "summary": "Streamlined single-window commercial power connection process with concessional MSME industrial tariff structure.",
        "provider": "State Power Distribution Corporation (Discom)",
        "official_url": "https://msme.gov.in",
        "estimated_duration": "15-21 working days for sanction",
        "eligibility": "Premise lease or ownership document with Udyam registration",
        "source": "KNOWLEDGE_DATABASE"
    },
    "ENTREPRENEURSHIP_EDP": {
        "gap": "Micro-Enterprise Incubation & Bookkeeping (EDP)",
        "priority": "MEDIUM",
        "why_it_matters": "First-time entrepreneurs benefit significantly from structured handholding on bookkeeping, pricing, working capital discipline, and statutory compliance.",
        "recommended_action": "Enroll in the 10-day Entrepreneurship Development Program (EDP) at your local RSETI / DIC centre.",
        "resource_type": "ADVISORY",
        "resource_title": "RSETI / KVIC Entrepreneurship Development Program",
        "summary": "Comprehensive foundation covering unit economics, bank loan liaison, ledger accounting, and dispute resolution for rural MSMEs.",
        "provider": "Rural Self Employment Training Institute (RSETI) / KVIC",
        "official_url": "https://www.kviconline.gov.in",
        "estimated_duration": "10 days (Free residential / non-residential)",
        "eligibility": "Aspiring and early-stage micro-entrepreneurs aged 18-45",
        "source": "KNOWLEDGE_DATABASE"
    },
    "SOLAR_TECHNICAL_TRAINING": {
        "gap": "Solar PV & Motor Diagnostics Certification",
        "priority": "HIGH",
        "why_it_matters": "Accurate VFD inverter diagnostics and safe high-voltage DC handling are necessary for reliable agricultural solar pump servicing.",
        "recommended_action": "Complete Suryamitra Skill Development Program certification under National Institute of Solar Energy.",
        "resource_type": "CERTIFICATION",
        "resource_title": "NISE Suryamitra Solar Technical Training Program",
        "summary": "Government-sponsored comprehensive technician training on solar PV installation, inverter maintenance, pump controller troubleshooting, and safety.",
        "provider": "National Institute of Solar Energy (NISE) / MNRE",
        "official_url": "https://suryamitra.nise.res.in",
        "estimated_duration": "3 months (Vocational Skill Program)",
        "eligibility": "ITI / Diploma in Electrical / Wireman",
        "source": "KNOWLEDGE_DATABASE"
    },
    "GENERAL_MSME_SUPPORT": {
        "gap": "General Micro-Enterprise Advisory & Credit Linkage",
        "priority": "MEDIUM",
        "why_it_matters": "Connecting with official district MSME advisory centers ensures access to statutory waivers, subsidy tracking, and trade dispute resolution.",
        "recommended_action": "Register on the MSME Champions portal to access district-level single-window facilitation.",
        "resource_type": "ADVISORY",
        "resource_title": "MSME Champions Single-Window Facilitation Desk",
        "summary": "Unified grievance redressal, government scheme credit linkage, and enterprise mentoring platform by Ministry of MSME.",
        "provider": "Ministry of Micro, Small and Medium Enterprises (MoMSME)",
        "official_url": "https://champions.gov.in",
        "estimated_duration": "Ongoing digital support",
        "eligibility": "All registered MSME units with Udyam number",
        "source": "KNOWLEDGE_DATABASE"
    }
}
