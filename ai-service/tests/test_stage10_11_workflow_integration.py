"""
End-to-End Deterministic Integration Test: Stage 6 -> Stage 8 -> Stage 9 -> Stage 10 -> Stage 11.
Validates the complete workflow chain across AgentRegistry and Orchestrator execution plan.
All external calls mocked; 100% deterministic local execution.
"""
import pytest
from app.agents.registry import agent_registry
from app.services.orchestration.hybrid_planner import hybrid_planner
from app.services.market_intelligence_engine import market_intelligence_engine
from app.services.opportunity_evaluation_engine import opportunity_evaluation_engine
from app.services.financial_engine import financial_engine
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine
from app.services.risk_engine import risk_engine


class TestStage10Stage11WorkflowIntegration:
    """
    End-to-End integration test across all 5 active downstream engines.
    """

    @pytest.mark.asyncio
    async def test_full_pipeline_stage6_to_stage11_execution(self):
        # 1. Canonical Input Business Profile
        business_profile = {
            "business_profile": {
                "business_id": "flour_milling_micro",
                "specific_business": "Atta Chakki Unit",
                "sector": "Agro Processing",
                "category": "Food Manufacturing",
                "nic_code": "10611"
            },
            "location_profile": {
                "village": "Gokak",
                "district": "Belagavi",
                "state": "Karnataka"
            },
            "financial_profile": {
                "available_margin_capital": 100000.0,
                "preferred_project_cost": 1000000.0
            },
            "user_profile": {
                "skills": {
                    "skills": ["Chakki Stone dressing", "Motor maintenance", "Weighment"],
                    "skill_level": "INTERMEDIATE"
                },
                "experience": {
                    "years_of_experience": 3.0,
                    "domain": "Flour Milling"
                },
                "training": {
                    "has_formal_training": True,
                    "certifications": ["FoSTaC Food Safety"]
                },
                "resources": {
                    "available_area_sqft": 250.0,
                    "power_connection_type": "THREE_PHASE_COMMERCIAL"
                },
                "operations": {
                    "commitment_type": "FULL_TIME",
                    "available_family_helpers": 1
                }
            }
        }

        # 2. Verify Orchestrator Execution Plan Generation
        plan = hybrid_planner.generate_deterministic_plan(business_profile)
        agent_names = [item["agent"] for item in plan]
        assert "opportunity_evaluation_engine" in agent_names
        assert "finance_engine" in agent_names
        assert "entrepreneur_profile_engine" in agent_names
        assert "risk_engine" in agent_names

        # 3. Step 1: Stage 6 Market Intelligence Engine Evaluation
        stage5_input = {
            "analysis_id": "test-e2e-workflow",
            "session_id": "session-e2e",
            "business_context": {"specific_business": "Atta Chakki Unit", "business_id": "flour_milling_micro"},
            "location_context": {"district": "Belagavi", "state": "Karnataka"},
            "market_evidence": {
                "demographics": {"population_total": 45000, "households_total": 9000},
                "competition": {"competitors_found": [{"name": "Local Chakki 1", "distance_km": 2.5}]},
                "infrastructure": {"three_phase_power": True, "grid_reliability_index": 0.88}
            }
        }
        stage6_res = market_intelligence_engine.analyze(stage5_input)
        assert stage6_res is not None

        # 4. Step 2: Stage 8 Opportunity Evaluation Engine
        stage8_input = {
            "analysis_id": "test-e2e-workflow",
            "market_intelligence": stage6_res.model_dump()
        }
        stage8_res = opportunity_evaluation_engine.evaluate(stage8_input)
        assert 0.0 <= stage8_res.opportunity_result.market_opportunity_score <= 1.0
        assert stage8_res.opportunity_result.level is not None

        # 5. Step 3: Stage 9 Financial Engine
        stage9_input = {
            "analysis_id": "test-e2e-workflow",
            "financial_profile": {"available_margin_capital": 100000.0},
            "business_profile": business_profile["business_profile"]
        }
        stage9_res = financial_engine.analyze(stage9_input)
        assert stage9_res.financial_analysis is not None
        dscr = stage9_res.financial_analysis.debt_service.dscr
        assert dscr is not None
        assert dscr > 0.0

        # 6. Step 4: Stage 10 Entrepreneur Profile Engine
        stage10_input = {
            "analysis_id": "test-e2e-workflow",
            "user_profile": business_profile["user_profile"],
            "business_profile": business_profile["business_profile"]
        }
        stage10_res = entrepreneur_profile_engine.analyze(stage10_input)
        assert stage10_res.success is True
        assert stage10_res.status == "READY"
        assert stage10_res.readiness_score >= 75.0

        # 7. Step 5: Stage 11 Risk Engine (Consumes outputs of 6, 8, 9, 10)
        stage11_input = {
            "analysis_id": "test-e2e-workflow",
            "business_profile": business_profile["business_profile"],
            "market_intelligence": stage6_res.model_dump(),
            "opportunity_evaluation": stage8_res.model_dump(),
            "financial_analysis": stage9_res.model_dump(),
            "entrepreneur_readiness": stage10_res.model_dump()
        }
        stage11_res = risk_engine.analyze(stage11_input)
        assert stage11_res.success is True
        assert 0.0 <= stage11_res.overall_risk_score <= 1.0
        assert stage11_res.overall_risk_severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert len(stage11_res.category_risks) == 7

        # 8. Verify Upstream Data Integrity in Stage 11
        # Financial evidence must reflect Stage 9 DSCR
        fin_evidence = stage11_res.category_risks["FINANCIAL"].evidence
        assert any(f"{dscr:.2f}" in str(ev) for ev in fin_evidence)

        # Operational evidence must reflect Stage 10 Readiness
        ops_evidence = stage11_res.category_risks["OPERATIONAL"].evidence
        assert any(f"{stage10_res.readiness_score:.1f}" in str(ev) for ev in ops_evidence)

    @pytest.mark.asyncio
    async def test_agent_registry_execution_of_stage10_and_11(self):
        """Validates adapter execution through the central AgentRegistry."""
        state = {
            "analysis_id": "test-registry-exec",
            "session_id": "session-123",
            "financial_profile": {"available_margin_capital": 100000.0},
            "agent_results": {}
        }
        business_profile = {
            "business_profile": {
                "business_id": "oil_expeller_unit",
                "specific_business": "Mustard Oil Expeller"
            },
            "user_profile": {
                "skills": {"skills": ["Cold pressed oil extraction"]},
                "experience": {"years_of_experience": 2.5},
                "training": {"has_formal_training": True},
                "resources": {"available_area_sqft": 400.0, "power_connection_type": "THREE_PHASE_COMMERCIAL"},
                "operations": {"commitment_type": "FULL_TIME"}
            }
        }

        # Execute Stage 10 via Registry
        res10 = await agent_registry.execute_agent(
            agent_id="entrepreneur_profile_engine",
            business_profile=business_profile,
            knowledge_context={},
            state=state
        )
        assert res10["success"] is True
        assert res10["execution_metadata"]["stage"] == 10
        state["agent_results"]["entrepreneur_profile_engine"] = res10

        # Execute Stage 11 via Registry
        res11 = await agent_registry.execute_agent(
            agent_id="risk_engine",
            business_profile=business_profile,
            knowledge_context={},
            state=state
        )
        assert res11["success"] is True
        assert res11["execution_metadata"]["stage"] == 11
        assert "category_risks" in res11
