"""
Comprehensive Integration Test Suite for Stage 6: Market Intelligence Engine.
Tests deterministic analysis, real Poultry Farm Stage 5 data ingestion,
benchmark comparisons, geospatial/competition/demand/supply/seasonality/capacity logic,
missing infrastructure data-gap handling, Stage 7 feature vector building,
and orchestrator integration.
"""
import pytest
import json
import os
from app.services.market_intelligence_engine import (
    Stage5Input,
    Stage6Output,
    MarketIntelligenceEngine,
    market_intelligence_engine,
    benchmark_service
)
from app.services.market_intelligence_engine.schemas import (
    CompetitivePressureLevel,
    MarketCapacityStatus,
    DemandSignalStrength,
    InfrastructureReadiness,
    SupplyRiskLevel,
    DataStatus
)
from app.agents.registry import agent_registry
from app.services.orchestration.hybrid_planner import hybrid_planner


# -----------------------------------------------------------------------------
# Test Fixtures: Real Poultry Farm Stage 5 Output
# -----------------------------------------------------------------------------

@pytest.fixture
def poultry_farm_stage5_payload():
    """
    Real Stage 5 output for Commercial Poultry Farm in Bangalore South, Bengaluru Urban, Karnataka.
    Matches the exact runtime production format.
    """
    return {
        "analysis_id": "99a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
        "session_id": "11a2b3c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c",
        "workflow": {
            "stage": 5,
            "state": "MARKET_EVIDENCE_COLLECTED",
            "status": "complete"
        },
        "business_context": {
            "business_id": "poultry_farm",
            "specific_business": "Poultry Farm",
            "sector": "Agriculture & Allied",
            "category": "Poultry Farming",
            "nic_code": "01461",
            "nic_name": "Raising of poultry for meat and egg production"
        },
        "location_context": {
            "resolved_location": {
                "village": "Bangarappa Nagara",
                "block": "Bangalore South",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "country": "India",
                "pincode": "560098"
            },
            "coordinates": {
                "latitude": 12.898576,
                "longitude": 77.51907,
                "accuracy": 15
            },
            "geographic_precision": "village",
            "resolution_confidence": 0.95
        },
        "collection_plan": {
            "planner": "deterministic",
            "requirements": [
                "poultry_feed_availability",
                "catchment_population",
                "day_old_chick_suppliers",
                "commercial_poultry_competitors",
                "seasonality_multipliers"
            ]
        },
        "market_evidence": {
            "demographics": [
                {
                    "metric": "total_population",
                    "value": 9621551,
                    "unit": "persons",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "geographic_precision": "district",
                    "proxy": True,
                    "proxy_reason": "District level PCA aggregate scaled to local catchment",
                    "source": {
                        "source_id": "SRC-CENSUS-001",
                        "organization": "Census of India",
                        "source_type": "OFFICIAL_DATASET",
                        "dataset_name": "Primary Census Abstract 2011"
                    }
                },
                {
                    "metric": "total_households",
                    "value": 2393845,
                    "unit": "households",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "geographic_precision": "district",
                    "proxy": True,
                    "source": {"source_id": "SRC-CENSUS-001", "organization": "Census of India"}
                },
                {
                    "metric": "female_population",
                    "value": 4556488,
                    "unit": "persons",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "source": {"source_id": "SRC-CENSUS-001"}
                },
                {
                    "metric": "sex_ratio",
                    "value": 916,
                    "unit": "females_per_1000_males",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "source": {"source_id": "SRC-CENSUS-001"}
                },
                {
                    "metric": "rural_percentage",
                    "value": 9.36,
                    "unit": "percent",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "source": {"source_id": "SRC-CENSUS-001"}
                },
                {
                    "metric": "population_density",
                    "value": 4381,
                    "unit": "persons_per_sq_km",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "source": {"source_id": "SRC-CENSUS-001"}
                }
            ],
            "competitors": {
                "direct": [
                    {
                        "competitor_type": "direct",
                        "business_name": "Integrated broiler integrators (Suguna / IB Group Cluster)",
                        "category": "Poultry Farm",
                        "distance_km": 6.5,
                        "location": {"district": "Bengaluru Urban", "state": "Karnataka"},
                        "source": {"source_id": "SRC-UDYAM-002", "organization": "MSME UDYAM Portal"},
                        "confidence": 0.85
                    },
                    {
                        "competitor_type": "direct",
                        "business_name": "Independent poultry farmers (Kengeri Cluster #1)",
                        "category": "Poultry Farm",
                        "distance_km": 3.8,
                        "location": {"district": "Bengaluru Urban", "state": "Karnataka"},
                        "source": {"source_id": "SRC-UDYAM-002", "organization": "MSME UDYAM Portal"},
                        "confidence": 0.85
                    }
                ],
                "adjacent": [
                    {
                        "competitor_type": "adjacent",
                        "business_name": "Country chicken (desi murga) breeders",
                        "category": "Poultry Breeding",
                        "distance_km": 4.2,
                        "location": {"district": "Bengaluru Urban", "state": "Karnataka"},
                        "source": {"source_id": "SRC-UDYAM-002"}
                    },
                    {
                        "competitor_type": "adjacent",
                        "business_name": "Fish and mutton vendors cluster",
                        "category": "Meat Retail",
                        "distance_km": 2.1,
                        "location": {"district": "Bengaluru Urban", "state": "Karnataka"},
                        "source": {"source_id": "SRC-UDYAM-002"}
                    }
                ],
                "substitutes": [
                    {
                        "competitor_type": "substitute",
                        "business_name": "Weekly Haat / Periodic Meat Bazaar",
                        "category": "Substitute Channel",
                        "distance_km": 3.0,
                        "source": {"source_id": "SRC-UDYAM-002"}
                    },
                    {
                        "competitor_type": "substitute",
                        "business_name": "E-commerce Quick-Commerce Delivery Points (Licious/FreshToHome)",
                        "category": "Substitute Channel",
                        "distance_km": 5.0,
                        "source": {"source_id": "SRC-UDYAM-002"}
                    }
                ]
            },
            "demand_indicators": [
                {
                    "indicator_name": "Catchment Consumption Demand Proxy",
                    "category": "consumption_demand",
                    "value": 4850,
                    "unit": "INR_monthly_per_household_protein_proxy",
                    "business_relevance": "Household animal protein and poultry meat expenditure proxy in urban/peri-urban catchment.",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "proxy": True,
                    "source": {"source_id": "SRC-NSSO-003", "organization": "NSSO Household Consumer Survey"}
                },
                {
                    "indicator_name": "Regional Seasonality Multiplier",
                    "category": "seasonality_demand",
                    "value": 1.25,
                    "unit": "multiplier",
                    "business_relevance": "Winter demand surge factor for live broiler chicken.",
                    "geography": {"district": "Bengaluru Urban", "state": "Karnataka"},
                    "source": {"source_id": "SRC-NABARD-004", "organization": "NABARD Model Bankable Project"}
                }
            ],
            "supply_access": [
                {
                    "hub_name": "Yeshwanthpur Wholesale APMC Yard",
                    "hub_type": "apmc_mandi",
                    "distance_km": 14.2,
                    "commodities_available": ["Commercial Poultry Feed (Maize/Soya)", "Veterinary Medicine", "Vaccines"],
                    "accessibility_rating": "high",
                    "source": {"source_id": "SRC-AGMARKNET-005", "organization": "AGMARKNET"}
                },
                {
                    "hub_name": "Regional Hatchery DOC Sourcing Center (Kanakapura Road)",
                    "hub_type": "hatchery",
                    "distance_km": 18.5,
                    "commodities_available": ["Day-Old Chicks (DOC Cob-500)", "Layer Pullets"],
                    "accessibility_rating": "high",
                    "source": {"source_id": "SRC-AGMARKNET-005", "organization": "AGMARKNET"}
                }
            ],
            "infrastructure": [],  # Real case: Empty infrastructure evidence array!
            "seasonality_evidence": [
                {"month": "jan", "multiplier": 1.25},
                {"month": "feb", "multiplier": 1.15},
                {"month": "mar", "multiplier": 1.05},
                {"month": "apr", "multiplier": 0.95},
                {"month": "may", "multiplier": 0.85},
                {"month": "jun", "multiplier": 0.85},
                {"month": "jul", "multiplier": 0.75},
                {"month": "aug", "multiplier": 0.80},
                {"month": "sep", "multiplier": 0.90},
                {"month": "oct", "multiplier": 1.10},
                {"month": "nov", "multiplier": 1.20},
                {"month": "dec", "multiplier": 1.30}
            ]
        },
        "evidence_quality": {
            "overall_score": 0.82,
            "completeness": 0.85,
            "source_quality": 0.90
        }
    }


# ============================================================================
# TESTS
# ============================================================================

def test_stage6_accepts_stage5_output_and_executes_deterministically(poultry_farm_stage5_payload):
    """
    Test 1: Stage 5 output is directly accepted and processed with zero LLM dependency.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)

    assert isinstance(output, Stage6Output)
    assert output.analysis_id == "99a1b2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c"
    assert output.session_id == "11a2b3c4-5d6e-7f8a-9b0c-1d2e3f4a5b6c"
    assert output.workflow.stage == 6
    assert output.workflow.state == "MARKET_INTELLIGENCE_ANALYZED"
    assert output.execution_metadata.llm_used is False
    assert output.execution_metadata.engine == "deterministic_market_intelligence_engine"


def test_stage6_demographics_processing_and_benchmarks(poultry_farm_stage5_payload):
    """
    Test 2: Demographics are cleaned, units normalized, and compared against minimum catchment population benchmarks.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)

    demo_features = output.market_features.demographic_features
    assert demo_features["total_population"] == 9621551
    assert demo_features["total_households"] == 2393845
    assert demo_features["population_density"] == 4381
    assert demo_features["rural_percentage"] == 9.36

    # Verify Benchmark Comparison
    comparisons = output.benchmark_analysis.comparisons
    pop_cmp = next((c for c in comparisons if c.benchmark_id == "BM-DEMO-001"), None)
    assert pop_cmp is not None
    assert pop_cmp.comparison_result == "FAVORABLE_EXCEEDS_BENCHMARK"
    assert pop_cmp.actual_value == 9621551
    assert pop_cmp.benchmark_value == 25000  # NABARD poultry catchment minimum


def test_stage6_competition_multi_tier_weighted_pressure(poultry_farm_stage5_payload):
    """
    Test 3: Competitors are segregated into Direct, Adjacent, and Substitute tiers
    with proximity decay, cluster detection, and driver explanations.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    comp = output.market_indicators.competition

    assert comp.direct.count == 2
    assert comp.adjacent.count == 2
    assert comp.substitute.count == 2
    assert comp.total_competitors == 6

    # Proximity decay weights: items <= 15km have full decay 1.0
    assert comp.direct.proximity_weighted_count == 2.0

    # Saturation threshold for poultry = 1.2 per 10k
    assert comp.saturation_threshold == 1.2
    assert comp.competitive_pressure in [CompetitivePressureLevel.LOW, CompetitivePressureLevel.MODERATE]
    assert len(comp.drivers) >= 2
    assert any("Direct" in d for d in comp.drivers)


def test_stage6_demand_evidence_synthesis(poultry_farm_stage5_payload):
    """
    Test 4: Demand evidence (consumption proxies and population scale) is synthesized deterministically.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    demand = output.market_indicators.demand_evidence

    assert demand.demand_signal_strength in [DemandSignalStrength.STRONG, DemandSignalStrength.MODERATE]
    assert demand.demand_signal_score >= 0.50
    assert len(demand.consumption_signals) >= 1
    assert demand.consumption_signals[0]["value"] == 4850
    assert demand.consumption_proxy["raw_value"] == 4850
    assert demand.consumption_proxy["normalized_score"] > 0.60


def test_stage6_missing_infrastructure_maps_to_data_gap(poultry_farm_stage5_payload):
    """
    Test 5: Empty infrastructure array `infrastructure: []` MUST map to UNKNOWN_DATA_GAP
    with low confidence (<=0.35) and explicit critical gaps, never assuming UNAVAILABLE or zero.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    infra = output.market_indicators.infrastructure

    assert infra.readiness == InfrastructureReadiness.UNKNOWN_DATA_GAP
    assert infra.readiness_score in (0.0, 0.50)
    assert infra.confidence <= 0.35
    assert len(infra.critical_gaps) >= 3

    # Verify workflow status reflects gaps honestly
    assert output.workflow.status == "complete_with_gaps"
    assert any(gap.category == "INFRASTRUCTURE" for gap in output.evidence_gaps)


def test_stage6_supply_ecosystem_and_critical_input_coverage(poultry_farm_stage5_payload):
    """
    Test 6: Supply hubs are evaluated for distance suitability and critical input coverage (Feed, Chicks, Vaccines).
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    supply = output.market_indicators.supply_ecosystem

    assert supply.hub_count == 2
    assert supply.nearest_hub_distance_km == 14.2  # Yeshwanthpur APMC
    assert supply.distance_assessment == "IDEAL_PROXIMITY"
    assert supply.accessibility == "HIGH"
    assert supply.supply_risk == SupplyRiskLevel.LOW

    coverage = supply.critical_input_coverage
    assert len(coverage["covered"]) >= 1


def test_stage6_seasonality_analysis_volatility_and_risk(poultry_farm_stage5_payload):
    """
    Test 7: 12-month seasonality factors produce accurate peak/lean months, volatility index, and risk rating.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    sea = output.market_indicators.seasonality

    assert "dec" in sea.peak_months
    assert "jan" in sea.peak_months
    assert "jul" in sea.lean_months
    assert sea.peak_multiplier == 1.30
    assert sea.lean_multiplier == 0.75
    assert sea.annual_volatility > 0.10
    assert sea.annual_volatility < 0.30
    assert sea.seasonal_risk.value in ["LOW", "MODERATE"]


def test_stage6_market_capacity_signal_synthesis(poultry_farm_stage5_payload):
    """
    Test 8: Market capacity combines demand, competition, and supply into a net capacity signal.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    cap = output.market_indicators.market_capacity

    assert cap.status in [MarketCapacityStatus.AVAILABLE, MarketCapacityStatus.LIMITED]
    assert cap.net_capacity_score > 0.0
    assert cap.capacity_signal in ["HIGH_EXPANSION_CAPACITY", "MODERATE_PRESSURE"]
    assert cap.confidence >= 0.70


def test_stage6_market_features_contract_for_stage7(poultry_farm_stage5_payload):
    """
    Test 9: Standardized 10-tier `market_features` contract for Stage 7 ML Demand Prediction is fully populated.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    features = output.market_features

    assert features.business_features["business_id"] == "poultry_farm"
    assert features.business_features["nic_code"] == "01461"
    assert features.location_features["latitude"] == 12.898576
    assert features.location_features["longitude"] == 77.51907
    assert features.demographic_features["total_population"] == 9621551
    assert features.economic_features["consumption_proxy_raw"] == 4850
    assert features.competition_features["direct_competitor_count"] == 2
    assert features.supply_features["nearest_hub_distance_km"] == 14.2
    assert features.infrastructure_features["infrastructure_readiness"] == "UNKNOWN_DATA_GAP"
    assert features.seasonal_features["peak_multiplier"] == 1.30
    assert features.demand_evidence_features["demand_signal_strength"] in ["STRONG", "MODERATE"]

    # Verify Stage 7 Contract declaration
    assert output.next_stage.stage == 7
    assert output.next_stage.component == "DEMAND_PREDICTION_ML_MODEL"
    assert output.next_stage.input_contract == "market_features"


def test_stage6_calculation_provenance_and_transparency(poultry_farm_stage5_payload):
    """
    Test 10: Calculation provenance traces formulas, inputs, assumptions, and datasets used.
    """
    output = market_intelligence_engine.analyze(poultry_farm_stage5_payload)
    provenance = output.calculation_provenance

    assert len(provenance) >= 3
    comp_prov = next((p for p in provenance if p.indicator == "competitive_pressure"), None)
    assert comp_prov is not None
    assert "formula" in comp_prov.model_dump()
    assert "weighted_proximity_decay_density" in comp_prov.calculation_method
    assert len(comp_prov.benchmarks_used) > 0


def test_stage6_edge_cases():
    """
    Test 11: Edge cases - Empty payload, minimal context, invalid coordinates, missing demand indicators.
    """
    minimal_payload = {
        "analysis_id": "minimal-test-001",
        "session_id": "minimal-session-001",
        "business_context": {"specific_business": "Rice Mill"},
        "location_context": {
            "coordinates": {"latitude": "invalid_lat", "longitude": "invalid_lon"},
            "resolved_location": {"district": "Varanasi", "state": "Uttar Pradesh"}
        },
        "market_evidence": {
            "demographics": [],
            "competitors": {"direct": [], "adjacent": [], "substitute": []},
            "demand_indicators": [],
            "supply_access": [],
            "infrastructure": []
        }
    }

    output = market_intelligence_engine.analyze(minimal_payload)
    assert isinstance(output, Stage6Output)
    assert output.analysis_id == "minimal-test-001"
    assert output.market_indicators.competition.total_competitors == 0
    assert output.market_indicators.geospatial_analysis.coordinates == {}
    assert output.market_indicators.infrastructure.readiness == InfrastructureReadiness.UNKNOWN_DATA_GAP


def test_stage6_orchestrator_agent_registry_and_dag_plan():
    """
    Test 12: Verifies MarketIntelligenceEngineAdapter is registered in AgentRegistry
    and correctly inserted as Step 3 in Orchestrator DAG plan.
    """
    # 1. Agent Registry Lookup
    adapter = agent_registry.get_agent("market_intelligence_engine")
    assert adapter is not None
    assert adapter.agent_id == "market_intelligence_engine"
    assert "market_intelligence_agent" in adapter.dependencies

    # 2. Hybrid Planner DAG Schedule
    dummy_profile = {
        "business_profile": {"specific_business": "Poultry Farm", "sector": "Agriculture & Allied"},
        "location_profile": {"district": "Bengaluru Urban", "state": "Karnataka"},
        "data_quality": {"profile_complete": True}
    }
    plan = hybrid_planner.generate_deterministic_plan(dummy_profile)
    agent_names = [step["agent"] for step in plan]

    assert "domain_knowledge_agent" in agent_names
    assert "market_intelligence_agent" in agent_names
    assert "market_intelligence_engine" in agent_names
    assert "opportunity_evaluation_engine" in agent_names

    # Verify sequence: market_intelligence_agent -> market_intelligence_engine -> opportunity_evaluation_engine
    agent_idx = agent_names.index("market_intelligence_agent")
    engine_idx = agent_names.index("market_intelligence_engine")
    opp_idx = agent_names.index("opportunity_evaluation_engine")

    assert engine_idx == agent_idx + 1
    assert opp_idx == engine_idx + 1
