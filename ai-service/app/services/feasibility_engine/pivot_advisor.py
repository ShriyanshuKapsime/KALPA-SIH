"""
Pivot Advisor Engine (NO / Conditional Path).
Recommends viable alternative micro-enterprise candidates from the business ontology
matched directly to the entrepreneur's demonstrated skills, available capital, and location.
"""
from typing import List, Dict, Any, Optional
from app.schemas.feasibility import PivotCandidate, FeasibilityFeatureVector


class PivotAdvisorEngine:
    """Generates contextually grounded alternative business pivot recommendations."""

    # Curated Domain Pivot Ontologies for MSME Sectors
    PIVOT_CATALOG = {
        "textile_retail": [
            {
                "business_id": "tailoring_alteration_boutique",
                "business_name": "Custom Tailoring & Alteration Boutique",
                "sector": "textile_apparel",
                "category": "services",
                "capital_requirement": 120000.0,
                "base_skill_fit": 88.0,
                "pivot_reason": "Low initial capex with high gross operating margin (60-70%) that capitalizes on fabric and design expertise without heavy inventory risk.",
                "market_rationale": "High local demand for customized festive wear and alteration services with zero seasonal unsold inventory burden.",
                "key_advantages": [
                    "Requires 80% less working capital than full retail stock",
                    "Immediate positive daily cash flow with advance payments",
                    "Operates comfortably in a 100-150 sqft space with single-phase power"
                ]
            },
            {
                "business_id": "women_apparel_accessories",
                "business_name": "Ethnic Apparel Accessories & Dress Material Counter",
                "sector": "retail_trade",
                "category": "retail",
                "capital_requirement": 200000.0,
                "base_skill_fit": 82.0,
                "pivot_reason": "Fast-moving inventory with lower ticket prices and higher turnover frequency than premium saree retail.",
                "market_rationale": "Complementary retail segment that attracts regular footfall and impulse purchases.",
                "key_advantages": [
                    "High inventory velocity (stock turns 8-10x per year)",
                    "Lower minimum floor space requirement (120-180 sqft)",
                    "Minimal credit risk from retail consumers"
                ]
            },
            {
                "business_id": "textile_reselling_consignment",
                "business_name": "Textile Reselling & Sourcing Agency",
                "sector": "textile_trade",
                "category": "wholesale_reselling",
                "capital_requirement": 150000.0,
                "base_skill_fit": 78.0,
                "pivot_reason": "Leverages wholesale supplier connections to supply local self-help groups and home-based retailers on commission/reselling terms.",
                "market_rationale": "High demand among village/block entrepreneurs for curated bulk fabric sourcing without travel to major textile hubs.",
                "key_advantages": [
                    "Zero commercial shopfront lease requirement",
                    "Rapid capital recycling within 15-30 days",
                    "B2B network defensibility"
                ]
            }
        ],
        "food_processing": [
            {
                "business_id": "packaged_spice_grinding",
                "business_name": "Micro Spice Grinding & Packaging Unit",
                "sector": "food_processing",
                "category": "manufacturing",
                "capital_requirement": 250000.0,
                "base_skill_fit": 85.0,
                "pivot_reason": "High-margin value addition on local raw spices with simple single/split-phase grinding machines.",
                "market_rationale": "Strong rural and semi-urban preference for fresh, adulteration-free local spice powders over national brands.",
                "key_advantages": [
                    "Compatible with standard domestic/rural commercial power",
                    "Eligible for 35% PMEGP subsidy under micro-food category",
                    "Long shelf life (6-9 months) reducing perishable spoilage"
                ]
            },
            {
                "business_id": "dairy_chilling_collection",
                "business_name": "Local Milk Collection & Value-Added Paneer/Curd Unit",
                "sector": "dairy",
                "category": "processing",
                "capital_requirement": 280000.0,
                "base_skill_fit": 80.0,
                "pivot_reason": "Captures fresh milk margin without incurring livestock maintenance overheads.",
                "market_rationale": "Daily essential consumption in local catchment ensuring predictable 365-day cash flow.",
                "key_advantages": [
                    "Daily cash inflow eliminates receivables collection delay",
                    "Direct linkage with local livestock farmers",
                    "FSSAI micro-registration fast-track available"
                ]
            }
        ],
        "general_retail_services": [
            {
                "business_id": "digital_csc_center",
                "business_name": "Common Service Center (CSC) & Citizen Banking Point",
                "sector": "services",
                "category": "digital_services",
                "capital_requirement": 100000.0,
                "base_skill_fit": 90.0,
                "pivot_reason": "Near-zero inventory risk with guaranteed fee-per-transaction revenue from government/banking services.",
                "market_rationale": "High recurring village demand for Aadhaar, utility bill payment, Direct Benefit Transfer (DBT), and photocopying.",
                "key_advantages": [
                    "Extremely low break-even threshold (under ₹15,000/month)",
                    "Single-phase power + laptop/printer setup",
                    "Stable, recession-proof footfall"
                ]
            },
            {
                "business_id": "mobile_electronics_repair",
                "business_name": "Mobile & Small Appliance Repair Hub",
                "sector": "technical_services",
                "category": "repair",
                "capital_requirement": 140000.0,
                "base_skill_fit": 75.0,
                "pivot_reason": "Pure service model where revenue is driven by labor and replacement components.",
                "market_rationale": "Rapidly growing smartphone penetration in rural districts with sparse authorized service centers.",
                "key_advantages": [
                    "High gross service margin (70-80%)",
                    "Compact 80-120 sqft workbench requirement",
                    "Supported by PMKVY electronic hardware training"
                ]
            }
        ]
    }

    def recommend_pivots(
        self,
        feature_vector: FeasibilityFeatureVector,
        business_profile: Optional[Dict[str, Any]] = None,
        entrepreneur_data: Optional[Dict[str, Any]] = None
    ) -> List[PivotCandidate]:
        candidates: List[PivotCandidate] = []
        bus = business_profile or {}
        ent = entrepreneur_data or {}

        # 1. Identify Sector / Category Context
        biz_name = str(bus.get("specific_business") or bus.get("business_name") or "Retail").lower()
        sector = str(bus.get("sector") or bus.get("category") or "").lower()

        # Available capital / project cost from Stage 9
        avail_capital = float(feature_vector.project_cost.value or 500000.0)

        # 2. Match Domain Pool
        if "saree" in biz_name or "cloth" in biz_name or "textile" in biz_name or "garment" in biz_name or "apparel" in sector:
            pool = self.PIVOT_CATALOG["textile_retail"]
        elif "food" in biz_name or "spice" in biz_name or "dairy" in biz_name or "mill" in biz_name or "agri" in sector:
            pool = self.PIVOT_CATALOG["food_processing"]
        else:
            pool = self.PIVOT_CATALOG["general_retail_services"]

        # 3. Build Candidates
        for p in pool:
            cap_req = p["capital_requirement"]
            if cap_req <= avail_capital:
                cap_fit = "WITHIN_BUDGET"
            elif cap_req <= avail_capital * 1.25:
                cap_fit = "MINIMAL_GAP"
            else:
                cap_fit = "EXCEEDS_BUDGET"

            # Adjust skill fit based on entrepreneur skills score
            base_skill = p["base_skill_fit"]
            ent_skills = float(feature_vector.skills_score.value or 70.0)
            adjusted_fit = round(min(98.0, (base_skill * 0.6) + (ent_skills * 0.4)), 1)

            candidates.append(
                PivotCandidate(
                    business_id=p["business_id"],
                    business_name=p["business_name"],
                    sector=p["sector"],
                    category=p["category"],
                    pivot_reason=p["pivot_reason"],
                    skill_fit_percentage=adjusted_fit,
                    capital_requirement=cap_req,
                    capital_fit=cap_fit,
                    market_rationale=p["market_rationale"],
                    key_advantages=p["key_advantages"]
                )
            )

        return candidates


pivot_advisor_engine = PivotAdvisorEngine()
