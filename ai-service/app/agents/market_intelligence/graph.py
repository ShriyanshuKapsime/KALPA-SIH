"""
LangGraph StateGraph Workflow Engine for Stage 5 Market Intelligence Agent.
Implements the 12-node autonomous evidence retrieval and validation cycle:
START -> load_business_profile -> resolve_location -> load_market_knowledge_pack
-> determine_market_requirements -> create_collection_plan -> validate_collection_plan
-> execute_tools -> validate_evidence -> retry_failed_tools -> check_evidence_completeness
-> assemble_market_evidence -> validate_market_evidence_profile -> persist_evidence -> END
"""
import uuid
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, START, END

from app.schemas.market import (
    MarketEvidenceProfile,
    CanonicalBusinessContext,
    LocationContext,
    CollectionPlan,
    MarketExecutionContext,
    MarketEvidenceAggregate,
    DemographicEvidenceItem,
    CompetitorEvidenceContainer,
    CompetitorEvidenceItem,
    DemandIndicatorItem,
    SupplyAccessItem,
    InfrastructureItem,
    EconomicIndicatorItem,
    SeasonalityEvidenceItem,
    DemandPredictionAdapterResult,
    EvidenceQuality,
    EvidenceGapItem,
    ExecutionMetadata,
    ProvenanceContainer,
    ProvenanceItem,
    WorkflowSection,
)
from app.services.market.location_resolver import location_resolver
from app.knowledge.services.knowledge_service import KnowledgeService
from app.agents.market_intelligence.planner import market_requirement_planner
from app.agents.market_intelligence.tools.base_tool import ToolExecutionContext, ToolResult
from app.agents.market_intelligence.tools.tool_registry import market_tool_registry
from app.agents.market_intelligence.execution.tool_runner import tool_execution_engine
from app.agents.market_intelligence.scoring import evidence_quality_scorer
from app.agents.market_intelligence.context_normalizer import context_normalizer
from app.agents.market_intelligence.integrity_gate import integrity_gate
from app.agents.market_intelligence.execution.caching import market_cache
from app.database.session import get_db_context
from app.database.models.market import MarketEvidenceRecord
from app.core.logging import logger


class MarketAgentState(TypedDict, total=False):
    analysis_id: str
    session_id: str
    user_id: Optional[str]

    # Normalized Canonical Business & Raw Profile
    business_profile: Dict[str, Any]
    canonical_business: Dict[str, Any]

    # Stage 5 Runtime State
    location_context: Dict[str, Any]
    knowledge_pack: Dict[str, Any]
    collection_plan: Dict[str, Any]

    tool_results: Dict[str, Any]
    market_evidence: Dict[str, Any]
    evidence_quality: Dict[str, Any]
    evidence_gaps: List[Dict[str, Any]]
    execution_metadata: Dict[str, Any]
    provenance: Dict[str, Any]

    workflow_status: str
    current_node: str
    errors: List[Dict[str, Any]]
    force_llm: bool
    force_refresh: bool
    context_integrity_passed: bool
    contamination_detected: bool

    # Final Output Document
    final_evidence_profile: Dict[str, Any]


# -----------------------------------------------------------------------------
# LangGraph Workflow Nodes
# -----------------------------------------------------------------------------

async def node_load_business_profile(state: MarketAgentState) -> MarketAgentState:
    analysis_id = state.get("analysis_id", str(uuid.uuid4()))
    session_id = state.get("session_id", str(uuid.uuid4()))
    logger.info(f"[STAGE 5 GRAPH] Normalizing business profile for analysis_id={analysis_id}")
    state["current_node"] = "load_business_profile"
    state["workflow_status"] = "MARKET_EVIDENCE_COLLECTING"
    state["errors"] = state.get("errors", [])

    raw_profile = state.get("business_profile") or {}
    canonical = context_normalizer.normalize(raw_profile, analysis_id=analysis_id, session_id=session_id)
    state["canonical_business"] = canonical.model_dump()

    # Context integrity gate check
    valid, err_msg = integrity_gate.validate_business_context(canonical)
    state["context_integrity_passed"] = valid
    if not valid:
        logger.error(f"[STAGE 5 GRAPH] Context validation failed: {err_msg}")
        state["errors"].append({"node": "load_business_profile", "error": err_msg})

    return state


async def node_resolve_location(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Resolving canonical location hierarchy & spatial conflict detection")
    state["current_node"] = "resolve_location"
    profile = state.get("business_profile", {})
    loc_sec = profile.get("location_profile", {})

    loc_context = await location_resolver.resolve_location(loc_sec)
    state["location_context"] = loc_context.model_dump()
    return state


async def node_load_market_knowledge_pack(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Querying Stage 4.5 Domain Knowledge Hub with canonical business ID")
    state["current_node"] = "load_market_knowledge_pack"
    canonical = state.get("canonical_business", {})
    business_id = canonical.get("business_id", "general")

    ks = KnowledgeService()
    pack = ks.get_market_context(business_id)
    state["knowledge_pack"] = pack.model_dump()
    return state


async def node_determine_market_requirements(state: MarketAgentState) -> MarketAgentState:
    state["current_node"] = "determine_market_requirements"
    return state


async def node_create_collection_plan(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Creating hybrid evidence collection plan with business isolation")
    state["current_node"] = "create_collection_plan"
    canonical = CanonicalBusinessContext(**state.get("canonical_business", {}))
    pack = state.get("knowledge_pack", {})
    loc_prof = state.get("business_profile", {}).get("location_profile")
    force_llm = state.get("force_llm", False)

    plan, llm_used, llm_fallback = await market_requirement_planner.plan_collection(
        canonical, pack, location_profile=loc_prof, force_llm=force_llm
    )

    state["collection_plan"] = plan.model_dump()
    exec_meta = state.get("execution_metadata", {})
    exec_meta["llm_used"] = llm_used
    exec_meta["llm_fallback_used"] = llm_fallback
    if hasattr(market_requirement_planner, "last_telemetry") and market_requirement_planner.last_telemetry:
        exec_meta.update(market_requirement_planner.last_telemetry)
    state["execution_metadata"] = exec_meta
    return state


async def node_validate_collection_plan(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Validating collection plan against registered tools & checking semantic contamination")
    state["current_node"] = "validate_collection_plan"
    plan_dict = state.get("collection_plan", {})
    selected = plan_dict.get("selected_tools", [])
    valid_names = set(market_tool_registry.list_tool_names())

    # Constrain to registered tools
    sanitized = [t for t in selected if t in valid_names]
    plan_dict["selected_tools"] = sanitized
    state["collection_plan"] = plan_dict

    # Check semantic contamination
    plan_obj = CollectionPlan(**plan_dict)
    canonical = state.get("canonical_business", {})
    b_id = canonical.get("business_id", "general")

    is_clean, contam_err = integrity_gate.check_semantic_contamination(b_id, plan_obj)
    if not is_clean:
        state["contamination_detected"] = True
        state["errors"].append({"node": "validate_collection_plan", "error": contam_err})
    else:
        state["contamination_detected"] = False

    return state


async def node_execute_tools(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Executing market tool suite concurrently with cache isolation")
    state["current_node"] = "execute_tools"
    plan_dict = state.get("collection_plan", {})
    selected_tools = plan_dict.get("selected_tools", [])

    canonical = CanonicalBusinessContext(**state.get("canonical_business", {}))
    # Purge any contaminated saree cache entries if current request is non-saree (Task 8)
    market_cache.invalidate_contaminated_saree_cache(canonical.business_id)

    location_ctx = LocationContext(**state.get("location_context", {}))
    requirements = plan_dict.get("requirements", [])
    force_refresh = state.get("force_refresh", False)

    context = MarketExecutionContext(
        analysis_id=state.get("analysis_id", str(uuid.uuid4())),
        session_id=state.get("session_id", str(uuid.uuid4())),
        business=canonical,
        location=location_ctx,
        requirements=requirements,
        knowledge_context=state.get("knowledge_pack", {}),
        execution_mode="live",
        force_refresh=force_refresh
    )

    exec_result = await tool_execution_engine.run_plan(selected_tools, context)

    # Store raw tool results
    tool_results_dict = {}
    for name, res in exec_result["results"].items():
        tool_results_dict[name] = res.model_dump()

    state["tool_results"] = tool_results_dict

    exec_meta = state.get("execution_metadata", {})
    exec_meta.update(exec_result["metadata"])
    state["execution_metadata"] = exec_meta
    return state


async def node_validate_evidence(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Validating and structuring retrieved raw evidence")
    state["current_node"] = "validate_evidence"
    tool_res = state.get("tool_results", {})

    demographics_items: List[DemographicEvidenceItem] = []
    comp_container = CompetitorEvidenceContainer()
    demand_items: List[DemandIndicatorItem] = []
    supply_items: List[SupplyAccessItem] = []
    infra_items: List[InfrastructureItem] = []
    econ_items: List[EconomicIndicatorItem] = []
    season_items: List[SeasonalityEvidenceItem] = []
    demand_pred = DemandPredictionAdapterResult()
    provenance_sources: List[ProvenanceItem] = []

    # 1. Demographics
    demo_res = tool_res.get("demographics_tool", {})
    if demo_res and "metrics" in demo_res:
        for m in demo_res["metrics"]:
            demographics_items.append(DemographicEvidenceItem(**m))
        if demo_res.get("source"):
            provenance_sources.append(ProvenanceItem(**demo_res["source"]))

    # 2. Competitors
    comp_res = tool_res.get("competitor_discovery_tool", {})
    if comp_res and "data" in comp_res:
        cdata = comp_res["data"]
        for d in cdata.get("direct_competitors", []):
            comp_container.direct.append(CompetitorEvidenceItem(**d))
        for a in cdata.get("adjacent_competitors", []):
            comp_container.adjacent.append(CompetitorEvidenceItem(**a))
        for s in cdata.get("substitute_competitors", []):
            comp_container.substitutes.append(CompetitorEvidenceItem(**s))
        comp_container.total_found = cdata.get("total_competitors_found", len(comp_container.direct))
        if comp_res.get("source"):
            provenance_sources.append(ProvenanceItem(**comp_res["source"]))
    elif comp_res and comp_res.get("status") == "failed":
        comp_container.status = "failed"
        comp_container.error = comp_res.get("error_message") or "Tool execution failed"

    # 3. Demand Indicators
    demand_res = tool_res.get("demand_evidence_tool", {})
    if demand_res and "data" in demand_res:
        for di in demand_res["data"].get("demand_indicators", []):
            demand_items.append(DemandIndicatorItem(**di))
        if demand_res.get("source"):
            provenance_sources.append(ProvenanceItem(**demand_res["source"]))

    # 4. Supply Access
    supply_res = tool_res.get("supply_access_tool", {})
    if supply_res and "data" in supply_res:
        for si in supply_res["data"].get("supply_hubs", []):
            supply_items.append(SupplyAccessItem(**si))
        if supply_res.get("source"):
            provenance_sources.append(ProvenanceItem(**supply_res["source"]))

    # 5. Infrastructure
    infra_res = tool_res.get("infrastructure_access_tool", {})
    if infra_res and "data" in infra_res:
        for ii in infra_res["data"].get("infrastructure_evidence", []):
            infra_items.append(InfrastructureItem(**ii))
        if infra_res.get("source"):
            provenance_sources.append(ProvenanceItem(**infra_res["source"]))

    # 6. Economic Purchasing Power
    econ_res = tool_res.get("economic_purchasing_power_tool", {})
    if econ_res and "data" in econ_res:
        for ei in econ_res["data"].get("economic_indicators", []):
            econ_items.append(EconomicIndicatorItem(**ei))
        if econ_res.get("source"):
            provenance_sources.append(ProvenanceItem(**econ_res["source"]))

    # 7. Seasonality & Knowledge
    kh_res = tool_res.get("knowledge_hub_tool", {})
    if kh_res and "data" in kh_res:
        for se in kh_res["data"].get("seasonality_evidence", []):
            season_items.append(SeasonalityEvidenceItem(**se))

    # 8. Demand Prediction
    dp_res = tool_res.get("demand_prediction_adapter", {})
    if dp_res and "data" in dp_res and "demand_prediction" in dp_res["data"]:
        demand_pred = DemandPredictionAdapterResult(**dp_res["data"]["demand_prediction"])

    aggregate = MarketEvidenceAggregate(
        demographics=demographics_items,
        competitors=comp_container,
        demand_indicators=demand_items,
        supply_access=supply_items,
        infrastructure=infra_items,
        economic_indicators=econ_items,
        seasonality_evidence=season_items,
        demand_prediction=demand_pred
    )

    state["market_evidence"] = aggregate.model_dump()
    state["provenance"] = ProvenanceContainer(sources=provenance_sources).model_dump()
    return state


async def node_retry_failed_tools(state: MarketAgentState) -> MarketAgentState:
    state["current_node"] = "retry_failed_tools"
    return state


async def node_check_evidence_completeness(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Computing explainable evidence quality score with hard penalties")
    state["current_node"] = "check_evidence_completeness"

    evidence_dict = state.get("market_evidence", {})
    evidence = MarketEvidenceAggregate(**evidence_dict)
    location = LocationContext(**state.get("location_context", {}))
    plan = CollectionPlan(**state.get("collection_plan", {}))
    canonical = CanonicalBusinessContext(**state.get("canonical_business", {}))

    exec_meta = state.get("execution_metadata", {})
    succ = exec_meta.get("successful_tools", [])
    fail = exec_meta.get("failed_tools", [])

    integrity_passed = state.get("context_integrity_passed", True)
    contam = state.get("contamination_detected", False)

    quality = evidence_quality_scorer.evaluate(
        evidence, location, plan, succ, fail,
        business=canonical,
        context_integrity_passed=integrity_passed,
        contamination_detected=contam
    )
    state["evidence_quality"] = quality.model_dump()

    # Formulate evidence gaps
    gaps: List[EvidenceGapItem] = []
    if quality.missing_requirements:
        for req in quality.missing_requirements:
            gaps.append(
                EvidenceGapItem(
                    requirement=req,
                    reason=f"Hyper-local data indicator for {req} not available in open catalogs.",
                    severity="warning",
                    recommended_action="Execute field surveyor intake or trigger dynamic API pull."
                )
            )

    if not evidence.demand_prediction.available:
        gaps.append(
            EvidenceGapItem(
                requirement="ml_demand_forecast",
                reason="Demand prediction ML model service is offline.",
                severity="info",
                recommended_action="Connect demand prediction ML model service to Stage 5 adapter."
            )
        )

    state["evidence_gaps"] = [g.model_dump() for g in gaps]
    return state


async def node_assemble_market_evidence(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Assembling canonical MarketEvidenceProfile")
    state["current_node"] = "assemble_market_evidence"

    profile = MarketEvidenceProfile(
        schema_version="1.0",
        analysis_id=state.get("analysis_id", str(uuid.uuid4())),
        session_id=state.get("session_id", str(uuid.uuid4())),
        workflow=WorkflowSection(
            stage=5,
            state="MARKET_EVIDENCE_COLLECTED",
            status="complete" if not state.get("errors") else "partial"
        ),
        business_context=CanonicalBusinessContext(**state.get("canonical_business", {})),
        location_context=LocationContext(**state.get("location_context", {})),
        collection_plan=CollectionPlan(**state.get("collection_plan", {})),
        market_evidence=MarketEvidenceAggregate(**state.get("market_evidence", {})),
        evidence_quality=EvidenceQuality(**state.get("evidence_quality", {})),
        evidence_gaps=[EvidenceGapItem(**g) for g in state.get("evidence_gaps", [])],
        execution_metadata=ExecutionMetadata(**state.get("execution_metadata", {})),
        provenance=ProvenanceContainer(**state.get("provenance", {}))
    )

    state["final_evidence_profile"] = profile.model_dump()
    state["workflow_status"] = "MARKET_EVIDENCE_READY"
    return state


async def node_validate_market_evidence_profile(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Running post-execution validation gate on assembled profile")
    state["current_node"] = "validate_market_evidence_profile"

    final_dict = state.get("final_evidence_profile", {})
    profile = MarketEvidenceProfile(**final_dict)

    is_valid, validation_errors = integrity_gate.validate_market_evidence_profile(profile)
    if not is_valid:
        profile.workflow.state = "MARKET_EVIDENCE_VALIDATION_FAILED"
        profile.workflow.status = "failed"
        state["workflow_status"] = "MARKET_EVIDENCE_VALIDATION_FAILED"
        state["final_evidence_profile"] = profile.model_dump()
        state["errors"].extend([{"node": "validate_market_evidence_profile", "error": e} for e in validation_errors])

    return state


async def node_persist_evidence(state: MarketAgentState) -> MarketAgentState:
    logger.info("[STAGE 5 GRAPH] Persisting MarketEvidenceRecord to database")
    state["current_node"] = "persist_evidence"

    if state.get("workflow_status") == "MARKET_EVIDENCE_VALIDATION_FAILED":
        logger.warning("[STAGE 5 PERSIST] Skipping database persistence due to validation failure.")
        return state

    try:
        final_doc = state.get("final_evidence_profile", {})
        analysis_uuid = uuid.UUID(state.get("analysis_id")) if state.get("analysis_id") else uuid.uuid4()
        session_uuid = uuid.UUID(state.get("session_id")) if state.get("session_id") else uuid.uuid4()
        user_uuid = uuid.UUID(state.get("user_id")) if state.get("user_id") else None

        with get_db_context() as db:
            if db:
                existing = db.query(MarketEvidenceRecord).filter(MarketEvidenceRecord.id == analysis_uuid).first()
                if existing:
                    existing.session_id = session_uuid
                    existing.user_id = user_uuid
                    existing.schema_version = "1.0"
                    existing.workflow_status = "MARKET_EVIDENCE_COLLECTED"
                    existing.geographic_precision = final_doc.get("location_context", {}).get("geographic_precision", "district")
                    existing.overall_quality_score = final_doc.get("evidence_quality", {}).get("overall_quality", 0.0)
                    existing.location_context = final_doc.get("location_context", {})
                    existing.collection_plan = final_doc.get("collection_plan", {})
                    existing.market_evidence = final_doc.get("market_evidence", {})
                    existing.evidence_quality = final_doc.get("evidence_quality", {})
                    existing.evidence_gaps = final_doc.get("evidence_gaps", [])
                    existing.execution_metadata = final_doc.get("execution_metadata", {})
                    existing.provenance = final_doc.get("provenance", {})
                    existing.full_profile = final_doc
                    db.commit()
                    logger.info(f"[STAGE 5 PERSIST] Updated existing MarketEvidenceRecord {analysis_uuid}.")
                else:
                    record = MarketEvidenceRecord(
                        id=analysis_uuid,
                        session_id=session_uuid,
                        user_id=user_uuid,
                        schema_version="1.0",
                        workflow_status="MARKET_EVIDENCE_COLLECTED",
                        geographic_precision=final_doc.get("location_context", {}).get("geographic_precision", "district"),
                        overall_quality_score=final_doc.get("evidence_quality", {}).get("overall_quality", 0.0),
                        location_context=final_doc.get("location_context", {}),
                        collection_plan=final_doc.get("collection_plan", {}),
                        market_evidence=final_doc.get("market_evidence", {}),
                        evidence_quality=final_doc.get("evidence_quality", {}),
                        evidence_gaps=final_doc.get("evidence_gaps", []),
                        execution_metadata=final_doc.get("execution_metadata", {}),
                        provenance=final_doc.get("provenance", {}),
                        full_profile=final_doc
                    )
                    db.add(record)
                    db.commit()
                    logger.info(f"[STAGE 5 PERSIST] Inserted new MarketEvidenceRecord {analysis_uuid}.")
    except Exception as e:
        logger.error(f"[STAGE 5 PERSIST ERROR] Database persistence error for {state.get('analysis_id')}: {e}")

    return state


# -----------------------------------------------------------------------------
# LangGraph Workflow Construction
# -----------------------------------------------------------------------------

def build_market_intelligence_graph() -> Any:
    workflow = StateGraph(MarketAgentState)

    workflow.add_node("load_business_profile", node_load_business_profile)
    workflow.add_node("resolve_location", node_resolve_location)
    workflow.add_node("load_market_knowledge_pack", node_load_market_knowledge_pack)
    workflow.add_node("determine_market_requirements", node_determine_market_requirements)
    workflow.add_node("create_collection_plan", node_create_collection_plan)
    workflow.add_node("validate_collection_plan", node_validate_collection_plan)
    workflow.add_node("execute_tools", node_execute_tools)
    workflow.add_node("validate_evidence", node_validate_evidence)
    workflow.add_node("retry_failed_tools", node_retry_failed_tools)
    workflow.add_node("check_evidence_completeness", node_check_evidence_completeness)
    workflow.add_node("assemble_market_evidence", node_assemble_market_evidence)
    workflow.add_node("validate_market_evidence_profile", node_validate_market_evidence_profile)
    workflow.add_node("persist_evidence", node_persist_evidence)

    # Edge connections
    workflow.add_edge(START, "load_business_profile")
    workflow.add_edge("load_business_profile", "resolve_location")
    workflow.add_edge("resolve_location", "load_market_knowledge_pack")
    workflow.add_edge("load_market_knowledge_pack", "determine_market_requirements")
    workflow.add_edge("determine_market_requirements", "create_collection_plan")
    workflow.add_edge("create_collection_plan", "validate_collection_plan")
    workflow.add_edge("validate_collection_plan", "execute_tools")
    workflow.add_edge("execute_tools", "validate_evidence")
    workflow.add_edge("validate_evidence", "retry_failed_tools")
    workflow.add_edge("retry_failed_tools", "check_evidence_completeness")
    workflow.add_edge("check_evidence_completeness", "assemble_market_evidence")
    workflow.add_edge("assemble_market_evidence", "validate_market_evidence_profile")
    workflow.add_edge("validate_market_evidence_profile", "persist_evidence")
    workflow.add_edge("persist_evidence", END)

    return workflow.compile()


market_intelligence_graph = build_market_intelligence_graph()
