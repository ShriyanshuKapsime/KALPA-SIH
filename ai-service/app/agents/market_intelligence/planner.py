"""
Market Requirement Planner for Stage 5 Market Intelligence Agent.
Implements the Hybrid Planning Architecture:
- Level 1: Sarvam LLM Planning (sarvam-105b) with strict schema validation
- Level 2: Deterministic Domain Requirement Planner (Ontology + Stage 4.5 Knowledge Pack)
- Level 3: Safe Business-Type Default Evidence Plan
"""
from typing import Dict, Any, List, Tuple, Union, Optional
from app.schemas.market import CollectionPlan, CanonicalBusinessContext
from app.services.sarvam_llm_service import sarvam_llm_service, ALLOWED_STAGE5_TOOLS
from app.agents.market_intelligence.tools.tool_registry import market_tool_registry
from app.core.logging import logger


class DeterministicMarketRequirementPlanner:
    """
    Deterministic domain rules mapping business ontology and requirements
    to explicit data requirements and tool selections across all 15 rural business domains.
    """

    DEFAULT_ALL_TOOLS = [
        "location_intelligence_tool",
        "knowledge_hub_tool",
        "demographics_tool",
        "competitor_discovery_tool",
        "demand_evidence_tool",
        "supply_access_tool",
        "infrastructure_access_tool",
        "economic_purchasing_power_tool",
        "dataset_retrieval_tool",
        "demand_prediction_adapter"
    ]

    ENTERPRISE_REQUIREMENT_MAP = {
        "dairy_farm": [
            "milch_livestock_population",
            "per_capita_milk_consumption",
            "dairy_cooperative_chilling_gap",
            "cattle_feed_wholesale_access",
            "veterinary_dispensary_proximity",
            "all_weather_milk_transport_roads"
        ],
        "saree_retail": [
            "female_population_density",
            "festivals_wedding_seasonality",
            "direct_saree_competitors",
            "adjacent_garment_stores",
            "textile_wholesale_supply_hubs",
            "commercial_market_infrastructure",
            "household_purchasing_power_proxy"
        ],
        "rice_mill": [
            "catchment_paddy_cultivation_acreage",
            "marketable_paddy_surplus",
            "harvest_milling_seasonality",
            "apmc_mandi_proximity",
            "commercial_rice_mill_competitors",
            "3phase_electricity_reliability",
            "rural_road_freight_access"
        ],
        "kirana_grocery": [
            "catchment_household_density",
            "staple_food_expenditure_index",
            "local_kirana_competitors",
            "fmcg_wholesale_depots",
            "commercial_hub_proximity"
        ],
        "flour_mill": [
            "catchment_wheat_production_acreage",
            "daily_atta_consumption_demand",
            "local_atta_chakki_competitors",
            "commercial_electricity_reliability",
            "food_safety_compliance_access"
        ],
        "spice_grinding": [
            "raw_spice_market_access",
            "household_masala_consumption",
            "spice_processing_competitors",
            "commercial_power_availability",
            "packaging_material_sourcing"
        ],
        "oil_expeller": [
            "mustard_oilseed_acreage",
            "per_capita_cooking_oil_consumption",
            "oil_mill_competitors",
            "oilseed_mandi_proximity",
            "industrial_power_feeder"
        ],
        "bakery": [
            "catchment_youth_demographics",
            "daily_bakery_snack_consumption",
            "local_bakery_competitors",
            "bakery_raw_material_wholesalers",
            "commercial_market_footfall"
        ],
        "poultry_broiler": [
            "per_capita_meat_consumption",
            "day_old_chick_hatchery_access",
            "poultry_feed_distributors",
            "veterinary_support_proximity",
            "broiler_farm_competitors"
        ],
        "goat_farming": [
            "grazing_fodder_availability",
            "local_meat_market_demand",
            "livestock_haat_proximity",
            "veterinary_deworming_access",
            "goat_rearing_clusters"
        ],
        "garment_retail": [
            "working_age_population_density",
            "festival_clothing_demand",
            "readymade_garment_competitors",
            "apparel_wholesale_depots",
            "main_market_road_access"
        ],
        "two_wheeler_repair": [
            "registered_two_wheeler_density",
            "daily_commuter_traffic_volume",
            "spare_parts_wholesale_access",
            "auto_repair_competitors",
            "highway_road_frontage"
        ],
        "welding_fabrication": [
            "rural_housing_construction_growth",
            "agricultural_implement_repair_demand",
            "steel_iron_wholesale_dealers",
            "three_phase_power_supply",
            "fabrication_workshop_competitors"
        ],
        "beauty_parlour": [
            "female_working_age_demographics",
            "bridal_festive_grooming_demand",
            "cosmetics_wholesale_access",
            "beauty_parlour_competitors",
            "commercial_centre_location"
        ],
        "cold_storage": [
            "perishable_horticulture_production",
            "cold_chain_capacity_deficit",
            "apmc_mandi_connectivity",
            "dedicated_power_substation",
            "agro_cold_room_competitors"
        ]
    }

    def plan(
        self,
        business: Union[CanonicalBusinessContext, Dict[str, Any]],
        knowledge_pack: Dict[str, Any]
    ) -> CollectionPlan:
        if isinstance(business, CanonicalBusinessContext):
            business_id = business.business_id.lower().strip()
            business_name = business.business_name
        else:
            bus_sec = business.get("business_profile") or {}
            business_id = (
                business.get("business_id") or
                bus_sec.get("business_id") or
                bus_sec.get("specific_business") or
                "general"
            ).lower().replace(" ", "_")
            business_name = bus_sec.get("specific_business") or business.get("specific_business") or business_id

        # Match domain requirement profile
        matched_reqs = None
        for k, reqs in self.ENTERPRISE_REQUIREMENT_MAP.items():
            if k == business_id or (k in business_id and len(k) > 4) or (business_id in k and len(business_id) > 4):
                matched_reqs = reqs
                break

        if not matched_reqs:
            # Check knowledge pack
            if knowledge_pack and knowledge_pack.get("demand_drivers"):
                matched_reqs = [
                    f"demand_{d.lower().replace(' ', '_')}" for d in knowledge_pack.get("demand_drivers", [])
                ] + [
                    "competitor_density",
                    "wholesale_supply_proximity",
                    "commercial_infrastructure",
                    "household_purchasing_power_proxy"
                ]
            else:
                matched_reqs = [
                    "demographic_catchment_population",
                    "competitor_density",
                    "domain_demand_indicators",
                    "wholesale_supply_proximity",
                    "commercial_infrastructure",
                    "household_purchasing_power_proxy"
                ]

        logger.info(
            f"[PLANNER] BUSINESS ID: '{business_id}' | "
            f"BUSINESS NAME: '{business_name}' | "
            f"REQUIREMENTS GENERATED: {len(matched_reqs)} | "
            f"REQUIREMENTS SOURCE: Stage 4.5 Domain Knowledge & Benchmark Ontology"
        )

        return CollectionPlan(
            planner="deterministic",
            business_id=business_id,
            requirements=matched_reqs,
            selected_tools=list(self.DEFAULT_ALL_TOOLS),
            fallback_used=False,
            reasoning=f"Deterministic rule engine planned {len(matched_reqs)} domain data vectors across the complete Stage 5 tool ecosystem for {business_name}.",
            requirements_source="Stage 4.5 Domain Knowledge & Benchmark Ontology"
        )


class MarketRequirementPlanner:
    """
    Hybrid Requirement Planner orchestrating Sarvam LLM reasoning with deterministic fallback.
    """

    def __init__(self):
        self.llm_service = sarvam_llm_service
        self.deterministic_planner = DeterministicMarketRequirementPlanner()
        self.valid_tools = set(market_tool_registry.list_tool_names())
        self.last_telemetry: Dict[str, Any] = {}

    async def plan_collection(
        self,
        business: Union[CanonicalBusinessContext, Dict[str, Any]],
        knowledge_pack: Dict[str, Any],
        location_profile: Optional[Dict[str, Any]] = None,
        force_llm: bool = False
    ) -> Tuple[CollectionPlan, bool, bool]:
        """
        Plans tool selection and data requirements.
        Returns (CollectionPlan, llm_used, llm_fallback_used)
        """
        b_id = business.business_id if isinstance(business, CanonicalBusinessContext) else (
            (business.get("business_profile") or {}).get("business_id") or "general"
        )

        # Step 1: Attempt Sarvam LLM if configured or requested
        if (self.llm_service.is_available or force_llm) and not getattr(self, "_disable_llm", False):
            try:
                llm_res = await self.llm_service.plan_market_collection(business, knowledge_pack, location_profile=location_profile)
                self.last_telemetry = dict(self.llm_service.last_telemetry)

                if llm_res and llm_res.selected_tools:
                    sanitized_tools = [t for t in llm_res.selected_tools if t in self.valid_tools]
                    if "location_intelligence_tool" not in sanitized_tools:
                        sanitized_tools.insert(0, "location_intelligence_tool")
                    if "knowledge_hub_tool" not in sanitized_tools:
                        sanitized_tools.append("knowledge_hub_tool")
                    if "demographics_tool" not in sanitized_tools:
                        sanitized_tools.append("demographics_tool")
                    if "demand_evidence_tool" not in sanitized_tools:
                        sanitized_tools.append("demand_evidence_tool")

                    plan = CollectionPlan(
                        planner="llm",
                        business_id=b_id,
                        requirements=llm_res.requirements or ["catchment_population", "competitor_density"],
                        selected_tools=sanitized_tools,
                        fallback_used=False,
                        reasoning=llm_res.reasoning or "Sarvam LLM selected specialized tool suite based on enterprise ontology.",
                        requirements_source="Sarvam AI LLM (sarvam-105b)"
                    )
                    logger.info(f"[PLANNER] Successfully generated Sarvam LLM collection plan with {len(sanitized_tools)} tools for '{b_id}'.")
                    return plan, True, False
            except Exception as e:
                logger.warning(f"[PLANNER ERROR] Sarvam LLM planning failed ({e}). Falling back to deterministic planner.")

        # Step 2: Deterministic Domain Planner Fallback
        det_plan = self.deterministic_planner.plan(business, knowledge_pack)
        llm_was_attempted = bool(self.llm_service.is_available or force_llm)
        det_plan.fallback_used = llm_was_attempted

        if not self.last_telemetry:
            self.last_telemetry = dict(self.llm_service.last_telemetry) or {
                "sarvam_request_success": False,
                "sarvam_fallback_triggered": llm_was_attempted,
                "sarvam_fallback_reason": "DETERMINISTIC_ONLY" if not llm_was_attempted else "LLM_RETURNED_NONE",
                "execution_state": "DETERMINISTIC_ONLY" if not llm_was_attempted else "LLM_FALLBACK"
            }

        if llm_was_attempted:
            fb_reason = self.last_telemetry.get("sarvam_fallback_reason") or "LLM_RETURNED_NONE"
            logger.info(f"[PLANNER] sarvam_fallback_triggered=True sarvam_fallback_reason={fb_reason} | Using deterministic planner for '{b_id}'.")

        return det_plan, False, llm_was_attempted


market_requirement_planner = MarketRequirementPlanner()
