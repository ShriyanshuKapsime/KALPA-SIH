import pytest
import asyncio
from app.schemas.market import (
    CanonicalBusinessContext,
    MarketExecutionContext,
    LocationContext,
    CollectionPlan,
    EvidenceDataStatus,
    MarketEvidenceAggregate,
    DemographicEvidenceItem,
    CompetitorEvidenceItem,
    CompetitorEvidenceContainer,
    DemandIndicatorItem,
    SupplyAccessItem,
    InfrastructureItem,
    EconomicIndicatorItem,
    CollectMarketEvidenceRequest,
)
from app.agents.market_intelligence.context_normalizer import BusinessContextNormalizer
from app.agents.market_intelligence.integrity_gate import ContextIntegrityGate, DOMAIN_FORBIDDEN_KEYWORDS
from app.agents.market_intelligence.execution.caching import MarketEvidenceCache
from app.agents.market_intelligence.planner import DeterministicMarketRequirementPlanner
from app.agents.market_intelligence.scoring import EvidenceQualityScorer, evidence_quality_scorer
from app.agents.market_intelligence.market_agent import MarketIntelligenceAgent
from app.agents.market_intelligence.tools.competitor_tool import CompetitorDiscoveryTool
from app.agents.market_intelligence.tools.demographics_tool import DemographicsTool
from app.agents.market_intelligence.tools.demand_prediction_adapter import DemandPredictionAdapter
from app.agents.market_intelligence.tools.base_tool import ToolExecutionContext


# ============================================================================
# 1. CONTEXT NORMALIZATION & RECOGNITION TESTS
# ============================================================================

def test_context_normalizer_dairy_farm():
    raw_bp = {
        "specific_business": "Commercial Dairy Farm (10-Cow Unit)",
        "normalized_concept": "dairy farm",
        "sector": "Animal Husbandry",
        "category": "Dairy Farming",
        "nic": {"code": "01411"}
    }
    canonical = BusinessContextNormalizer.normalize(raw_bp)
    assert canonical.business_id == "dairy_farm"
    assert "Animal Husbandry" in canonical.sector
    assert "dairy" in canonical.normalized_concept.lower() or "dairy" in canonical.business_name.lower()
    assert "dairy_farm" in DOMAIN_FORBIDDEN_KEYWORDS
    assert "saree" in DOMAIN_FORBIDDEN_KEYWORDS["dairy_farm"]
    assert "textile" in DOMAIN_FORBIDDEN_KEYWORDS["dairy_farm"]


def test_context_normalizer_saree_retail():
    raw_bp = {
        "specific_business": "Saree & Traditional Apparel Retail",
        "normalized_concept": "saree retail",
        "sector": "Retail Trade",
        "category": "Saree Retail",
        "nic": {"code": "47711"}
    }
    canonical = BusinessContextNormalizer.normalize(raw_bp)
    assert canonical.business_id == "saree_retail"
    assert "Retail" in canonical.sector
    assert "saree" in canonical.normalized_concept.lower() or "saree" in canonical.business_name.lower()
    assert "saree_retail" in DOMAIN_FORBIDDEN_KEYWORDS
    assert "milk" in DOMAIN_FORBIDDEN_KEYWORDS["saree_retail"]
    assert "cattle" in DOMAIN_FORBIDDEN_KEYWORDS["saree_retail"]


# ============================================================================
# 2. CACHE ISOLATION & DETERMINISTIC FINGERPRINTING TESTS
# ============================================================================

def test_cache_key_isolation_across_businesses():
    cache = MarketEvidenceCache()
    
    loc_chatra = LocationContext(
        resolved_location={"district": "Chatra", "state": "Jharkhand"},
        geographic_precision="district"
    )

    saree_canon = BusinessContextNormalizer.normalize({"specific_business": "Saree Retail"})
    dairy_canon = BusinessContextNormalizer.normalize({"specific_business": "Dairy Farm"})

    saree_ctx = MarketExecutionContext(
        analysis_id="test_saree_analysis",
        session_id="test_session_1",
        business=saree_canon,
        location=loc_chatra,
        requirements=["direct_competitors"]
    )

    dairy_ctx = MarketExecutionContext(
        analysis_id="test_dairy_analysis",
        session_id="test_session_2",
        business=dairy_canon,
        location=loc_chatra,
        requirements=["direct_competitors"]
    )

    key_saree = cache.build_cache_key("competitor_discovery_tool", saree_ctx)
    key_dairy = cache.build_cache_key("competitor_discovery_tool", dairy_ctx)

    assert key_saree != key_dairy, "Saree Retail and Dairy Farm must produce distinct cache keys!"
    assert len(key_saree) == 64
    assert len(key_dairy) == 64


def test_cache_key_isolation_across_locations():
    cache = MarketEvidenceCache()
    dairy_canon = BusinessContextNormalizer.normalize({"specific_business": "Dairy Farm"})

    dairy_chatra = MarketExecutionContext(
        analysis_id="test_chatra",
        session_id="test_session_1",
        business=dairy_canon,
        location=LocationContext(
            resolved_location={"district": "Chatra", "state": "Jharkhand"},
            geographic_precision="district"
        ),
        requirements=[]
    )

    dairy_solapur = MarketExecutionContext(
        analysis_id="test_solapur",
        session_id="test_session_2",
        business=dairy_canon,
        location=LocationContext(
            resolved_location={"district": "Solapur", "state": "Maharashtra"},
            geographic_precision="district"
        ),
        requirements=[]
    )

    key_chatra = cache.build_cache_key("demographics_tool", dairy_chatra)
    key_solapur = cache.build_cache_key("demographics_tool", dairy_solapur)

    assert key_chatra != key_solapur, "Chatra and Solapur must produce distinct cache keys!"


def test_cache_force_refresh():
    cache = MarketEvidenceCache()
    dairy_canon = BusinessContextNormalizer.normalize({"specific_business": "Dairy Farm"})
    ctx_normal = MarketExecutionContext(
        analysis_id="test_refresh",
        session_id="test_session",
        business=dairy_canon,
        location=LocationContext(resolved_location={"district": "Chatra"}),
        force_refresh=False
    )
    cache.set("test_tool", ctx_normal, {"dummy": "data"})
    assert cache.get("test_tool", ctx_normal) == {"dummy": "data"}

    # With force_refresh=True, get must return None
    ctx_refresh = MarketExecutionContext(
        analysis_id="test_refresh",
        session_id="test_session",
        business=dairy_canon,
        location=LocationContext(resolved_location={"district": "Chatra"}),
        force_refresh=True
    )
    assert cache.get("test_tool", ctx_refresh) is None


# ============================================================================
# 3. COMPETITOR TOOL: EMPTY COMPETITORS IS NOT A FAILURE
# ============================================================================

@pytest.mark.asyncio
async def test_competitor_discovery_empty_is_success():
    tool = CompetitorDiscoveryTool()
    tool_ctx = ToolExecutionContext(
        business_id="poultry_farm",
        raw_business_profile={"specific_business": "Poultry Farm"},
        canonical_business=BusinessContextNormalizer.normalize({"specific_business": "Poultry Farm"}),
        location_context={"resolved_location": {"district": "UnknownRemoteDistrict", "state": "Jharkhand"}},
        analysis_requirements={}
    )
    result = await tool.execute(tool_ctx)
    assert result.status == "success", "Empty competitor discovery must be treated as successful discovery without crash"
    assert "direct_competitors" in result.data
    assert isinstance(result.data["direct_competitors"], list)


# ============================================================================
# 4. TRUTHFUL GEOGRAPHIC PRECISION & DEMOGRAPHICS TEST
# ============================================================================

@pytest.mark.asyncio
async def test_demographics_truthful_precision():
    tool = DemographicsTool()
    tool_ctx = ToolExecutionContext(
        business_id="dairy_farm",
        raw_business_profile={"specific_business": "Dairy Farm"},
        canonical_business=BusinessContextNormalizer.normalize({"specific_business": "Dairy Farm"}),
        location_context={
            "resolved_location": {"village": "Karma", "district": "Chatra", "state": "Jharkhand"},
            "target_geographic_precision": "village"
        },
        analysis_requirements={}
    )
    result = await tool.execute(tool_ctx)
    assert result.status == "success"
    demographics = result.metrics or []
    assert len(demographics) > 0
    for d in demographics:
        # Census 2011 stats are district-level
        assert d["data_geographic_precision"] == "district"
        assert d["target_geographic_precision"] == "village"


# ============================================================================
# 5. DEMAND PREDICTION ML ADAPTER: HONEST DIAGNOSTIC
# ============================================================================

@pytest.mark.asyncio
async def test_demand_prediction_adapter_honest_unavailability():
    tool = DemandPredictionAdapter()
    tool_ctx = ToolExecutionContext(
        business_id="dairy_farm",
        raw_business_profile={"specific_business": "Dairy Farm"},
        canonical_business=BusinessContextNormalizer.normalize({"specific_business": "Dairy Farm"}),
        location_context={"resolved_location": {"district": "Chatra", "state": "Jharkhand"}},
        analysis_requirements={}
    )
    result = await tool.execute(tool_ctx)
    pred = result.data["demand_prediction"]
    assert pred["available"] is False
    assert pred["data_status"] == EvidenceDataStatus.UNAVAILABLE.value
    assert pred["status"] == "model_not_connected"


# ============================================================================
# 6. INTEGRITY GATE & CONTAMINATION HARD PENALTY
# ============================================================================

def test_semantic_contamination_detection():
    gate = ContextIntegrityGate()
    
    # Clean dairy plan
    clean_plan = CollectionPlan(
        business_id="dairy_farm",
        planner="deterministic",
        selected_tools=[],
        requirements=["Daily milk procurement volume", "Chilling plant logistics", "Cattle feed availability"]
    )
    passed_clean, _ = gate.check_semantic_contamination("dairy_farm", clean_plan)
    assert passed_clean is True

    # Contaminated dairy plan containing Saree terms
    dirty_plan = CollectionPlan(
        business_id="dairy_farm",
        planner="deterministic",
        selected_tools=[],
        requirements=["Bridal saree retail demand", "Silk cloth merchant access"]
    )
    passed_dirty, err_dict = gate.check_semantic_contamination("dairy_farm", dirty_plan)
    assert passed_dirty is False
    assert "Semantic contamination" in err_dict["error"]


def test_evidence_quality_scoring_penalty():
    scorer = EvidenceQualityScorer()

    clean_evidence = MarketEvidenceAggregate(
        demographics=[DemographicEvidenceItem(metric="total_population", value=100000, unit="persons", geographic_precision="district", source={"organization": "Census 2011"}, data_status="OFFICIAL_STATIC_DATA")],
        competitors=CompetitorEvidenceContainer(direct=[CompetitorEvidenceItem(business_name="Local Dairy Unit", category="Dairy", distance_km=2.0, source={"organization": "MSME"}, data_status="LIVE_RETRIEVED")]),
        demand_indicators=[DemandIndicatorItem(indicator_name="Daily Milk Consumption", category="Demand", value=5000, unit="litres/day", geographic_precision="district", source={"organization": "NDDB"}, data_status="OFFICIAL_STATIC_DATA")],
        supply_access=[SupplyAccessItem(hub_name="District Feed Mandi", hub_type="feed_market", distance_km=8.0, commodities_available=["Cattle Feed"], source={"organization": "APMC"}, data_status="LIVE_RETRIEVED")],
        infrastructure=[InfrastructureItem(name="3-Phase Feeder", infrastructure_type="power", distance_km=1.0, reliability_hours_daily=20.0, status="operational", source={"organization": "State Electricity Board"}, data_status="OFFICIAL_STATIC_DATA")],
        economic_indicators=[EconomicIndicatorItem(indicator_type="per_capita_income", value=75000, unit="INR/year", geographic_precision="district", source={"organization": "RBI"}, data_status="PROXY")]
    )

    clean_loc = LocationContext(
        resolved_location={"district": "Chatra", "state": "Jharkhand"},
        geographic_precision="district"
    )

    clean_plan = CollectionPlan(
        business_id="dairy_farm",
        planner="deterministic",
        selected_tools=["location_intelligence_tool", "demographics_tool", "competitor_discovery_tool", "demand_evidence_tool", "supply_access_tool", "infrastructure_access_tool", "economic_purchasing_power_tool"],
        requirements=[]
    )

    # Score clean evidence
    clean_score = scorer.evaluate(
        evidence=clean_evidence,
        location=clean_loc,
        plan=clean_plan,
        successful_tools=clean_plan.selected_tools,
        failed_tools=[],
        context_integrity_passed=True,
        contamination_detected=False
    )
    assert clean_score.overall_quality >= 0.70
    assert clean_score.confidence_level in ["high", "moderate"]

    # Score contaminated evidence with context mismatch
    mismatch_score = scorer.evaluate(
        evidence=clean_evidence,
        location=clean_loc,
        plan=clean_plan,
        successful_tools=clean_plan.selected_tools,
        failed_tools=[],
        context_integrity_passed=False,
        contamination_detected=True
    )
    assert mismatch_score.overall_quality <= 0.20, "Contaminated evidence must be penalized to <= 0.20"
    assert mismatch_score.confidence_level == "untrustworthy"


# ============================================================================
# 7. ACCEPTANCE SEQUENCE (4 STEPS: SAREE -> DAIRY -> DAIRY SOLAPUR -> SAREE)
# ============================================================================

@pytest.mark.asyncio
async def test_full_acceptance_sequence():
    agent = MarketIntelligenceAgent()

    # Step 1: Saree Retail (Chatra)
    saree_req = {
        "business_profile": {
            "business_profile": {
                "specific_business": "Saree & Traditional Apparel Retail",
                "normalized_concept": "saree retail",
                "sector": "Retail Trade",
                "category": "Apparel Retail",
                "nic": {"code": "47711"}
            },
            "location_profile": {
                "village": "Chatra",
                "district": "Chatra",
                "state": "Jharkhand",
                "coordinates": {"latitude": 24.2089, "longitude": 84.8717}
            }
        },
        "force_refresh": True
    }
    res1 = await agent.run(saree_req)
    assert res1.business_context.business_id == "saree_retail"
    assert res1.evidence_quality.overall_quality > 0.50
    # Assert demand indicators are apparel/saree related
    saree_demand = res1.market_evidence.demand_indicators
    assert any("Textile" in d.indicator_name or "Female" in d.indicator_name or "Wedding" in d.indicator_name or "saree" in d.business_relevance.lower() or "apparel" in d.business_relevance.lower() for d in saree_demand)
    # Zero dairy contamination
    for d in saree_demand:
        assert "milk" not in d.indicator_name.lower()
        assert "cattle" not in d.indicator_name.lower()

    # Step 2: Dairy Farm (Chatra) - ZERO SAREE CONTAMINATION
    dairy_req = {
        "business_profile": {
            "business_profile": {
                "specific_business": "Commercial Dairy Farm (10-Cow Unit)",
                "normalized_concept": "dairy farm",
                "sector": "Animal Husbandry",
                "category": "Dairy Farming",
                "nic": {"code": "01411"}
            },
            "location_profile": {
                "village": "Chatra",
                "district": "Chatra",
                "state": "Jharkhand",
                "coordinates": {"latitude": 24.2089, "longitude": 84.8717}
            }
        },
        "force_refresh": True
    }
    res2 = await agent.run(dairy_req)
    assert res2.business_context.business_id == "dairy_farm"
    assert res2.evidence_quality.overall_quality > 0.50
    # Assert demand indicators are milk/dairy related
    dairy_demand = res2.market_evidence.demand_indicators
    assert any("Milk" in d.indicator_name or "Dairy" in d.indicator_name or "Livestock" in d.category for d in dairy_demand)
    # Verify zero Saree contamination
    for d in dairy_demand:
        assert "saree" not in d.indicator_name.lower()
        assert "apparel" not in d.indicator_name.lower()
        assert "textile" not in d.indicator_name.lower()
    for s in res2.market_evidence.supply_access:
        assert "saree" not in s.hub_name.lower()
        assert "textile" not in s.hub_name.lower()

    # Step 3: Dairy Farm (Solapur) - LOCATION ISOLATION
    dairy_solapur_req = {
        "business_profile": {
            "business_profile": {
                "specific_business": "Commercial Dairy Farm (10-Cow Unit)",
                "normalized_concept": "dairy farm",
                "sector": "Animal Husbandry",
                "category": "Dairy Farming",
                "nic": {"code": "01411"}
            },
            "location_profile": {
                "village": "Solapur",
                "district": "Solapur",
                "state": "Maharashtra",
                "coordinates": {"latitude": 17.6599, "longitude": 75.9064}
            }
        },
        "force_refresh": True
    }
    res3 = await agent.run(dairy_solapur_req)
    assert res3.business_context.business_id == "dairy_farm"
    assert res3.location_context.resolved_location.district == "Solapur"
    assert res3.location_context.resolved_location.state == "Maharashtra"
    assert res3.market_evidence.demographics[0].geography.get("district") == "Solapur"

    # Step 4: Re-run Saree Retail (Chatra) - PROVES ZERO STALE LEAKAGE
    res4 = await agent.run(saree_req)
    assert res4.business_context.business_id == "saree_retail"
    assert res4.location_context.resolved_location.district == "Chatra"
    for d in res4.market_evidence.demand_indicators:
        assert "milk" not in d.indicator_name.lower()
        assert "cattle" not in d.indicator_name.lower()
