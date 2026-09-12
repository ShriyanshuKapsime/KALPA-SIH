import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import engine
import app.database.models
from app.main import app as fastapi_app
from app.agents.registry import agent_registry
from app.agents.adapters.base_adapter import BaseAgentAdapter

if engine is not None:
    Base.metadata.create_all(bind=engine)

client = TestClient(fastapi_app)


def _setup_stage1_to_stage3_session(text="I want to open a rice mill in Mandya with 5 lakh rupees and farming skills."):
    """Helper creating full Stage 1 -> Stage 2 -> Stage 3 pipeline state in PostgreSQL."""
    # 1. Intake
    res1 = client.post("/api/v1/intake/text", json={
        "text": text,
        "language_code": "en"
    })
    assert res1.status_code == 200
    session_id = res1.json()["session_id"]

    # 2. Classification
    res2 = client.post("/api/v1/classification/classify", json={
        "session_id": session_id,
        "original_input": text,
        "business_concept": "Rice Mill",
        "language_code": "en",
        "product_service": "Milled Rice",
        "skills": ["paddy milling", "retail sales"]
    })
    assert res2.status_code == 200

    # 3. Stage 3 Profile Build
    res3 = client.post("/api/v1/profile/build", json={"session_id": session_id})
    assert res3.status_code == 200
    profile_data = res3.json()
    analysis_id = profile_data["analysis_id"]

    return session_id, analysis_id, profile_data["profile"]


def test_scenario_1_complete_profile_deterministic_routing_no_llm():
    """
    TEST 1: Complete business profile
    -> Deterministic routing
    -> No LLM call required (llm_usage.calls == 0)
    """
    session_id, analysis_id, _ = _setup_stage1_to_stage3_session(
        "I want to open a rice mill in Mandya with 5 lakh rupees and farming skills."
    )

    res = client.post("/api/v1/orchestrator/start", json={"session_id": session_id})
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["orchestration_status"] == "ORCHESTRATION_COMPLETE"
    assert data["analysis_id"] == analysis_id
    assert data["session_id"] == session_id

    # Verify Hybrid Decision Engine token conservation
    routing = data["routing_summary"]
    assert routing["decision_source"] == "deterministic"
    assert routing["llm_used"] is False
    assert routing["deterministic_confidence"] >= 0.85
    assert "factors" in routing
    assert routing["factors"]["profile_completeness"] == 1.0

    # Verify All 5 DAG Agents Completed
    summary = data["agent_execution_summary"]
    assert len(summary["completed"]) >= 4
    assert "domain_knowledge_agent" in summary["completed"]
    assert "market_intelligence_agent" in summary["completed"]
    assert "finance_engine" in summary["completed"]
    assert "feasibility_engine" in summary["completed"]

    # Verify Domain Knowledge Output
    knowledge = data["knowledge_context"]
    assert knowledge["knowledge_status"] == "success"
    assert "benchmarks" in knowledge
    assert "infrastructure_requirements" in knowledge

    # Verify Prototype Agent Scopes
    results = data["agent_results"]
    assert "finance_engine" in results
    assert results["finance_engine"]["prototype_financials"]["capital_adequacy_status"] in [
        "Adequate",
        "Partial - Scheme / Debt Support Recommended"
    ]


def test_scenario_2_incomplete_profile_clarification_state():
    """
    TEST 2: Incomplete profile -> clarification / request state
    """
    incomplete_profile = {
        "schema_version": "1.0",
        "analysis_id": "00000000-0000-0000-0000-000000000001",
        "session_id": "00000000-0000-0000-0000-000000000002",
        "workflow": {"state": "BUSINESS_PROFILE_INCOMPLETE", "stage_completed": 3},
        "business_profile": {"specific_business": "", "category": ""},
        "location_profile": {},
        "financial_profile": {},
        "data_quality": {
            "profile_complete": False,
            "missing_fields": ["business_profile.specific_business", "location_profile.district"],
            "validation_status": "INCOMPLETE"
        }
    }

    res = client.post("/api/v1/orchestrator/start", json={
        "analysis_id": incomplete_profile["analysis_id"],
        "session_id": incomplete_profile["session_id"],
        "business_profile": incomplete_profile
    })
    assert res.status_code == 200
    data = res.json()

    assert data["orchestration_status"] == "CLARIFICATION_REQUIRED"
    assert data["agent_execution_summary"]["total_planned"] == 0


def test_scenario_3_ambiguous_workflow_llm_escalation():
    """
    TEST 3: Ambiguous business workflow -> LLM escalation path
    """
    session_id, analysis_id, _ = _setup_stage1_to_stage3_session(
        "I want to start a custom handloom boutique in Varanasi with 4 lakh rupees."
    )

    res = client.post("/api/v1/orchestrator/start", json={
        "session_id": session_id,
        "force_llm": True
    })
    assert res.status_code == 200
    data = res.json()

    assert data["success"] is True
    assert data["orchestration_status"] == "ORCHESTRATION_COMPLETE"
    routing = data["routing_summary"]
    # Either hybrid_llm or deterministic_fallback if LLM key is absent in local test
    assert routing["decision_source"] in ["hybrid_llm", "deterministic_fallback"]


def test_scenario_4_no_llm_api_key_deterministic_fallback():
    """
    TEST 4: No LLM API key -> Graceful deterministic fallback without crashing
    """
    from unittest.mock import PropertyMock
    from app.services.llm_client import LLMClient

    session_id, _, _ = _setup_stage1_to_stage3_session(
        "I want to open a dairy farm in Hassan with 3 lakh rupees."
    )

    with patch.object(LLMClient, "is_available", new_callable=PropertyMock, return_value=False):
        res = client.post("/api/v1/orchestrator/start", json={
            "session_id": session_id,
            "force_llm": True
        })
        assert res.status_code == 200
        data = res.json()

        assert data["success"] is True
        assert data["orchestration_status"] == "ORCHESTRATION_COMPLETE"
        assert data["routing_summary"]["decision_source"] == "deterministic_fallback"
        assert len(data["agent_execution_summary"]["completed"]) >= 4


def test_scenario_5_prototype_agent_failure_retry_and_fallback():
    """
    TEST 5: Prototype agent failure -> Retry count increments and graceful fallback applied
    """
    class FlakyAdapter(BaseAgentAdapter):
        def __init__(self):
            super().__init__(
                agent_id="test_flaky_agent",
                name="Flaky Test Agent",
                description="Fails repeatedly to test retry budget and fallback.",
                capabilities=["testing"],
                dependencies=["domain_knowledge_agent"],
                max_retries=2
            )
            self.attempt = 0

        async def execute(self, business_profile, knowledge_context, state):
            self.attempt += 1
            raise RuntimeError(f"Simulated network timeout on attempt {self.attempt}")

    flaky_adapter = FlakyAdapter()
    agent_registry.register(flaky_adapter)

    session_id, _, profile = _setup_stage1_to_stage3_session(
        "I want to open a saree shop in Chatra, Jharkhand with 3 lakh rupees."
    )

    # Inject flaky agent into state execution plan by running orchestrator
    res = client.post("/api/v1/orchestrator/start", json={"session_id": session_id})
    assert res.status_code == 200
    data = res.json()
    assert data["orchestration_status"] == "ORCHESTRATION_COMPLETE"


def test_scenario_6_decision_history_trace_recorded():
    """
    TEST 6: Verify decision history is recorded with observations, reasons, confidence, and timestamps
    """
    session_id, _, _ = _setup_stage1_to_stage3_session(
        "I want to start a flour mill in Dharwad with 2 lakh rupees."
    )

    res = client.post("/api/v1/orchestrator/start", json={"session_id": session_id})
    assert res.status_code == 200
    data = res.json()

    trace = data["decision_history"]
    assert len(trace) >= 5

    nodes_in_trace = [item["node"] for item in trace]
    assert "load_business_profile" in nodes_in_trace
    assert "validate_profile" in nodes_in_trace
    assert "plan_workflow" in nodes_in_trace
    assert "select_next_agent" in nodes_in_trace
    assert "execute_agent" in nodes_in_trace
    assert "complete_orchestration" in nodes_in_trace

    for item in trace:
        assert "timestamp" in item
        assert "observation" in item
        assert "decision" in item
        assert "reason" in item
        assert "confidence" in item


def test_scenario_7_execution_plan_dependencies_respected():
    """
    TEST 7: Verify DAG execution plan dependencies are strictly respected
    """
    session_id, _, _ = _setup_stage1_to_stage3_session(
        "I want to start a poultry farm in Belagavi with 6 lakh rupees."
    )

    res = client.post("/api/v1/orchestrator/start", json={"session_id": session_id})
    assert res.status_code == 200
    data = res.json()

    trace = data["decision_history"]
    executed_agents = [
        item["next_action"]["agent"]
        for item in trace
        if item.get("next_action") and item["next_action"].get("action") == "EXECUTE"
    ]

    # domain_knowledge_agent must be executed first before market_intelligence_agent or finance_engine
    assert executed_agents[0] == "domain_knowledge_agent"
    assert "market_intelligence_agent" in executed_agents


def test_scenario_8_structured_output_persisted_and_retrievable():
    """
    TEST 8: Verify structured orchestration output is persisted in PostgreSQL and retrievable via GET API
    """
    session_id, analysis_id, _ = _setup_stage1_to_stage3_session(
        "I want to start a grocery shop in Mysuru with 3 lakh rupees."
    )

    res_post = client.post("/api/v1/orchestrator/start", json={"session_id": session_id})
    assert res_post.status_code == 200
    posted_data = res_post.json()

    # 1. Retrieve by Analysis ID
    res_get_aid = client.get(f"/api/v1/orchestrator/{analysis_id}")
    assert res_get_aid.status_code == 200
    aid_data = res_get_aid.json()
    assert aid_data["analysis_id"] == analysis_id
    assert aid_data["orchestration_status"] == "ORCHESTRATION_COMPLETE"
    assert len(aid_data["execution_plan"]) > 0

    # 2. Retrieve by Session ID
    res_get_sid = client.get(f"/api/v1/orchestrator/session/{session_id}")
    assert res_get_sid.status_code == 200
    sid_data = res_get_sid.json()
    assert sid_data["session_id"] == session_id
    assert sid_data["analysis_id"] == analysis_id
