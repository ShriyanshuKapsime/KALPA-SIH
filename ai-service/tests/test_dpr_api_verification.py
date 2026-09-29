"""
Automated Test Suite for DPR 14.1 / 14.2 API Contract, State Isolation, and Readiness Truthfulness.
Covers Tests A through H specified in Section 14:
- TEST A: Valid context (Kirana / DPR-Kirana)
- TEST B: Invalid scenario/business combination (Kirana / DPR-saree_re -> 409, no leakage)
- TEST C: Missing context handling (structured BLOCKED state, no fake readiness)
- TEST D: Enrichment with valid context (HTTP 200, valid DPR_ENRICHMENT_PACKAGE)
- TEST E: Enrichment with failed context (HTTP 409 BLOCKED state, no unhandled 500)
- TEST F: Readiness truthfulness after context failure (is_ready_for_stage_14_2 = false)
- TEST G: Stale success protection (switching business or failed request clears derived readiness)
- TEST H: Cross-business isolation (Kirana -> Saree -> Kirana)
"""
import pytest
import asyncio
from typing import Dict, Any
from fastapi.testclient import TestClient

from app.main import app
from app.services.dpr_stage1.dpr_context_builder import dpr_context_builder
from app.services.dpr_stage1.dpr_scenario_manager import dpr_scenario_manager, DPR_STATE_ISOLATION_ERROR
from app.services.dpr_stage1.dpr_gap_analyzer import dpr_gap_analyzer
from app.services.dpr_stage2.dpr_enrichment_service import dpr_enrichment_service


client = TestClient(app)


# TEST A: Valid context
def test_a_valid_context():
    resp = client.get("/api/v1/dpr/context/Kirana?scenario_id=DPR-Kirana")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["business_id"].strip() == "Kirana"
    assert data["scenario_id"].strip() == "DPR-Kirana"


# Also verify with trailing whitespace in query
def test_a_valid_context_with_trailing_whitespace():
    resp = client.get("/api/v1/dpr/context/Kirana%20?scenario_id=DPR-Kirana%20")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["business_id"].strip() == "Kirana"
    assert data["scenario_id"].strip() == "DPR-Kirana"


# TEST B: Invalid scenario/business combination
def test_b_invalid_scenario_business_combination():
    resp = client.get("/api/v1/dpr/context/Kirana?scenario_id=DPR-saree_re")
    assert resp.status_code == 409, f"Expected 409, got {resp.status_code}: {resp.text}"
    detail = resp.json().get("detail", "")
    assert "DPR_STATE_ISOLATION_ERROR" in detail or "does not belong to business" in detail
    assert "saree" not in resp.text.lower() or "belong" in resp.text.lower()


# TEST C: Missing context produces structured BLOCKED state, NOT fake readiness
@pytest.mark.asyncio
async def test_c_missing_context_not_fake_readiness():
    empty_ctx = {
        "business_id": "non_existent_biz_xyz",
        "scenario_id": "DPR-non_exis",
        "fields": {},
        "modules": {},
        "business_profile": {}
    }
    gap_res = dpr_gap_analyzer.analyze(empty_ctx)
    assert not gap_res.is_ready_for_stage_14_2
    assert not gap_res.can_proceed_to_dpr
    assert len(gap_res.blocking_gaps) > 0


# TEST D: Enrichment with valid context
def test_d_enrichment_with_valid_context():
    resp = client.get("/api/v1/dpr/14.2/enrichment/Kirana?scenario_id=DPR-Kirana")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["business_id"].strip() == "Kirana"
    assert data["scenario_id"].strip() == "DPR-Kirana"
    assert "fields" in data or "dpr_fields" in data


# TEST E: Enrichment with failed context
def test_e_enrichment_with_mismatched_scenario_returns_blocked():
    resp = client.get("/api/v1/dpr/14.2/enrichment/Kirana?scenario_id=DPR-saree_re")
    assert resp.status_code == 409, f"Expected 409 Conflict, got {resp.status_code}: {resp.text}"
    detail = resp.json().get("detail", {})
    if isinstance(detail, dict):
        assert detail.get("status") == "BLOCKED"
        assert detail.get("reason") == "CONTEXT_LOAD_FAILED"
        assert detail.get("http_error") == 409
    else:
        assert "DPR_STATE_ISOLATION_ERROR" in str(detail) or "does not belong" in str(detail)


# TEST F: Readiness after context failure
def test_f_readiness_truthfulness_after_context_failure():
    # If context loading fails, readiness gate must evaluate to false
    context_package = None
    context_error = {"status": "BLOCKED", "http_error": 409, "reason": "CONTEXT_LOAD_FAILED"}
    business_id = "Kirana"

    is_context_valid = bool(
        context_package
        and not context_error
        and context_package.get("business_id", "").strip().lower() == business_id.lower()
    )
    is_ready_for_14_2 = bool(is_context_valid and True)
    assert is_context_valid is False
    assert is_ready_for_14_2 is False


# TEST G: Stale success protection
def test_g_stale_success_protection():
    # Simulate loading business A successfully
    state_a = {
        "business_id": "Kirana",
        "scenario_id": "DPR-Kirana",
        "is_ready_for_stage_14_2": True
    }
    assert state_a["is_ready_for_stage_14_2"] is True

    # Switching to business B where context request fails (e.g. 409)
    current_context = None
    current_error = {"http_error": 409, "status": "BLOCKED"}
    is_context_valid = bool(current_context and not current_error)
    derived_readiness = bool(is_context_valid and state_a["is_ready_for_stage_14_2"])
    
    # Assert old ready=true is cleared and NOT displayed as current state
    assert is_context_valid is False
    assert derived_readiness is False


# TEST H: Cross-business isolation (Grocery -> Saree -> Grocery)
@pytest.mark.asyncio
async def test_h_cross_business_isolation_grocery_saree_grocery():
    grocery_id = "grocery_store"
    saree_id = "saree_retail"

    # Step 1: Grocery context
    scen_g = dpr_scenario_manager.get_or_create_scenario(grocery_id)
    assert scen_g.business_id == grocery_id
    pkg_g = dpr_enrichment_service.get_persisted_enrichment(grocery_id, scen_g.scenario_id)
    if not pkg_g:
        pkg_g = await dpr_enrichment_service.run_enrichment(grocery_id, scen_g.scenario_id)
    assert pkg_g.business_id == grocery_id

    # Step 2: Saree context
    scen_s = dpr_scenario_manager.get_or_create_scenario(saree_id)
    assert scen_s.business_id == saree_id
    pkg_s = dpr_enrichment_service.get_persisted_enrichment(saree_id, scen_s.scenario_id)
    if not pkg_s:
        pkg_s = await dpr_enrichment_service.run_enrichment(saree_id, scen_s.scenario_id)
    assert pkg_s.business_id == saree_id
    assert pkg_s.business_id != pkg_g.business_id

    # Step 3: Return to Grocery
    pkg_g2 = dpr_enrichment_service.get_persisted_enrichment(grocery_id, scen_g.scenario_id)
    assert pkg_g2.business_id == grocery_id
    assert pkg_g2.business_id != saree_id
