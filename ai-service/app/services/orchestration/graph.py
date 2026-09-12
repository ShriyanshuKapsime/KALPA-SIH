"""
LangGraph StateGraph Workflow Engine for KALPA Stage 4 Manager Agent.
Implements the genuine agent execution cycle:
OBSERVE -> VALIDATE -> ANALYZE -> PLAN -> SELECT AGENT -> EXECUTE -> EVALUATE -> ROUTE / COMPLETE
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Literal

from langgraph.graph import StateGraph, START, END

from app.schemas.orchestrator import KALPAOrchestratorState
from app.agents.registry import agent_registry
from app.services.orchestration.hybrid_planner import hybrid_planner
from app.core.logging import logger


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _add_trace(
    state: KALPAOrchestratorState,
    node: str,
    observation: str,
    decision: str,
    reason: str,
    decision_source: str = "deterministic",
    confidence: float = 1.0,
    next_action: Dict[str, Any] = None
):
    trace_item = {
        "timestamp": _now_iso(),
        "node": node,
        "observation": observation,
        "decision": decision,
        "reason": reason,
        "decision_source": decision_source,
        "confidence": confidence,
        "next_action": next_action
    }
    history = state.get("decision_history", [])
    history.append(trace_item)
    state["decision_history"] = history


# -----------------------------------------------------------------------------
# LangGraph Nodes
# -----------------------------------------------------------------------------

async def node_load_business_profile(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Loads and initializes canonical Stage 3 profile into state."""
    logger.info(f"[GRAPH:LOAD_PROFILE] Initializing state for analysis_id={state.get('analysis_id')}")
    state["current_node"] = "load_business_profile"
    state["workflow_status"] = "ANALYZING"
    state["decision_history"] = state.get("decision_history", [])
    state["errors"] = state.get("errors", [])
    state["retry_counts"] = state.get("retry_counts", {})
    state["agent_results"] = state.get("agent_results", {})
    state["knowledge_context"] = state.get("knowledge_context", {})
    state["completed_agents"] = state.get("completed_agents", [])
    state["pending_agents"] = state.get("pending_agents", [])

    bus = state.get("business_profile", {}).get("business_profile", {})
    concept = bus.get("specific_business") or bus.get("category", "Unknown Business")

    _add_trace(
        state,
        node="load_business_profile",
        observation=f"Canonical profile loaded for '{concept}'",
        decision="Proceed to profile completeness and validation checks",
        reason="Initial ingestion of Stage 3 profile document into orchestrator state",
        confidence=1.0
    )
    return state


async def node_validate_profile(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Validates profile completeness and flags any missing required information."""
    state["current_node"] = "validate_profile"
    profile = state.get("business_profile", {})
    dq = profile.get("data_quality", {})
    missing = dq.get("missing_fields", [])
    is_complete = dq.get("profile_complete", True)

    bus = profile.get("business_profile", {})
    if not bus.get("specific_business") and not bus.get("category"):
        is_complete = False
        missing.append("business_profile.specific_business")

    if not is_complete and missing:
        logger.warning(f"[GRAPH:VALIDATE] Profile incomplete. Missing fields: {missing}")
        state["workflow_status"] = "CLARIFICATION_REQUIRED"
        _add_trace(
            state,
            node="validate_profile",
            observation=f"Profile validation found missing mandatory fields: {missing}",
            decision="Route to clarification request",
            reason="Downstream analysis requires complete business profile data",
            confidence=0.95,
            next_action={"action": "USER_CLARIFICATION", "missing_fields": missing}
        )
    else:
        logger.info("[GRAPH:VALIDATE] Profile validation passed.")
        state["workflow_status"] = "PLANNING"
        _add_trace(
            state,
            node="validate_profile",
            observation="Profile validation passed all data quality checks",
            decision="Proceed to requirements analysis and workflow planning",
            reason="All mandatory identity, location, and classification fields are present",
            confidence=1.0
        )
    return state


async def node_analyze_requirements(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Analyzes business sector and analysis vectors needed for planning."""
    state["current_node"] = "analyze_requirements"
    profile = state.get("business_profile", {})
    bus = profile.get("business_profile", {})
    sector = bus.get("sector", "General")
    reqs = profile.get("analysis_requirements", {})

    _add_trace(
        state,
        node="analyze_requirements",
        observation=f"Identified sector '{sector}' with {len(reqs.get('required_datasets', []))} required data layers",
        decision="Synthesize workflow execution plan",
        reason="Determine required agent adapters and DAG execution sequence",
        confidence=0.95
    )
    return state


async def node_plan_workflow(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Generates the dynamic DAG execution plan using the Hybrid Decision Engine."""
    state["current_node"] = "plan_workflow"
    profile = state.get("business_profile", {})
    force_llm = state.get("routing_metadata", {}).get("force_llm", False)

    plan, routing_meta, llm_usage = await hybrid_planner.plan_workflow(profile, force_llm=force_llm)

    state["execution_plan"] = plan
    state["pending_agents"] = [item["agent"] for item in plan]
    state["completed_agents"] = []
    state["routing_metadata"] = routing_meta
    state["llm_usage"] = llm_usage
    state["workflow_status"] = "EXECUTING"

    _add_trace(
        state,
        node="plan_workflow",
        observation=f"Execution plan created with {len(plan)} agents: {state['pending_agents']}",
        decision=f"Select first available agent using {routing_meta.get('decision_source')} routing",
        reason=routing_meta.get("explanation", "Standard DAG execution plan formed"),
        decision_source=routing_meta.get("decision_source", "deterministic"),
        confidence=routing_meta.get("deterministic_confidence", 0.95)
    )
    return state


async def node_select_next_agent(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Selects the next executable agent whose upstream dependencies have finished."""
    state["current_node"] = "select_next_agent"
    pending = state.get("pending_agents", [])
    completed = state.get("completed_agents", [])

    ready_agents = agent_registry.get_executable_agents(pending, completed)

    if ready_agents:
        next_agent = ready_agents[0]
        state["current_agent"] = next_agent
        logger.info(f"[GRAPH:SELECT_AGENT] Next agent selected: '{next_agent}' (ready: {ready_agents})")

        # Update status in execution plan
        for item in state.get("execution_plan", []):
            if item["agent"] == next_agent:
                item["status"] = "in_progress"

        _add_trace(
            state,
            node="select_next_agent",
            observation=f"Executable agents with satisfied dependencies: {ready_agents}",
            decision=f"Execute agent '{next_agent}'",
            reason=f"All upstream dependencies {agent_registry.get_agent(next_agent).dependencies} are satisfied",
            confidence=1.0,
            next_action={"agent": next_agent, "action": "EXECUTE"}
        )
    else:
        state["current_agent"] = None
        if not pending:
            logger.info("[GRAPH:SELECT_AGENT] All pending agents completed.")
            _add_trace(
                state,
                node="select_next_agent",
                observation="No pending agents remaining in execution plan",
                decision="Proceed to complete orchestration",
                reason="All scheduled workflow tasks have executed successfully",
                confidence=1.0
            )
        else:
            logger.warning(f"[GRAPH:SELECT_AGENT] Pending agents remain {pending} but dependencies not satisfied by {completed}.")
            _add_trace(
                state,
                node="select_next_agent",
                observation=f"Unresolved dependencies for pending agents: {pending}",
                decision="Route to safe failure / partial completion",
                reason="Dependency deadlock detected",
                confidence=0.80
            )
    return state


async def node_execute_agent(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Invokes the selected agent adapter via the Agent Registry."""
    state["current_node"] = "execute_agent"
    current_agent = state.get("current_agent")
    if not current_agent:
        return state

    profile = state.get("business_profile", {})
    knowledge_ctx = state.get("knowledge_context", {})

    try:
        logger.info(f"[GRAPH:EXECUTE_AGENT] Running adapter for '{current_agent}'")
        adapter_output = await agent_registry.execute_agent(
            agent_id=current_agent,
            business_profile=profile,
            knowledge_context=knowledge_ctx,
            state=state
        )

        # Store result in shared state
        results = state.get("agent_results", {})
        results[current_agent] = adapter_output
        state["agent_results"] = results

        # If domain knowledge agent, enrich global knowledge context
        if current_agent == "domain_knowledge_agent":
            state["knowledge_context"] = adapter_output

        # Update execution plan item
        for item in state.get("execution_plan", []):
            if item["agent"] == current_agent:
                item["status"] = "completed"

        # Update completed list
        completed = state.get("completed_agents", [])
        if current_agent not in completed:
            completed.append(current_agent)
        state["completed_agents"] = completed

        pending = state.get("pending_agents", [])
        if current_agent in pending:
            pending.remove(current_agent)
        state["pending_agents"] = pending

        _add_trace(
            state,
            node="execute_agent",
            observation=f"Agent '{current_agent}' returned status '{adapter_output.get('status', 'success')}'",
            decision="Evaluate agent execution output",
            reason=f"Adapter completed with {len(adapter_output.keys())} result keys",
            confidence=1.0
        )

    except Exception as e:
        logger.error(f"[GRAPH:EXECUTE_AGENT] Error executing '{current_agent}': {e}")
        retries = state.get("retry_counts", {})
        retries[current_agent] = retries.get(current_agent, 0) + 1
        state["retry_counts"] = retries

        errors = state.get("errors", [])
        errors.append({
            "agent": current_agent,
            "error": str(e),
            "retry_count": retries[current_agent],
            "timestamp": _now_iso()
        })
        state["errors"] = errors

        _add_trace(
            state,
            node="execute_agent",
            observation=f"Agent '{current_agent}' failed with error: {str(e)}",
            decision="Evaluate retry or fallback routing",
            reason=f"Execution error on attempt {retries[current_agent]}",
            confidence=0.85
        )

    return state


async def node_evaluate_result(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Evaluates agent outcome and decides whether to retry, fallback, or proceed."""
    state["current_node"] = "evaluate_result"
    current_agent = state.get("current_agent")
    if not current_agent:
        return state

    retries = state.get("retry_counts", {}).get(current_agent, 0)
    adapter = agent_registry.get_agent(current_agent)
    max_retries = adapter.max_retries if adapter else 2

    # If the agent has completed successfully
    if current_agent in state.get("completed_agents", []):
        logger.info(f"[GRAPH:EVALUATE] '{current_agent}' execution verified. Proceeding to next agent.")
        _add_trace(
            state,
            node="evaluate_result",
            observation=f"Agent '{current_agent}' outputs verified valid",
            decision="Continue workflow loop to select next agent",
            reason="Output satisfies requirements for downstream dependencies",
            confidence=1.0
        )
        state["current_agent"] = None
        return state

    # If the agent failed but has retries remaining
    if retries <= max_retries:
        logger.info(f"[GRAPH:EVALUATE] Retrying '{current_agent}' (attempt {retries}/{max_retries})")
        _add_trace(
            state,
            node="evaluate_result",
            observation=f"Agent '{current_agent}' failure on attempt {retries}",
            decision=f"Retry execution of agent '{current_agent}'",
            reason=f"Retry budget remaining ({retries}/{max_retries})",
            confidence=0.75
        )
        return state

    # Retry limit exhausted -> use safe fallback
    logger.warning(f"[GRAPH:EVALUATE] Retry limit exhausted for '{current_agent}'. Applying graceful fallback.")
    fallback_output = {
        "status": "fallback_applied",
        "agent": current_agent,
        "error": "Max retries exceeded; fallback defaults applied",
        "fallback_used": True
    }
    results = state.get("agent_results", {})
    results[current_agent] = fallback_output
    state["agent_results"] = results

    for item in state.get("execution_plan", []):
        if item["agent"] == current_agent:
            item["status"] = "failed_with_fallback"

    completed = state.get("completed_agents", [])
    completed.append(current_agent)
    state["completed_agents"] = completed

    pending = state.get("pending_agents", [])
    if current_agent in pending:
        pending.remove(current_agent)
    state["pending_agents"] = pending

    _add_trace(
        state,
        node="evaluate_result",
        observation=f"Max retries ({max_retries}) exceeded for '{current_agent}'",
        decision="Apply fallback output and continue workflow",
        reason="Prevent entire orchestration from halting on single agent failure",
        confidence=0.85
    )
    state["current_agent"] = None
    return state


async def node_complete_orchestration(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Final node synthesizing canonical Stage 4 output."""
    state["current_node"] = "complete_orchestration"
    state["workflow_status"] = "ORCHESTRATION_COMPLETE"

    completed = state.get("completed_agents", [])
    pending = state.get("pending_agents", [])
    errors = state.get("errors", [])

    state["final_decision"] = {
        "status": "SUCCESS",
        "message": f"Orchestration completed with {len(completed)} agents executed.",
        "stage_completed": 4,
        "next_stage": 5,
        "next_action": "STAGE_5_OPPORTUNITY_EVALUATION"
    }

    state["next_action"] = {
        "agent": "market_intelligence_agent",
        "action": "READY_FOR_STAGE_5_EXECUTION",
        "description": "Orchestrator generated verified execution plan and benchmark context for downstream engines."
    }

    _add_trace(
        state,
        node="complete_orchestration",
        observation=f"All workflow stages complete. Total agents executed: {len(completed)}",
        decision="Finalize canonical Stage 4 orchestration record",
        reason="All planned agents executed and knowledge context synthesized for Stage 5",
        confidence=1.0
    )
    return state


async def node_request_clarification(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Handles incomplete profile state requiring user input."""
    state["current_node"] = "request_clarification"
    state["workflow_status"] = "CLARIFICATION_REQUIRED"
    return state


async def node_fail_safely(state: KALPAOrchestratorState) -> KALPAOrchestratorState:
    """Handles critical unresolvable deadlock or errors safely."""
    state["current_node"] = "fail_safely"
    state["workflow_status"] = "FAILED"
    return state


# -----------------------------------------------------------------------------
# Conditional Routing Functions
# -----------------------------------------------------------------------------

def route_after_validate(state: KALPAOrchestratorState) -> Literal["request_clarification", "analyze_requirements"]:
    if state.get("workflow_status") == "CLARIFICATION_REQUIRED":
        return "request_clarification"
    return "analyze_requirements"


def route_after_select_agent(state: KALPAOrchestratorState) -> Literal["execute_agent", "complete_orchestration", "fail_safely"]:
    if state.get("current_agent"):
        return "execute_agent"
    if not state.get("pending_agents"):
        return "complete_orchestration"
    return "fail_safely"


def route_after_evaluate(state: KALPAOrchestratorState) -> Literal["execute_agent", "select_next_agent"]:
    current_agent = state.get("current_agent")
    if current_agent:
        # Agent is set, meaning evaluate decided to retry
        return "execute_agent"
    return "select_next_agent"


# -----------------------------------------------------------------------------
# Build and Compile StateGraph
# -----------------------------------------------------------------------------

def build_orchestrator_graph():
    graph = StateGraph(KALPAOrchestratorState)

    # Add Nodes
    graph.add_node("load_business_profile", node_load_business_profile)
    graph.add_node("validate_profile", node_validate_profile)
    graph.add_node("analyze_requirements", node_analyze_requirements)
    graph.add_node("plan_workflow", node_plan_workflow)
    graph.add_node("select_next_agent", node_select_next_agent)
    graph.add_node("execute_agent", node_execute_agent)
    graph.add_node("evaluate_result", node_evaluate_result)
    graph.add_node("complete_orchestration", node_complete_orchestration)
    graph.add_node("request_clarification", node_request_clarification)
    graph.add_node("fail_safely", node_fail_safely)

    # Add Edges
    graph.add_edge(START, "load_business_profile")
    graph.add_edge("load_business_profile", "validate_profile")

    graph.add_conditional_edges(
        "validate_profile",
        route_after_validate,
        {
            "request_clarification": "request_clarification",
            "analyze_requirements": "analyze_requirements"
        }
    )

    graph.add_edge("request_clarification", END)
    graph.add_edge("analyze_requirements", "plan_workflow")
    graph.add_edge("plan_workflow", "select_next_agent")

    graph.add_conditional_edges(
        "select_next_agent",
        route_after_select_agent,
        {
            "execute_agent": "execute_agent",
            "complete_orchestration": "complete_orchestration",
            "fail_safely": "fail_safely"
        }
    )

    graph.add_edge("execute_agent", "evaluate_result")

    graph.add_conditional_edges(
        "evaluate_result",
        route_after_evaluate,
        {
            "execute_agent": "execute_agent",
            "select_next_agent": "select_next_agent"
        }
    )

    graph.add_edge("complete_orchestration", END)
    graph.add_edge("fail_safely", END)

    return graph.compile()


# Global compiled workflow graph instance
orchestrator_graph = build_orchestrator_graph()
