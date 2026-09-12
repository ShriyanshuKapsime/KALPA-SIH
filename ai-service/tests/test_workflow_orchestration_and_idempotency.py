"""
Integration tests for KALPA SIH Workflow Orchestration, State Synchronization,
and Market Intelligence Idempotency (Requirement K).
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.schemas.orchestrator import StartOrchestratorRequest, OrchestratorResponse, CanonicalWorkflowState
from app.services.orchestration.orchestrator_service import orchestrator_service
from app.agents.market_intelligence.market_agent import market_intelligence_agent
from app.database.session import get_db_context
from app.database.models.market import MarketEvidenceRecord
from app.database.models.orchestrator import OrchestrationRecord
from app.database.models.profile import StructuredBusinessProfile


SAMPLE_DAIRY_PROFILE = {
    "analysis_id": str(uuid.uuid4()),
    "session_id": str(uuid.uuid4()),
    "business_profile": {
        "business_id": "commercial_dairy_solapur",
        "specific_business": "Commercial Dairy Farm (10-Cow Unit)",
        "normalized_concept": "dairy farm",
        "sector": "Animal Husbandry",
        "category": "Commercial Dairy Farm",
        "nic": {"code": "01411", "description": "Raising of dairy cattle"}
    },
    "location_profile": {
        "name": "Solapur Catchment",
        "district": "Solapur",
        "state": "Maharashtra",
        "country": "India",
        "coordinates": {"latitude": 17.6599, "longitude": 75.9064}
    },
    "financial_profile": {"available_capital": 350000.0},
    "analysis_requirements": {
        "direct_competitors": ["Local Dairy Units"],
        "adjacent_competitors": ["Milk Collection Centers"],
        "substitute_businesses": ["Packaged Milk Distributors"],
        "demand_features": ["catchment_population", "milk_consumption_proxy"],
        "infrastructure_requirements": ["bulk milk chiller access", "veterinary clinic proximity"],
        "required_datasets": ["Census 2011", "Livestock Census", "LGD"]
    },
    "data_quality": {"profile_complete": True, "missing_fields": []}
}


@pytest.mark.asyncio
async def test_orchestrator_completes_stage4_and_stage5_workflow_state():
    """
    Test 1: Orchestrator executes LangGraph orchestration and returns
    CanonicalWorkflowState with Stage 5/6 completed.
    """
    test_analysis_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    req_profile = dict(SAMPLE_DAIRY_PROFILE)
    req_profile["analysis_id"] = test_analysis_id
    req_profile["session_id"] = test_session_id

    request = StartOrchestratorRequest(
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        business_profile=req_profile,
        force_llm=False
    )

    response = await orchestrator_service.run_orchestrator(request)

    assert response.success is True
    assert response.analysis_id == test_analysis_id
    assert response.session_id == test_session_id
    assert response.workflow.current_stage == 4
    assert 5 in response.workflow.completed_stages
    assert response.workflow.workflow_status in ("ORCHESTRATION_COMPLETE", "ANALYZING", "PLANNING", "EXECUTING")
    assert response.business_context.get("sector") == "Animal Husbandry"


@pytest.mark.asyncio
async def test_market_intelligence_idempotency_prevents_duplicate_sarvam_and_tools():
    """
    Test 2 & 6: Existing MarketEvidenceRecord prevents another Sarvam call and tool execution.
    """
    test_analysis_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    req_profile = dict(SAMPLE_DAIRY_PROFILE)
    req_profile["analysis_id"] = test_analysis_id
    req_profile["session_id"] = test_session_id

    # 1. First execution creates the record
    first_profile = await market_intelligence_agent.collect_evidence(
        business_profile=req_profile,
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        force_refresh=False
    )
    assert first_profile is not None
    assert first_profile.analysis_id == test_analysis_id

    # 2. Second execution with mock Sarvam service to verify zero Sarvam calls
    with patch("app.services.sarvam_llm_service.sarvam_llm_service.plan_market_collection") as mock_sarvam:
        second_profile = await market_intelligence_agent.collect_evidence(
            business_profile=req_profile,
            analysis_id=test_analysis_id,
            session_id=test_session_id,
            force_refresh=False
        )
        # Sarvam must NOT have been called due to idempotency hit
        mock_sarvam.assert_not_called()
        assert second_profile.analysis_id == test_analysis_id
        assert second_profile.business_context.business_id == "dairy_farm"
        assert second_profile.location_context.resolved_location is not None


@pytest.mark.asyncio
async def test_market_evidence_record_upsert_no_unique_constraint_violation():
    """
    Test 5: Running collection twice with same analysis_id does NOT throw UniqueViolation error.
    """
    test_analysis_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    req_profile = dict(SAMPLE_DAIRY_PROFILE)
    req_profile["analysis_id"] = test_analysis_id
    req_profile["session_id"] = test_session_id

    # Execute twice (with force_refresh=True to test the DB upsert node directly)
    res1 = await market_intelligence_agent.collect_evidence(
        business_profile=req_profile,
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        force_refresh=False
    )
    assert res1.analysis_id == test_analysis_id

    res2 = await market_intelligence_agent.collect_evidence(
        business_profile=req_profile,
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        force_refresh=True
    )
    assert res2.analysis_id == test_analysis_id

    # Verify only ONE record exists in DB for this analysis_id
    with get_db_context() as db:
        if db:
            records = db.query(MarketEvidenceRecord).filter(
                MarketEvidenceRecord.id == uuid.UUID(test_analysis_id)
            ).all()
            assert len(records) == 1
            assert records[0].workflow_status == "MARKET_EVIDENCE_COLLECTED"


@pytest.mark.asyncio
async def test_force_refresh_allows_rerun():
    """
    Test 7: force_refresh=True intentionally bypasses the idempotency cache.
    """
    test_analysis_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    req_profile = dict(SAMPLE_DAIRY_PROFILE)
    req_profile["analysis_id"] = test_analysis_id
    req_profile["session_id"] = test_session_id

    # First run
    await market_intelligence_agent.collect_evidence(
        business_profile=req_profile,
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        force_refresh=False
    )

    # Force refresh rerun
    res = await market_intelligence_agent.collect_evidence(
        business_profile=req_profile,
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        force_refresh=True
    )
    assert res.analysis_id == test_analysis_id
    assert res.workflow.status in ("complete", "success")


@pytest.mark.asyncio
async def test_workflow_state_lookup_by_analysis_and_session_id():
    """
    Test 3 & 4: get_workflow_state resolves workflow by analysis_id and session_id.
    """
    test_analysis_id = str(uuid.uuid4())
    test_session_id = str(uuid.uuid4())
    req_profile = dict(SAMPLE_DAIRY_PROFILE)
    req_profile["analysis_id"] = test_analysis_id
    req_profile["session_id"] = test_session_id

    # Start orchestrator to create DB record
    request = StartOrchestratorRequest(
        analysis_id=test_analysis_id,
        session_id=test_session_id,
        business_profile=req_profile,
        force_llm=False
    )
    await orchestrator_service.run_orchestrator(request)

    # Lookup by analysis_id
    wf_by_aid = await orchestrator_service.get_workflow_state(test_analysis_id)
    assert wf_by_aid is not None
    assert wf_by_aid.analysis_id == test_analysis_id
    assert wf_by_aid.session_id == test_session_id
    assert 4 in wf_by_aid.completed_stages
    assert 5 in wf_by_aid.completed_stages

    # Lookup by session_id
    wf_by_sid = await orchestrator_service.get_workflow_state(test_session_id)
    assert wf_by_sid is not None
    assert wf_by_sid.session_id == test_session_id
    assert wf_by_sid.analysis_id == test_analysis_id


@pytest.mark.asyncio
async def test_nonexistent_workflow_state_returns_none():
    """
    Test 4 (cont): Invalid or non-existent workflow IDs return None cleanly.
    """
    random_id = str(uuid.uuid4())
    wf = await orchestrator_service.get_workflow_state(random_id)
    assert wf is None

    invalid_id = "not-a-valid-uuid"
    wf_invalid = await orchestrator_service.get_workflow_state(invalid_id)
    assert wf_invalid is None
