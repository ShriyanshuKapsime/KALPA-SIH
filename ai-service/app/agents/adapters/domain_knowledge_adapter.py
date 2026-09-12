"""
Domain Knowledge Agent Adapter:
Production-ready knowledge retrieval adapter connecting KALPA Manager Orchestrator
to the Stage 4.5 Knowledge Hub (KnowledgeService).
Retrieves verified financial benchmarks, market catchment norms, infrastructure requirements,
risk catalogs, and eligible government schemes.
"""
from typing import Dict, Any, List, Optional
from app.agents.adapters.base_adapter import BaseAgentAdapter
from app.services.classification.ontology_service import ontology_service
from app.services.classification.nic_service import nic_service
from app.knowledge.services.knowledge_service import get_knowledge_service
from app.schemas.knowledge import SchemeEligibilityQuery
from app.core.logging import logger


class DomainKnowledgeAdapter(BaseAgentAdapter):
    def __init__(self):
        super().__init__(
            agent_id="domain_knowledge_agent",
            name="Domain Knowledge & Benchmark Agent",
            description="Retrieves official NIC classifications, sector guidelines, MSME benchmarks, infrastructure requirements, and scheme rules from the Knowledge Hub.",
            capabilities=[
                "nic_hierarchy_retrieval",
                "sector_benchmarking",
                "risk_factor_identification",
                "infrastructure_specifications",
                "competitor_landscape_mapping",
                "required_dataset_identification",
                "scheme_eligibility_matching",
                "engine_knowledge_pack_generation"
            ],
            status="available",
            default_priority="HIGH",
            dependencies=[]  # Root agent; no upstream dependencies
        )
        self.knowledge_service = get_knowledge_service()

    async def execute(
        self,
        business_profile: Dict[str, Any],
        knowledge_context: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id.upper()}] Executing domain knowledge & benchmark retrieval via KnowledgeService")

        bus = business_profile.get("business_profile", {})
        specific_business = bus.get("specific_business") or bus.get("category", "")
        sector = bus.get("sector") or "General Enterprise"
        category = bus.get("category") or "General MSME"
        scale = bus.get("scale", "micro")
        nic = bus.get("nic", {})
        nic_code = nic.get("code") or ""
        nic_desc = nic.get("description") or ""

        # Check investment amount
        fin = business_profile.get("financial_profile", {})
        project_cost = fin.get("total_investment_inr") or fin.get("total_project_cost")
        available_margin = fin.get("available_equity_inr") or fin.get("promoter_contribution")

        # Map concept / NIC to a node_id
        ontology_node = ontology_service.get_node_by_concept(specific_business) or {}
        business_node_id = ontology_node.get("node_id") or specific_business.lower().replace(" ", "_")
        analysis_reqs = ontology_node.get("analysis_requirements", {})

        # Query Engine-ready packs
        market_pack = self.knowledge_service.get_market_context(
            business_id=business_node_id,
            location=business_profile.get("location_profile", {}).get("district")
        )
        financial_pack = self.knowledge_service.get_financial_context(
            business_id=business_node_id,
            project_cost=project_cost,
            available_margin=available_margin
        )
        comp_pack = self.knowledge_service.get_comprehensive_business_pack(
            business_node_id=business_node_id,
            project_cost=project_cost,
            available_margin=available_margin
        )

        fin_bench = comp_pack.layer3_financial_benchmarks.model_dump() if comp_pack.layer3_financial_benchmarks else None
        mkt_bench = comp_pack.layer3_market_benchmarks.model_dump() if comp_pack.layer3_market_benchmarks else None
        profile_data = comp_pack.layer2_domain_knowledge.model_dump() if comp_pack.layer2_domain_knowledge else None
        applicable_risks = self.knowledge_service.get_risks(business_node_id=business_node_id)
        inst_docs = comp_pack.layer4_institutional_evidence

        # Build MSME benchmarks output
        if fin_bench:
            capex = fin_bench.get("capex", {})
            margins = fin_bench.get("margins", {})
            timelines = fin_bench.get("timelines", {})
            wc = fin_bench.get("working_capital", {})
            benchmarks = {
                "typical_capital_range_inr": [capex.get("range_min", 100000), capex.get("range_max", 500000)],
                "typical_capital_inr": capex.get("typical", 200000),
                "typical_operating_margin_pct": [margins.get("net_margin_pct_min", 15.0), margins.get("net_margin_pct_max", 30.0)],
                "average_gestation_months": timelines.get("breakeven_months", 3),
                "payback_period_months": timelines.get("payback_period_months", 12),
                "working_capital_months_recommended": wc.get("working_capital_months_recommended", 2.0),
                "cost_structure_pct": fin_bench.get("cost_structure_pct", {}),
                "provenance": fin_bench.get("provenance", {}),
                "quality": fin_bench.get("quality", {}),
            }
        else:
            benchmarks = self._compute_fallback_benchmarks(sector, scale)

        # Build infrastructure specs
        if profile_data:
            infra_list = []
            if profile_data.get("space_and_infrastructure"):
                space = profile_data["space_and_infrastructure"]
                infra_list.append(f"Area: {space.get('built_up_area_sqft_recommended', 200)} sq.ft ({space.get('ventilation_type', 'Standard')})")
            if profile_data.get("power_and_utilities"):
                pwr = profile_data["power_and_utilities"]
                infra_list.append(f"Power: {pwr.get('power_load_hp', 5)} HP ({pwr.get('power_connection_type', 'Commercial')})")
            for mach in profile_data.get("core_machinery", []):
                infra_list.append(f"Machinery: {mach.get('item_name')} (~₹{mach.get('estimated_cost_inr', 0):,.0f})")
            infra_reqs = infra_list
            compliance_licenses = profile_data.get("compliance_and_licensing", [])
        else:
            infra_reqs = analysis_reqs.get(
                "infrastructure_requirements",
                ["Commercial space / shop front", "Power connection", "POS billing setup", "Basic inventory storage"]
            )
            compliance_licenses = []

        # Build risk list
        if applicable_risks:
            risk_context = [f"{r.risk_name} ({r.severity})" for r in applicable_risks]
        else:
            risk_context = analysis_reqs.get(
                "risk_factors",
                ["Market competition", "Working capital management", "Demand seasonality"]
            )

        # Build market & competitor landscape
        if mkt_bench:
            comp = mkt_bench.get("competition_and_saturation", {})
            competitor_landscape = {
                "direct": comp.get("direct_competitors", ["Local direct competitors"]),
                "adjacent": comp.get("indirect_competitors", ["Alternative service providers"]),
                "substitutes": ["Online / Regional alternatives"],
                "saturation_threshold": f"{comp.get('saturation_threshold_units_per_10k_pop', 2.0)} units / 10k pop",
                "seasonality_factors": mkt_bench.get("seasonality_factors", {}),
                "seasonality_notes": mkt_bench.get("seasonality_notes", "")
            }
        else:
            competitor_landscape = {
                "direct": analysis_reqs.get("direct_competitors", ["Local retail competitors"]),
                "adjacent": analysis_reqs.get("adjacent_competitors", ["Alternative service providers"]),
                "substitutes": analysis_reqs.get("substitute_businesses", ["Online marketplaces"])
            }

        # Build comprehensive knowledge context
        result = {
            "knowledge_status": "success",
            "agent": self.agent_id,
            "business_context": {
                "specific_business": specific_business,
                "sector": sector,
                "category": category,
                "nic_code": nic_code,
                "nic_description": nic_desc,
                "scale": scale,
                "business_node_id": business_node_id
            },
            "market_knowledge_pack": market_pack.model_dump(),
            "financial_knowledge_pack": financial_pack.model_dump(),
            "comprehensive_pack": comp_pack.model_dump(),
            "benchmarks": benchmarks,
            "infrastructure_requirements": infra_reqs,
            "compliance_licenses": compliance_licenses,
            "risk_context": risk_context,
            "detailed_risks": [r.model_dump() for r in applicable_risks],
            "competitor_landscape": competitor_landscape,
            "scheme_eligibility": comp_pack.layer1_rules_and_schemes,
            "institutional_references": [
                {"title": d.title, "institution": d.institution, "url": d.document_url}
                for d in inst_docs
            ],
            "required_datasets": analysis_reqs.get(
                "required_datasets",
                ["AGMARKNET_DAILY_MANDI", "DISTRICT_CENSUS_2011_SOCIOECONOMIC", "ROAD_CONNECTIVITY_PMGSY"]
            ),
            "recommended_analysis": [
                "market_intelligence_agent",
                "opportunity_evaluation_engine",
                "finance_engine",
                "feasibility_engine"
            ]
        }
        return result

    def _compute_fallback_benchmarks(self, sector: str, scale: str) -> Dict[str, Any]:
        """Fallback when exact business node is not in curated repository."""
        sector_lower = sector.lower()
        if "manufacturing" in sector_lower or "processing" in sector_lower:
            return {
                "typical_capital_range_inr": [300000, 1500000],
                "typical_capital_inr": 600000,
                "typical_operating_margin_pct": [18.0, 28.0],
                "average_gestation_months": 4,
                "payback_period_months": 18,
                "turnover_to_capital_ratio": 2.2,
                "power_requirement_kwh": "3-Phase Commercial (10-25 HP)",
                "recommended_inventory_days": 30
            }
        elif "retail" in sector_lower or "trade" in sector_lower:
            return {
                "typical_capital_range_inr": [150000, 800000],
                "typical_capital_inr": 350000,
                "typical_operating_margin_pct": [15.0, 24.0],
                "average_gestation_months": 2,
                "payback_period_months": 10,
                "turnover_to_capital_ratio": 3.0,
                "power_requirement_kwh": "Single-Phase Commercial (2-5 kW)",
                "recommended_inventory_days": 45
            }
        elif "agriculture" in sector_lower or "dairy" in sector_lower or "poultry" in sector_lower:
            return {
                "typical_capital_range_inr": [200000, 1000000],
                "typical_capital_inr": 450000,
                "typical_operating_margin_pct": [20.0, 32.0],
                "average_gestation_months": 3,
                "payback_period_months": 14,
                "turnover_to_capital_ratio": 1.8,
                "power_requirement_kwh": "Agricultural / Rural Commercial (5-10 HP)",
                "recommended_inventory_days": 15
            }
        else:
            return {
                "typical_capital_range_inr": [100000, 500000],
                "typical_capital_inr": 250000,
                "typical_operating_margin_pct": [25.0, 40.0],
                "average_gestation_months": 1,
                "payback_period_months": 8,
                "turnover_to_capital_ratio": 3.5,
                "power_requirement_kwh": "Single-Phase (1-3 kW)",
                "recommended_inventory_days": 10
            }
