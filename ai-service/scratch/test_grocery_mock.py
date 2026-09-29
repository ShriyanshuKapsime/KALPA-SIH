import sys
import json
sys.path.insert(0, r"c:\Users\shriy\OneDrive\Documents\KALPA SIH\ai-service")
from app.services.dpr_stage1.dpr_canonical_field_registry import CANONICAL_FIELDS, resolve_canonical_id, get_canonical_entry

print("Total registered canonical fields:", len(CANONICAL_FIELDS))

# Mock upstream data for Grocery Store
grocery_sources = {
    "business_profile": {
        "business_name": "Kirana & Grocery Store",
        "specific_business": "Kirana & Grocery Store",
        "business_activity": "Kirana & Grocery Store",
        "business_archetype": "Essential Retail",
        "archetype": "Essential Retail",
        "category": "Essential Retail",
        "subcategory": "Grocery & Provision",
        "nic_code": "47110",
        "state": "Karnataka",
        "district": "Mandya",
        "constitution": "PROPRIETORSHIP",
        "premises_status": "RENTED",
        "carpet_area": 250.0,
        "carpet_area_sqft": 250.0,
        "promoter_name": "Suresh Kumar",
        "promoter_experience_years": 4.0,
        "education_level": "GRADUATE"
    },
    "classification": {
        "archetype": "Essential Retail",
        "category": "Essential Retail",
        "subcategory": "Grocery & Provision",
        "nic_code": "47110",
        "business_activity": "Kirana & Grocery Store"
    },
    "entrepreneur_readiness": {
        "relevant_sector_experience": 4.0,
        "prior_experience_years": 4.0,
        "overall_score": 88.0
    },
    "financial_package": {
        "total_project_cost": 300000.0,
        "project_cost": {
            "total_project_cost": 300000.0,
            "land_and_building": 0.0,
            "plant_and_machinery": 165000.0,
            "preliminary_and_preoperative": 15000.0,
            "working_capital_margin": 120000.0,
            "contingency_and_others": 15000.0
        },
        "means_of_finance": {
            "total_project_cost": 300000.0,
            "promoter_contribution": 30000.0,
            "term_loan": 270000.0,
            "subsidy_grant": 0.0,
            "scheme_name": "MSME Term Loan Scheme"
        },
        "banking_metrics": {
            "average_dscr": 12.83,
            "break_even_capacity_percentage": 15.4,
            "debt_equity_ratio": 9.0,
            "current_ratio": 2.1
        },
        "working_capital": {
            "inventory_holding_days": 20,
            "receivable_credit_days": 15,
            "working_capital_margin_req": 120000.0
        }
    },
    "user_answers": {
        "target_scheme_code": "Term"  # USER ANSWERED "Term"!
    }
}

print("Loaded test sources.")
