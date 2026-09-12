"""
Centralized Government Financing Schemes & Policy Rules (Stage 9).
Provides structured database of curated government financing schemes,
concessional microfinance, term loans, and credit enhancement programs.
Preserves official provenance and strict parameter boundaries.
"""
from typing import Dict, Any, List, Optional
from enum import Enum


class EligibilityStatus(str, Enum):
    ELIGIBLE_BASED_ON_PROVIDED_DATA = "ELIGIBLE_BASED_ON_PROVIDED_DATA"
    NOT_ELIGIBLE_BASED_ON_PROVIDED_DATA = "NOT_ELIGIBLE_BASED_ON_PROVIDED_DATA"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


# Curated schemes database with parameters, limits, and documentation requirements
GOVERNMENT_SCHEMES_DATABASE: Dict[str, Dict[str, Any]] = {
    "MICRO_FINANCE_SCHEME": {
        "scheme_id": "MICRO_FINANCE_SCHEME",
        "scheme_name": "Micro Credit / Micro Finance Scheme",
        "administering_institution": "National / State Concessional Finance Development Corporation & MUDRA",
        "ministry": "Ministry of Micro, Small and Medium Enterprises / Social Justice",
        "target_beneficiary": "Micro-entrepreneurs, rural artisan workshops, nano-enterprises, backward class / underserved beneficiaries",
        "min_project_cost": 5000.0,
        "max_project_cost": 140000.0,  # Up to ₹1.40 lakh
        "min_margin_percentage": 10.0, # 10% Beneficiary Contribution
        "max_financing_percentage": 90.0, # Up to 90% Financing
        "maximum_loan_limit": 125000.0, # Maximum loan ₹1.25 lakh
        "annual_interest_rate": 0.065, # 6.5% p.a.
        "repayment_tenure_months": 36, # 3 years
        "moratorium_months": 3, # 3 months moratorium
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": [
            "ALL_MICRO_ENTERPRISES",
            "ARTISAN_CRAFT",
            "RETAIL_SERVICE",
            "AGRI_ALLIED_MICRO"
        ],
        "eligibility_requirements": [
            "Valid government identity proof (Aadhaar / Voter ID)",
            "Beneficiary belongs to eligible target target group or recognized micro-enterprise category",
            "Annual family income within prescribed statutory limits where applicable (< ₹3.00 Lakh p.a.)",
            "No existing default with any scheduled commercial bank or credit institution"
        ],
        "required_verification_fields": [
            "beneficiary_category",
            "community_certificate",
            "annual_family_income_proof",
            "bank_account_aadhaar_seed"
        ],
        "provenance": {
            "source_id": "KALPA_SIH_SPEC_MICRO",
            "organization": "Smart India Hackathon / Ministry of MSME",
            "document_name": "KALPA Baseline Financial Norms: Micro Finance Framework",
            "publication_year": 2026,
            "last_verified_date": "2026-09-12"
        }
    },
    "TERM_LOAN_SCHEME": {
        "scheme_id": "TERM_LOAN_SCHEME",
        "scheme_name": "MSME Term Loan Scheme",
        "administering_institution": "Scheduled Commercial Banks, RRBs & State Financial Corporations",
        "ministry": "Ministry of MSME / Department of Financial Services",
        "target_beneficiary": "Small & Medium Enterprises, Food Processors, Light Manufacturing, Retail Establishments",
        "min_project_cost": 140000.01, # Above ₹1.40 lakh
        "max_project_cost": 5000000.0,  # Up to ₹50 lakh
        "min_margin_percentage": 10.0, # 10% Beneficiary Contribution
        "max_financing_percentage": 90.0, # Up to 90% Financing
        "maximum_loan_limit": 4500000.0, # Maximum loan ₹45 lakh
        "annual_interest_rate": 0.080, # 8.0% p.a.
        "repayment_tenure_months": 84, # Up to 7 years
        "moratorium_months": 6, # 6 months moratorium
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": [
            "MANUFACTURING",
            "AGRO_PROCESSING",
            "COMMERCIAL_RETAIL",
            "SERVICES",
            "VALUE_ADDED_FOOD"
        ],
        "eligibility_requirements": [
            "Indian citizen aged 18+ with enterprise registration (Udyam Registration Certificate)",
            "Viable business project report / detailed project profile",
            "Satisfactory credit history (CIBIL score compliant with bank norms)",
            "Premises ownership or registered rent/lease deed for operational site"
        ],
        "required_verification_fields": [
            "udyam_registration_number",
            "business_pan",
            "project_report_dpr",
            "prior_6mo_bank_statements"
        ],
        "provenance": {
            "source_id": "KALPA_SIH_SPEC_TERMLOAN",
            "organization": "Smart India Hackathon / Ministry of MSME",
            "document_name": "KALPA Baseline Financial Norms: Term Loan Framework",
            "publication_year": 2026,
            "last_verified_date": "2026-09-12"
        }
    },
    "PMMY_SHISHU": {
        "scheme_id": "PMMY_SHISHU",
        "scheme_name": "Pradhan Mantri MUDRA Yojana (PMMY) - Shishu",
        "administering_institution": "Micro Units Development & Refinance Agency (MUDRA) & Commercial Banks",
        "ministry": "Department of Financial Services, Ministry of Finance",
        "target_beneficiary": "Nano entrepreneurs, street vendors, small artisans, petty shopkeepers",
        "min_project_cost": 5000.0,
        "max_project_cost": 50000.0,
        "min_margin_percentage": 0.0,
        "max_financing_percentage": 100.0,
        "maximum_loan_limit": 50000.0,
        "annual_interest_rate": 0.0875,
        "repayment_tenure_months": 36,
        "moratorium_months": 1,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["RETAIL_MICRO", "ARTISAN", "STREET_VENDING", "MICRO_SERVICES"],
        "eligibility_requirements": [
            "Identity and residence proof",
            "Quotations for machinery/inventory items to be financed",
            "No collateral or third-party guarantee needed"
        ],
        "required_verification_fields": ["aadhaar_card", "bank_account", "quotation_of_items"],
        "provenance": {
            "source_id": "MUDRA_OFFICIAL_PMMY",
            "organization": "MUDRA / Ministry of Finance",
            "document_name": "PMMY Shishu Guidelines",
            "publication_year": 2024,
            "last_verified_date": "2026-02-20"
        }
    },
    "PMMY_KISHORE": {
        "scheme_id": "PMMY_KISHORE",
        "scheme_name": "Pradhan Mantri MUDRA Yojana (PMMY) - Kishore",
        "administering_institution": "MUDRA / Scheduled Commercial Banks / RRBs",
        "ministry": "Department of Financial Services, Ministry of Finance",
        "target_beneficiary": "Growing small enterprises, workshops, local retail and service establishments",
        "min_project_cost": 50001.0,
        "max_project_cost": 500000.0,
        "min_margin_percentage": 10.0,
        "max_financing_percentage": 90.0,
        "maximum_loan_limit": 500000.0,
        "annual_interest_rate": 0.0925,
        "repayment_tenure_months": 60,
        "moratorium_months": 3,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["MANUFACTURING", "PROCESSING", "SERVICES", "TRADING", "AGRI_ALLIED"],
        "eligibility_requirements": [
            "Udyam registration certificate",
            "Past 6 months bank statement",
            "Quotations for plant & machinery"
        ],
        "required_verification_fields": ["udyam_certificate", "bank_statement_6mo", "machinery_quotation"],
        "provenance": {
            "source_id": "MUDRA_OFFICIAL_KISHORE",
            "organization": "MUDRA / Ministry of Finance",
            "document_name": "PMMY Kishore Guidelines",
            "publication_year": 2024,
            "last_verified_date": "2026-02-20"
        }
    },
    "PMMY_TARUN": {
        "scheme_id": "PMMY_TARUN",
        "scheme_name": "Pradhan Mantri MUDRA Yojana (PMMY) - Tarun / Tarun Plus",
        "administering_institution": "MUDRA & Commercial Lending Banks",
        "ministry": "Department of Financial Services, Ministry of Finance",
        "target_beneficiary": "Established MSMEs expanding operations or procuring higher technology equipment",
        "min_project_cost": 500001.0,
        "max_project_cost": 2000000.0,
        "min_margin_percentage": 15.0,
        "max_financing_percentage": 85.0,
        "maximum_loan_limit": 2000000.0,
        "annual_interest_rate": 0.0975,
        "repayment_tenure_months": 84,
        "moratorium_months": 6,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["FOOD_PROCESSING", "MANUFACTURING", "SERVICES", "COMMERCIAL_LOGISTICS"],
        "eligibility_requirements": [
            "Udyam Registration",
            "ITR filings for past 2 years",
            "Audited or projected financial balance sheets"
        ],
        "required_verification_fields": ["itr_past_2yrs", "audited_balance_sheet", "udyam_certificate"],
        "provenance": {
            "source_id": "MUDRA_OFFICIAL_TARUN",
            "organization": "MUDRA / Ministry of Finance",
            "document_name": "PMMY Tarun Guidelines & 2024 Enhanced Limits",
            "publication_year": 2024,
            "last_verified_date": "2026-02-20"
        }
    },
    "PMEGP_KVIC": {
        "scheme_id": "PMEGP_KVIC",
        "scheme_name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "administering_institution": "Khadi and Village Industries Commission (KVIC) & State KVI Boards",
        "ministry": "Ministry of Micro, Small and Medium Enterprises (MoMSME)",
        "target_beneficiary": "First-generation entrepreneurs, SHGs, rural youth, women and special category beneficiaries",
        "min_project_cost": 50000.0,
        "max_project_cost": 5000000.0, # 50L for Manufacturing, 20L for Service
        "min_margin_percentage": 5.0,  # 5% for Special Categories, 10% General
        "max_financing_percentage": 95.0,
        "maximum_loan_limit": 4500000.0,
        "annual_interest_rate": 0.095,
        "repayment_tenure_months": 84,
        "moratorium_months": 6,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "subsidy_pct_range": "15% - 35% Capital Margin Money Subsidy",
        "business_applicability": ["AGRO_FOOD_PROCESSING", "RURAL_ENGINEERING", "HANDICRAFTS", "SERVICES"],
        "eligibility_requirements": [
            "Individuals aged 18+ with minimum 8th standard pass for Mfg > ₹10L / Service > ₹5L",
            "Special Category Certificate for enhanced 35% rural margin money subsidy",
            "Rural Area Certificate from local Tehsildar / Gram Panchayat"
        ],
        "required_verification_fields": [
            "educational_qualification_proof",
            "special_category_certificate",
            "rural_area_certificate",
            "detailed_project_report_dpr"
        ],
        "provenance": {
            "source_id": "KVIC_PMEGP_GUIDELINES",
            "organization": "KVIC / Ministry of MSME",
            "document_name": "PMEGP Scheme Operational Guidelines 2024-25",
            "publication_year": 2024,
            "last_verified_date": "2026-02-15"
        }
    },
    "STANDUP_INDIA": {
        "scheme_id": "STANDUP_INDIA",
        "scheme_name": "Stand-Up India Scheme",
        "administering_institution": "Small Industries Development Bank of India (SIDBI) & Scheduled Commercial Banks",
        "ministry": "Department of Financial Services, Ministry of Finance",
        "target_beneficiary": "SC, ST, and Women entrepreneurs setting up greenfield non-farm enterprises",
        "min_project_cost": 1000000.0,
        "max_project_cost": 10000000.0, # ₹10 Lakh to ₹1 Crore
        "min_margin_percentage": 15.0,
        "max_financing_percentage": 85.0,
        "maximum_loan_limit": 10000000.0,
        "annual_interest_rate": 0.085,
        "repayment_tenure_months": 84,
        "moratorium_months": 18,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["MANUFACTURING", "SERVICES", "AGRI_ALLIED", "TRADING"],
        "eligibility_requirements": [
            "SC / ST or Woman entrepreneur with at least 51% shareholding",
            "Greenfield project (first-time venture in manufacturing, services, or trading sector)",
            "Borrower should not be in default to any bank / financial institution"
        ],
        "required_verification_fields": [
            "caste_certificate_or_women_identity",
            "greenfield_undertaking",
            "comprehensive_dpr",
            "udyam_registration"
        ],
        "provenance": {
            "source_id": "SIDBI_STANDUPMITRA",
            "organization": "SIDBI / Department of Financial Services",
            "document_name": "Stand-Up India Operational Manual",
            "publication_year": 2024,
            "last_verified_date": "2026-02-15"
        }
    },
    "PM_VISHWAKARMA": {
        "scheme_id": "PM_VISHWAKARMA",
        "scheme_name": "PM Vishwakarma Scheme",
        "administering_institution": "Ministry of MSME, Ministry of Skill Development, & Commercial Banks",
        "ministry": "Ministry of MSME",
        "target_beneficiary": "Traditional artisans and craftspeople across 18 designated trades",
        "min_project_cost": 10000.0,
        "max_project_cost": 300000.0,
        "min_margin_percentage": 0.0,
        "max_financing_percentage": 100.0,
        "maximum_loan_limit": 300000.0, # ₹1L Tranche 1 + ₹2L Tranche 2
        "annual_interest_rate": 0.050,  # 5% Concessional Interest Rate (Subvention of 8% by GoI)
        "repayment_tenure_months": 30,  # 18 mo (Tranche 1) + 30 mo (Tranche 2)
        "moratorium_months": 0,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["TRADITIONAL_CRAFT", "HANDLOOM", "BLACKSMITH", "CARPENTER", "POTTERY", "MASONRY"],
        "eligibility_requirements": [
            "Practicing artisan in one of 18 trades (carpenter, blacksmith, goldsmith, potter, etc.)",
            "Completion of basic 5-7 days skill verification training",
            "Age 18+, one member per family eligible"
        ],
        "required_verification_fields": [
            "pm_vishwakarma_certificate",
            "trade_skill_assessment_record",
            "aadhaar_biometric_auth"
        ],
        "provenance": {
            "source_id": "PM_VISHWAKARMA_PORTAL",
            "organization": "Ministry of MSME / MSDE",
            "document_name": "PM Vishwakarma Operational Guidelines",
            "publication_year": 2024,
            "last_verified_date": "2026-02-10"
        }
    },
    "NRLM_SHG_BANK_LINKAGE": {
        "scheme_id": "NRLM_SHG_BANK_LINKAGE",
        "scheme_name": "Deendayal Antyodaya Yojana - NRLM (SHG Bank Linkage)",
        "administering_institution": "National Rural Livelihoods Mission (NRLM) & Regional Rural Banks / Commercial Banks",
        "ministry": "Ministry of Rural Development",
        "target_beneficiary": "Women Self Help Groups (SHGs) and micro-enterprise collectives",
        "min_project_cost": 50000.0,
        "max_project_cost": 2000000.0,
        "min_margin_percentage": 5.0,
        "max_financing_percentage": 95.0,
        "maximum_loan_limit": 1000000.0,
        "annual_interest_rate": 0.070, # 7% with interest subvention for timely repayment
        "repayment_tenure_months": 48,
        "moratorium_months": 3,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["AGRI_PRODUCE_AGGREGATION", "HANDICRAFTS", "DAIRY_SHG", "LOCAL_FOOD_PRODUCTS"],
        "eligibility_requirements": [
            "Active SHG functioning for minimum 6 months following Panchasutra norms",
            "Satisfactory grading by NRLM / Bank",
            "No existing overdue loan"
        ],
        "required_verification_fields": [
            "shg_panchasutra_record_book",
            "nrlm_portal_registration_code",
            "group_resolution_for_loan"
        ],
        "provenance": {
            "source_id": "NRLM_MoRD",
            "organization": "Ministry of Rural Development",
            "document_name": "NRLM SHG Credit Linkage Manual",
            "publication_year": 2024,
            "last_verified_date": "2026-01-20"
        }
    },
    "CGTMSE_SCHEME": {
        "scheme_id": "CGTMSE_SCHEME",
        "scheme_name": "Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)",
        "administering_institution": "CGTMSE Trust (MoMSME & SIDBI)",
        "ministry": "Ministry of MSME & SIDBI",
        "target_beneficiary": "New and existing Micro and Small Enterprises seeking collateral-free bank loans",
        "min_project_cost": 50000.0,
        "max_project_cost": 50000000.0,
        "min_margin_percentage": 10.0,
        "max_financing_percentage": 90.0,
        "maximum_loan_limit": 50000000.0,
        "annual_interest_rate": 0.090,
        "repayment_tenure_months": 84,
        "moratorium_months": 6,
        "moratorium_interest_mode": "INTEREST_ONLY",
        "business_applicability": ["ALL_MICRO_SMALL_MANUFACTURING", "ALL_MICRO_SMALL_SERVICES"],
        "eligibility_requirements": [
            "Collateral-free credit facility sanctioned by Member Lending Institution (MLI)",
            "Valid Udyam Registration",
            "Standard credit appraisal clearance"
        ],
        "required_verification_fields": [
            "bank_sanction_letter",
            "udyam_registration_number"
        ],
        "provenance": {
            "source_id": "CGTMSE_OFFICIAL",
            "organization": "CGTMSE / SIDBI",
            "document_name": "CGTMSE Guarantee Operational Rules 2024",
            "publication_year": 2024,
            "last_verified_date": "2026-02-10"
        }
    }
}
