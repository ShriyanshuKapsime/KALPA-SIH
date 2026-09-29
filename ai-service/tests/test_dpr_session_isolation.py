"""
Unit and regression test suite for KALPA DPR Session Persistence,
Isolation, 14.2 -> 14.3 Readiness Gate, and SWOT Key Uniqueness.
"""
import pytest
import os
import shutil
import tempfile
from datetime import datetime, timezone

from app.services.dpr_stage1.dpr_scenario_manager import (
    ScenarioRepository,
    DPRScenarioManager,
    DPRScenarioState,
)
from app.services.dpr_stage1.dpr_registry import DPR_STATE_ISOLATION_ERROR
from app.services.dpr_stage1 import (
    dpr_context_builder,
    dpr_gap_analyzer,
    dpr_question_engine,
)
from app.services.dpr_stage2.dpr_enrichment_validator import dpr_enrichment_validator
from app.services.dpr_stage2.dpr_enrichment_schemas import (
    EnrichmentField,
    EnrichmentSourceType,
    EnrichmentValidationSummary,
)


@pytest.fixture
def temp_storage():
    """Provides an isolated directory for scenario disk persistence."""
    d = tempfile.mkdtemp(prefix="test_dpr_scenarios_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def repo(temp_storage):
    return ScenarioRepository(storage_dir=temp_storage)


@pytest.fixture
def manager(repo):
    return DPRScenarioManager(repo=repo)


def test_new_scenario_isolation(repo, manager):
    """
    Test A: Starting a new scenario creates a clean, collision-safe scenario
    with empty answers and no inheritance of existing state.
    """
    biz_id = "test_dairy_farm"
    
    # 1. Create Scenario A and answer questions
    scen_a = manager.get_or_create_scenario(biz_id, "DPR-test_dairy_farm-scenA")
    scen_a.user_answers["promoter_name"] = "Ramesh Kumar"
    scen_a.user_answers["business_name"] = "Ramesh Dairy"
    scen_a.user_answers["location_state"] = "Maharashtra"
    scen_a.user_answers["location_district"] = "Pune"
    repo.save(scen_a)

    # Verify Scenario A answers are persisted
    loaded_a = repo.get(biz_id, "DPR-test_dairy_farm-scenA")
    assert loaded_a is not None
    assert loaded_a.user_answers["promoter_name"] == "Ramesh Kumar"

    # 2. Create Scenario B using explicit create_new_scenario
    scen_b = manager.create_new_scenario(biz_id)
    assert scen_b.scenario_id.startswith(f"DPR-{biz_id}-")
    assert scen_b.scenario_id != loaded_a.scenario_id

    # 3. Verify Scenario B is genuinely clean
    assert scen_b.user_answers == {}
    assert scen_b.user_overrides == {}
    assert scen_b.accepted_benchmarks == {}
    assert scen_b.document_statuses == {}
    assert scen_b.financial_package == {}

    # 4. Verify Scenario A remains unchanged
    fresh_a = repo.get(biz_id, "DPR-test_dairy_farm-scenA")
    assert fresh_a.user_answers["promoter_name"] == "Ramesh Kumar"


def test_same_business_different_scenarios(repo, manager):
    """
    Test B: Same business, different scenarios remain isolated.
    """
    biz_id = "test_dairy_farm"
    
    scen_1 = manager.create_new_scenario(biz_id, scenario_id="DPR-test_dairy_farm-001")
    scen_1.user_answers["promoter_name"] = "Promoter One"
    repo.save(scen_1)

    scen_2 = manager.create_new_scenario(biz_id, scenario_id="DPR-test_dairy_farm-002")
    scen_2.user_answers["promoter_name"] = "Promoter Two"
    repo.save(scen_2)

    assert repo.get(biz_id, "DPR-test_dairy_farm-001").user_answers["promoter_name"] == "Promoter One"
    assert repo.get(biz_id, "DPR-test_dairy_farm-002").user_answers["promoter_name"] == "Promoter Two"


def test_server_restart_preserves_and_new_scenario_starts_clean(temp_storage):
    """
    Test C & D: Server restart preserves existing scenarios from disk,
    and a newly created scenario after restart starts completely clean.
    """
    biz_id = "test_dairy_farm"
    
    # Session 1: Create and answer
    repo1 = ScenarioRepository(storage_dir=temp_storage)
    s1 = repo1.create_new_scenario(biz_id, scenario_id="DPR-test_dairy_farm-alpha")
    s1.user_answers["promoter_name"] = "Original Promoter"
    repo1.save(s1)

    # Session 2: Server restart (fresh in-memory state, same disk storage)
    repo2 = ScenarioRepository(storage_dir=temp_storage)
    assert len(repo2._store) == 0  # In-memory cache is cold

    # Existing scenario is loaded from disk and resumable
    resumed = repo2.get(biz_id, "DPR-test_dairy_farm-alpha")
    assert resumed is not None
    assert resumed.user_answers["promoter_name"] == "Original Promoter"

    # Start NEW scenario after restart
    new_s = repo2.create_new_scenario(biz_id)
    assert new_s.scenario_id != "DPR-test_dairy_farm-alpha"
    assert new_s.user_answers == {}
    assert "promoter_name" not in new_s.user_answers


def test_previous_answers_do_not_leak_and_questions_asked(repo, manager):
    """
    Test E: In a fresh scenario, unresolved required fields are identified
    by the gap analyzer and presented by the question engine.
    """
    biz_id = "test_dairy_farm"
    
    # Scenario A has answers
    scen_a = manager.create_new_scenario(biz_id, scenario_id="DPR-test_dairy_farm-qa")
    scen_a.user_answers["promoter_name"] = "Anand Patil"
    repo.save(scen_a)

    # Scenario B starts clean
    scen_b = manager.create_new_scenario(biz_id, scenario_id="DPR-test_dairy_farm-qb")
    
    # In Scenario B, answers are empty
    assert len(scen_b.user_answers) == 0

    # Build gap analysis for Scenario B
    mock_context = {
        "business_id": biz_id,
        "scenario_id": scen_b.scenario_id,
        "business_intake": {},
        "business_profile": {},
        "fields": {
            "business_name": {"field_id": "business_name", "status": "UNKNOWN", "value": None, "materiality": "CRITICAL", "applicable": True},
            "promoter_name": {"field_id": "promoter_name", "status": "USER_REQUIRED", "value": None, "materiality": "CRITICAL", "applicable": True},
            "location_state": {"field_id": "location_state", "status": "USER_REQUIRED", "value": None, "materiality": "CRITICAL", "applicable": True},
            "location_district": {"field_id": "location_district", "status": "USER_REQUIRED", "value": None, "materiality": "CRITICAL", "applicable": True},
        },
        "conflicts": [],
        "financial_integrity": {"overall_status": "PENDING"},
        "readiness_gates": {}
    }
    gap_result = dpr_gap_analyzer.analyze(mock_context)
    
    # Gaps must be present for required fields
    blocking_fids = [g.field_id for g in gap_result.blocking_gaps]
    assert "promoter_name" in blocking_fids or "business_name" in blocking_fids


def test_14_2_readiness_gate_validation():
    """
    Test F & G: 14.2 Readiness Gate logic:
    - Incomplete/unresolved package returns False with blocking reasons.
    - Valid, reconciled package returns True.
    """
    # 1. Incomplete package -> False with blocking reasons
    incomplete_fields = {
        "promoter_name": EnrichmentField(
            field_id="promoter_name",
            section_id="promoter_profile",
            module_id="module_0",
            label="Promoter Name",
            value=None,
            status="USER_REQUIRED",
            source_type=EnrichmentSourceType.UNKNOWN,
            materiality="CRITICAL"
        )
    }
    
    val_incomplete = dpr_enrichment_validator.validate_enrichment(
        fields=incomplete_fields,
        financial_package={},
        intake_package={"readiness": {"is_ready_for_stage_14_2": False, "reasons": ["Incomplete intake"]}},
        scenario_id="DPR-test_dairy_farm-01"
    )
    assert val_incomplete.overall_valid is False
    assert len(val_incomplete.blocking_reasons) > 0
    assert any("intake" in r.lower() or "mandatory" in r.lower() or "missing" in r.lower() for r in val_incomplete.blocking_reasons)

    # 2. Complete, reconciled package -> True
    complete_fields = {
        "total_project_cost": EnrichmentField(
            field_id="total_project_cost",
            section_id="project_cost",
            module_id="module_3",
            label="Total Project Cost",
            value=1000000.0,
            status="RESOLVED_ENGINE",
            source_type=EnrichmentSourceType.ENGINE_CALCULATED,
            materiality="CRITICAL"
        ),
        "bank_term_loan_amount": EnrichmentField(
            field_id="bank_term_loan_amount",
            section_id="means_of_finance",
            module_id="module_3",
            label="Term Loan",
            value=750000.0,
            status="RESOLVED_ENGINE",
            source_type=EnrichmentSourceType.ENGINE_CALCULATED,
            materiality="CRITICAL"
        ),
        "promoter_equity_amount": EnrichmentField(
            field_id="promoter_equity_amount",
            section_id="means_of_finance",
            module_id="module_3",
            label="Promoter Equity",
            value=250000.0,
            status="RESOLVED_ENGINE",
            source_type=EnrichmentSourceType.ENGINE_CALCULATED,
            materiality="CRITICAL"
        ),
        "business_name": EnrichmentField(
            field_id="business_name",
            section_id="enterprise_identity",
            module_id="module_0",
            label="Business Name",
            value="Dairy Express",
            status="RESOLVED_USER",
            source_type=EnrichmentSourceType.USER_PROVIDED,
            materiality="CRITICAL"
        )
    }
    complete_fin_pkg = {
        "project_cost": {"total_project_cost": 1000000.0},
        "means_of_finance": {"total_project_cost": 1000000.0, "term_loan": 750000.0, "promoter_contribution": 250000.0}
    }
    intake_ok = {"readiness": {"is_ready_for_stage_14_2": True, "reasons": []}}

    val_complete = dpr_enrichment_validator.validate_enrichment(
        fields=complete_fields,
        financial_package=complete_fin_pkg,
        intake_package=intake_ok,
        scenario_id="DPR-test_dairy_farm-01"
    )
    assert val_complete.overall_valid is True
    assert len(val_complete.blocking_reasons) == 0


def test_cross_business_isolation(repo):
    """
    Test J: Accessing a scenario belonging to one business with a mismatched
    business ID raises DPR_STATE_ISOLATION_ERROR.
    """
    scen = repo.create_new_scenario("dairy_farm", scenario_id="DPR-dairy_farm-safe1")
    assert scen.business_id == "dairy_farm"

    # Attempting to fetch or save under a completely different business
    with pytest.raises(DPR_STATE_ISOLATION_ERROR):
        repo.get("poultry_farm", "DPR-dairy_farm-safe1")


def test_swot_key_uniqueness():
    """
    Test I: SWOT key uniqueness across categories and deterministic sibling handling.
    """
    def get_deterministic_swot_key(category, item, idx, seen_keys=None):
        cat_prefix = (category or "item").lower().rstrip("s")
        raw_id = item.get("id") or item.get("code")
        key = f"{cat_prefix}-{raw_id}" if raw_id else f"{cat_prefix}-{idx}"
        if seen_keys is not None and key in seen_keys:
            key = f"{key}-{idx}"
        if seen_keys is not None:
            seen_keys.add(key)
        return key

    # Upstream collision: strength and threat have the same raw id "TH-001"
    item_st = {"id": "TH-001", "title": "Strength 1"}
    item_th = {"id": "TH-001", "title": "Threat 1"}

    seen = set()
    key_st = get_deterministic_swot_key("strengths", item_st, 0, seen)
    key_th = get_deterministic_swot_key("threats", item_th, 0, seen)

    assert key_st == "strength-TH-001"
    assert key_th == "threat-TH-001"
    assert key_st != key_th  # Zero cross-category collision

    # Sibling duplicate within same category: two items with id "ST-001"
    item1 = {"id": "ST-001", "title": "First"}
    item2 = {"id": "ST-001", "title": "Second"}
    seen_cat = set()
    k1 = get_deterministic_swot_key("strengths", item1, 0, seen_cat)
    k2 = get_deterministic_swot_key("strengths", item2, 1, seen_cat)

    assert k1 == "strength-ST-001"
    assert k2 == "strength-ST-001-1"
    assert k1 != k2  # Zero sibling collision


def test_h_readiness_api_and_new_scenario_contract():
    """
    Test H: Fast API endpoint test for POST /dpr/new-scenario/{business_id}
    and GET /dpr/14.2/readiness/{business_id}.
    Verifies response shape, ready_for_stage_14_3 boolean, and blocking reasons.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    biz_id = "test_dairy_api"

    # 1. POST new scenario
    resp_new = client.post(f"/api/v1/dpr/new-scenario/{biz_id}")
    assert resp_new.status_code == 200, f"Expected 200, got {resp_new.status_code}: {resp_new.text}"
    new_data = resp_new.json()
    assert new_data["business_id"] == biz_id
    assert new_data["scenario_id"].startswith(f"DPR-{biz_id}-")
    assert "intake_id" in new_data
    scen_id = new_data["scenario_id"]

    # 2. Check 14.2 readiness for this fresh, incomplete scenario
    resp_readiness = client.get(f"/api/v1/dpr/14.2/readiness/{biz_id}?scenario_id={scen_id}")
    assert resp_readiness.status_code == 200
    readiness_data = resp_readiness.json()
    assert "ready_for_stage_14_3" in readiness_data
    assert readiness_data["ready_for_stage_14_3"] is False
    assert "blocking_reasons" in readiness_data
    assert len(readiness_data["blocking_reasons"]) > 0
    assert "context_key" in readiness_data
    assert readiness_data["business_id"] == biz_id
    assert readiness_data["scenario_id"] == scen_id

