"""
KALPA DPR API Router: Stage 1 (Intake, Gap Discovery & Overrides) and Stage 14 (DPR Generator).
Exposes REST endpoints for DPR context assembly, 39-section gap analysis, interactive questioning,
benchmark reviews, scenario recalculations, and report downloads.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.engines.dpr.schemas import DPRDocumentRequest, DPRDocumentMetadata
from app.engines.dpr.service import dpr_generation_engine, REPORTS_DIR
from app.services.dpr_stage1 import (
    dpr_context_builder,
    dpr_gap_analyzer,
    dpr_question_engine,
    dpr_answer_resolver,
    dpr_scenario_manager,
    build_stage1_handoff_package,
    build_stage14_handoff_package,
    get_field_definition,
    DPRQuestion,
)
from app.services.dpr_stage1.dpr_registry import DPR_STATE_ISOLATION_ERROR
from app.dpr.stage14_3.document_schema import DPR_FINANCIAL_RECONCILIATION_FAILED
from app.services.dpr_stage2 import dpr_enrichment_service
from app.services.sarvam_service import sarvam_stt_service, sarvam_tts_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dpr", tags=["Stage 14: DPR Intake, Enrichment & Generation"])


def _log_dpr_state_trace(
    route: str,
    business_id: str,
    scenario_id: Optional[str] = None,
    intake_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    b_id = (business_id or "").strip()
    s_id = scenario_id.strip() if scenario_id else f"DPR-{b_id[:8] if len(b_id) >= 8 else b_id}"
    logger.info(
        f"[DPR_STATE_TRACE]\n"
        f"route: {route}\n"
        f"business_id: {b_id}\n"
        f"scenario_id: {s_id}\n"
        f"intake_id: {intake_id or 'none'}\n"
        f"session_id: {session_id or 'none'}\n"
        f"context_key: dpr_context:{b_id}:{s_id}\n"
        f"enrichment_key: dpr_enrichment:{b_id}:{s_id}\n"
        f"financial_package_key: fin:{b_id}"
    )


def _log_dpr_context_debug(
    requested_business_id: str,
    requested_scenario_id: Optional[str],
    resolved_business_id: str,
    resolved_scenario_id: str,
    existing_scenario_id: Optional[str] = None,
    scenario_exists: bool = False,
    scenario_business_id: Optional[str] = None,
    context_exists: bool = False,
    context_business_id: Optional[str] = None,
    context_scenario_id: Optional[str] = None,
    conflict_reason: Optional[str] = None,
):
    logger.info(
        f"[DPR_CONTEXT_DEBUG]\n"
        f"requested_business_id={requested_business_id}\n"
        f"requested_scenario_id={requested_scenario_id or 'none'}\n"
        f"resolved_business_id={resolved_business_id}\n"
        f"resolved_scenario_id={resolved_scenario_id}\n"
        f"existing_scenario_id={existing_scenario_id or 'none'}\n"
        f"scenario_exists={scenario_exists}\n"
        f"scenario_business_id={scenario_business_id or 'none'}\n"
        f"context_exists={context_exists}\n"
        f"context_business_id={context_business_id or 'none'}\n"
        f"context_scenario_id={context_scenario_id or 'none'}\n"
        f"conflict_reason={conflict_reason or 'none'}"
    )


def _log_dpr_identity(
    business_id: str,
    scenario_id: str,
    business_name: Optional[str] = None,
    intake_id: Optional[str] = None,
    session_id: Optional[str] = None,
    source: str = "api",
):
    logger.info(
        f"[DPR_IDENTITY]\n"
        f"business_id={business_id}\n"
        f"scenario_id={scenario_id}\n"
        f"business_name={business_name or business_id}\n"
        f"intake_id={intake_id or 'none'}\n"
        f"session_id={session_id or 'none'}\n"
        f"source={source}"
    )


def _assert_state_isolation(
    business_id: str,
    package_business_id: Optional[str],
    scenario_id: Optional[str] = None,
    package_scenario_id: Optional[str] = None,
):
    b_id = (business_id or "").strip()
    pkg_b_id = (package_business_id or "").strip() if package_business_id else None
    if pkg_b_id and pkg_b_id.lower() != b_id.lower():
        raise HTTPException(
            status_code=409,
            detail=f"DPR_STATE_ISOLATION_ERROR: requested_business_id={business_id} returned_business_id={package_business_id}"
        )
    if scenario_id and package_scenario_id:
        s_id = scenario_id.strip()
        pkg_s_id = package_scenario_id.strip()
        if pkg_s_id.lower() != s_id.lower():
            raise HTTPException(
                status_code=409,
                detail=f"DPR_STATE_ISOLATION_ERROR: requested_scenario_id={scenario_id} returned_scenario_id={package_scenario_id}"
            )


# ============================================================================
# DPR SCENARIO & SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/14.1/scenario/fresh/{business_id}")
@router.post("/new-scenario/{business_id}")
async def create_new_dpr_scenario(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Explicitly starts a fresh DPR assessment with a unique collision-safe scenario_id (e.g. DPR-{business_id}-iter-{uid}),
    empty answers/overrides/benchmarks, fresh 14.1 context, and gap analysis.
    Inherits authoritative upstream Stage 1–13 outputs without copying old DPR iteration state.
    """
    try:
        b_id = (business_id or "").strip()
        if not b_id:
            raise HTTPException(status_code=400, detail="business_id is required")

        req_scen_id = payload.get("scenario_id") if payload else None
        req_journey_id = payload.get("source_journey_id") if payload else None
        req_upstream = payload.get("upstream_context") if payload else None

        new_state = dpr_scenario_manager.create_fresh_dpr_scenario(
            business_id=b_id,
            upstream_context=req_upstream,
            source_journey_id=req_journey_id,
            scenario_id=req_scen_id
        )
        s_id = new_state.scenario_id
        
        # Unique intake / session id for this fresh scenario
        intake_session_id = (payload.get("session_id") if payload else None) or f"intake-{s_id.lower()}"
        
        _log_dpr_state_trace(f"/dpr/new-scenario/{b_id}", b_id, s_id, intake_id=intake_session_id, session_id=intake_session_id)
        
        return {
            "business_id": b_id,
            "scenario_id": s_id,
            "dpr_iteration_id": new_state.dpr_iteration_id or s_id,
            "source_journey_id": new_state.source_journey_id,
            "intake_id": intake_session_id,
            "session_id": intake_session_id,
            "created_at": new_state.created_at,
            "version": new_state.version,
            "status": new_state.status,
            "fresh_dpr_iteration": True,
            "message": "Fresh DPR scenario initialized. Upstream facts inherited; DPR answers reset."
        }
    except Exception as e:
        logger.error(f"[DPR Session] Failed to create new scenario for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create new DPR scenario: {str(e)}")


async def _build_lineage_response(b_id: str, active_s_id: Optional[str], db: Session) -> Dict[str, Any]:
    scenario = dpr_scenario_manager.get_or_create_scenario(b_id, active_s_id)
    ctx = await dpr_context_builder.build_context(
        business_id=b_id,
        db=db,
        scenario_id=scenario.scenario_id,
        user_overrides=scenario.user_overrides,
        user_answers=scenario.user_answers,
        document_statuses=scenario.document_statuses
    )
    fields_dict = ctx.get("fields") or {}
    lineage_records: Dict[str, Any] = {}
    for fid, fdata in fields_dict.items():
        if isinstance(fdata, dict):
            lineage_records[fid] = {
                "field": fid,
                "value": fdata.get("value"),
                "status": fdata.get("status"),
                "source": fdata.get("source_type") or fdata.get("source"),
                "source_stage": fdata.get("source_stage"),
                "source_module": fdata.get("source_module"),
                "source_path": fdata.get("source_path"),
                "raw_value": fdata.get("raw_value", fdata.get("value")),
                "raw_type": fdata.get("raw_type", type(fdata.get("value")).__name__),
                "canonical_type": fdata.get("canonical_type", "string"),
                "canonical_enum": fdata.get("canonical_enum"),
                "display_label": fdata.get("display_label"),
                "normalization_method": fdata.get("resolution_method") or fdata.get("normalization_method"),
                "question_suppressed": fdata.get("question_suppressed", str(fdata.get("status", "")).startswith("RESOLVED_") or fdata.get("status") in ("NOT_APPLICABLE", "DERIVED"))
            }

    return {
        "business_id": b_id,
        "scenario_id": scenario.scenario_id,
        "dpr_iteration_id": scenario.dpr_iteration_id or scenario.scenario_id,
        "source_journey_id": scenario.source_journey_id,
        "fresh_dpr_iteration": bool(scenario.dpr_iteration_id or "-iter-" in scenario.scenario_id),
        "total_fields": len(lineage_records),
        "resolved_upstream_count": sum(1 for r in lineage_records.values() if r["question_suppressed"]),
        "fields": lineage_records
    }


@router.get("/14.1/lineage/{business_id}")
async def get_dpr_14_1_lineage(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Authoritative Data Lineage Diagnostic Endpoint.
    Exposes complete provenance for every canonical field across Stage 1–13 sources.
    """
    b_id = (business_id or "").strip()
    active_s_id = (scenario_id or "").strip() or None
    try:
        return await _build_lineage_response(b_id, active_s_id, db)
    except Exception as e:
        logger.error(f"[DPR Lineage] Error retrieving lineage for {b_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DPR lineage: {str(e)}")


@router.get("/14.1/lineage/{business_id}/{scenario_id}")
async def get_dpr_14_1_lineage_by_scenario(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: str = Path(..., description="Target scenario identifier"),
    db: Session = Depends(get_db)
):
    """
    Authoritative Data Lineage Diagnostic Endpoint by Scenario ID.
    """
    b_id = (business_id or "").strip()
    active_s_id = (scenario_id or "").strip()
    try:
        return await _build_lineage_response(b_id, active_s_id, db)
    except Exception as e:
        logger.error(f"[DPR Lineage] Error retrieving lineage for {b_id}/{scenario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DPR lineage: {str(e)}")


# ============================================================================
# STAGE 1: DPR CONTEXT & GAP ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/context/{business_id}")
async def get_dpr_context(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Retrieves the canonical DPRContextPackage assembled from all upstream stages (3–13),
    benchmarks, policy engines, and user overrides across all 8 modules and 39 sections.
    """
    b_id = business_id.strip()
    s_id = scenario_id.strip() if scenario_id else None
    resolved_scen = s_id or f"DPR-{b_id[:8] if len(b_id) >= 8 else b_id}"
    _log_dpr_identity(b_id, resolved_scen, source="/dpr/context")

    # Mismatch protection
    if s_id and s_id.startswith("DPR-"):
        clean_biz = b_id.replace("-", "").replace("_", "")[:5].lower()
        clean_scen = s_id.replace("DPR-", "").replace("-", "").replace("_", "")[:5].lower()
        if clean_biz and clean_scen and len(clean_scen) >= 4 and len(clean_biz) >= 4:
            if not clean_biz.startswith(clean_scen[:3]) and not clean_scen.startswith(clean_biz[:3]):
                conflict_reason = f"Scenario '{s_id}' does not belong to business '{b_id}'"
                _log_dpr_context_debug(
                    requested_business_id=b_id,
                    requested_scenario_id=s_id,
                    resolved_business_id=b_id,
                    resolved_scenario_id=resolved_scen,
                    conflict_reason=conflict_reason
                )
                raise HTTPException(status_code=409, detail=f"DPR_STATE_ISOLATION_ERROR: {conflict_reason}")

    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(b_id, s_id)
        _log_dpr_state_trace(f"/dpr/context/{b_id}", b_id, scenario.scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=b_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        _assert_state_isolation(b_id, ctx.get("business_id"), s_id, ctx.get("scenario_id"))
        _log_dpr_context_debug(
            requested_business_id=b_id,
            requested_scenario_id=s_id,
            resolved_business_id=b_id,
            resolved_scenario_id=scenario.scenario_id,
            existing_scenario_id=scenario.scenario_id,
            scenario_exists=True,
            scenario_business_id=scenario.business_id,
            context_exists=True,
            context_business_id=ctx.get("business_id"),
            context_scenario_id=ctx.get("scenario_id"),
            conflict_reason=None
        )
        return ctx
    except HTTPException:
        raise
    except Exception as e:
        conflict_msg = str(e)
        _log_dpr_context_debug(
            requested_business_id=b_id,
            requested_scenario_id=s_id,
            resolved_business_id=b_id,
            resolved_scenario_id=resolved_scen,
            conflict_reason=conflict_msg
        )
        logger.error(f"[DPR Stage 1] Error building context for {b_id}: {e}", exc_info=True)
        if "DPR_STATE_ISOLATION_ERROR" in conflict_msg:
            raise HTTPException(status_code=409, detail=f"Failed to build DPR context: {conflict_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to build DPR context: {conflict_msg}")


@router.get("/gap-analysis/{business_id}")
async def get_dpr_gap_analysis(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Executes comprehensive gap scan across 8 modules and 39 sections.
    Returns blocking vs high vs optional gaps, section-level completeness, and readiness gates.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        _log_dpr_state_trace(f"/dpr/gap-analysis/{business_id}", business_id, scenario.scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        _assert_state_isolation(business_id, ctx.get("business_id"), scenario_id, ctx.get("scenario_id"))
        gap_res = dpr_gap_analyzer.analyze(ctx)
        return gap_res.model_dump()
    except Exception as e:
        logger.error(f"[DPR Stage 1] Error analyzing gaps for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze DPR gaps: {str(e)}")


@router.get("/sections/{business_id}")
async def get_dpr_sections(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns the complete 39-section breakdown grouped under 8 canonical modules with field-level details.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        return {
            "modules": ctx.get("modules"),
            "sections": ctx.get("sections")
        }
    except Exception as e:
        logger.error(f"[DPR Stage 1] Error getting sections for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DPR sections: {str(e)}")


@router.get("/assumptions/{business_id}")
async def get_dpr_assumptions(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns baseline benchmarks, active assumptions, and explicit user overrides.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        return {
            "scenario_id": scenario.scenario_id,
            "version": scenario.version,
            "benchmarks": ctx.get("assumptions"),
            "user_overrides": scenario.user_overrides,
            "fields": ctx.get("fields")
        }
    except Exception as e:
        logger.error(f"[DPR Stage 1] Error getting assumptions for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DPR assumptions: {str(e)}")


# ============================================================================
# INTERACTIVE QUESTION & OVERRIDE FLOW
# ============================================================================

@router.get("/question/next/{business_id}")
async def get_next_dpr_question(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    language: str = Query(default="en", description="Language code (en, hi, mr)"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns the next single prioritized user question for unresolved DPR inputs.
    Never asks for calculated values (DSCR, Project Cost, EBITDA, Depreciation, Tax).
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)
        question = await dpr_question_engine.get_next_question(gap_res, ctx, language=language)

        if not question:
            return {
                "has_question": False,
                "question": None,
                "message": "All critical and high-priority questions have been resolved."
            }

        return {
            "has_question": True,
            "question": question.model_dump(),
            "remaining_blocking_gaps": len(gap_res.blocking_gaps),
            "readiness_status": gap_res.dpr_readiness_status.value
        }
    except Exception as e:
        logger.error(f"[DPR Stage 1] Error getting next question for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}")


@router.get("/question/next")
async def get_next_dpr_question_query(
    business_id: str = Query(..., description="Target business identifier or UUID"),
    language: str = Query(default="en", description="Language code (en, hi)"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Query parameter alias for get_next_dpr_question (?business_id=saree_retail&scenario_id=default).
    """
    return await get_next_dpr_question(
        business_id=business_id,
        language=language,
        scenario_id=scenario_id,
        db=db
    )



@router.post("/question/answer/{business_id}")
async def answer_dpr_question(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="Answer payload: { field_id, answer, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Submits user answer, validates input, applies multi-field resolutions,
    and recalculates downstream financial impact if applicable.
    """
    try:
        field_id = payload.get("field_id")
        raw_answer = payload.get("answer") if "answer" in payload else payload.get("value")
        scenario_id = payload.get("scenario_id")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        res = dpr_answer_resolver.resolve_answer(field_id=field_id, raw_answer=raw_answer)
        if not res.validation_passed:
            return {
                "success": False,
                "validation_error": res.validation_error,
                "field_id": field_id
            }

        # Save user answer
        dpr_scenario_manager.set_user_answer(
            business_id=business_id,
            field_id=field_id,
            value=res.canonical_value,
            multi_updates=res.multi_field_updates,
            scenario_id=scenario_id
        )

        # Trigger authoritative recalculation
        recalc_res = await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            changed_field_id=field_id,
            db=db
        )

        gap_analysis_data = recalc_res.get("gap_analysis") or {}
        return {
            "success": True,
            "resolved_value": res.canonical_value,
            "multi_field_updates": res.multi_field_updates,
            "impact": recalc_res.get("impact"),
            "gap_analysis": gap_analysis_data,
            "is_ready_for_stage_14_2": gap_analysis_data.get("is_ready_for_stage_14_2", False),
            "is_ready_for_stage_2": gap_analysis_data.get("is_ready_for_stage_2", False),
            "can_proceed_to_dpr": gap_analysis_data.get("can_proceed_to_dpr", False),
            "dpr_context_package": recalc_res.get("dpr_context_package")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR Stage 1] Error processing answer for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process question answer: {str(e)}")


@router.post("/override/{business_id}")
async def set_dpr_override(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="Override payload: { field_id, override_value, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Applies an explicit user override to an assumption without altering the underlying benchmark.
    Triggers authoritative financial recalculation and returns Change Impact Panel data.
    """
    try:
        field_id = payload.get("field_id")
        val = payload.get("override_value")
        scenario_id = payload.get("scenario_id")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        fdef = get_field_definition(field_id)
        if not fdef or not fdef.editable:
            raise HTTPException(status_code=400, detail=f"Field {field_id} is calculated and cannot be directly edited.")

        # Save override
        dpr_scenario_manager.set_user_override(
            business_id=business_id,
            field_id=field_id,
            value=val,
            scenario_id=scenario_id
        )

        # Recalculate
        recalc_res = await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            changed_field_id=field_id,
            db=db
        )

        return {
            "success": True,
            "override_applied": {
                "field_id": field_id,
                "value": val
            },
            "impact": recalc_res.get("impact"),
            "gap_analysis": recalc_res.get("gap_analysis")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR Stage 1] Error setting override for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to set override: {str(e)}")


@router.post("/benchmark/accept/{business_id}")
async def accept_benchmark(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ field_id, benchmark_value, benchmark_id, source, scenario_id, category, nic_code, user_modified_value }"),
    db: Session = Depends(get_db)
):
    """
    Confirms acceptance of an authoritative benchmark value, removing any previous override.
    If user provided an altered value, records as USER_OVERRIDE.
    """
    try:
        field_id = payload.get("field_id")
        bench_val = payload.get("benchmark_value")
        bench_id = payload.get("benchmark_id")
        source = payload.get("source")
        scenario_id = payload.get("scenario_id")
        category = payload.get("category")
        nic_code = payload.get("nic_code")
        user_modified_val = payload.get("user_modified_value")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        dpr_scenario_manager.accept_benchmark(
            business_id=business_id,
            field_id=field_id,
            benchmark_value=bench_val,
            benchmark_id=bench_id,
            source=source,
            scenario_id=scenario_id,
            category=category,
            nic_code=nic_code,
            user_modified_value=user_modified_val
        )

        recalc_res = await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            changed_field_id=field_id,
            db=db
        )

        return {
            "success": True,
            "message": f"Processed benchmark acceptance for {field_id}",
            "gap_analysis": recalc_res.get("gap_analysis")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error accepting benchmark for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to accept benchmark: {str(e)}")


@router.post("/document/update/{business_id}")
async def update_dpr_document(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ document_key, status, document_name, extracted_value, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Updates document enclosure checklist status (e.g. PROVIDED, VERIFIED, PENDING),
    persists evidence in the scenario, rebuilds DPR context, and re-runs gap analysis immediately.
    """
    try:
        doc_key = payload.get("document_key")
        status = payload.get("status", "PROVIDED")
        doc_name = payload.get("document_name")
        ext_val = payload.get("extracted_value")
        scenario_id = payload.get("scenario_id")

        if not doc_key:
            raise HTTPException(status_code=400, detail="document_key is required")

        dpr_scenario_manager.update_document(
            business_id=business_id,
            document_key=doc_key,
            status=status,
            document_name=doc_name,
            extracted_value=ext_val,
            scenario_id=scenario_id
        )

        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)

        return {
            "success": True,
            "document_updated": doc_key,
            "status": status,
            "gap_analysis": gap_res.model_dump(),
            "dpr_context_package": ctx
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error updating document for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update document status: {str(e)}")


@router.post("/recalculate/{business_id}")
async def trigger_recalculation(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Forces an immediate end-to-end recalculation across M1-M6 financial engines.
    """
    try:
        res = await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            db=db
        )
        return res
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error during recalculation for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")


@router.get("/readiness/{business_id}")
async def get_dpr_readiness(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns the deterministic readiness gate evaluation and reasons.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)
        return {
            "readiness_status": gap_res.dpr_readiness_status.value,
            "can_proceed_to_dpr": gap_res.can_proceed_to_dpr,
            "is_ready_for_stage_14_2": gap_res.is_ready_for_stage_14_2,
            "reasons": gap_res.readiness_reasons,
            "blocking_gaps_count": len(gap_res.blocking_gaps),
            "high_priority_gaps_count": len(gap_res.high_priority_gaps),
            "completed_sections_count": sum(1 for s in gap_res.section_summaries.values() if s.completeness_status == "COMPLETE"),
            "total_sections_count": len(gap_res.section_summaries)
        }
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error checking readiness for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check readiness: {str(e)}")


@router.get("/package/{business_id}")
async def get_dpr_context_package(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns the complete canonical DPR_CONTEXT_PACKAGE snapshot.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        return ctx
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error getting package for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get context package: {str(e)}")


@router.get("/handoff/{business_id}")
async def get_stage14_handoff(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Exports the canonical Stage 14.1 -> Stage 14.2 DPR_INTAKE_PACKAGE handoff contract.
    Preserves upstream business classification (Stages 1–13), verified intake, promoter context,
    location context, document evidence, assumptions, conflicts, and readiness gates.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)
        handoff_pkg = build_stage14_handoff_package(
            business_id=business_id,
            context=ctx,
            gap_analysis=gap_res,
            scenario_id=scenario.scenario_id
        )
        return handoff_pkg.model_dump()
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error building handoff package for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate Stage 14 handoff package: {str(e)}")


@router.get("/stage1/debug/lineage/{business_id}")
@router.get("/debug/lineage/{business_id}")
async def get_stage1_debug_lineage(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Diagnostic Lineage Endpoint:
    Returns full provenance and end-to-end data lineage for Stage 1 -> Stage 14.1 -> Stage 14.2.
    Verifies that user business inputs (e.g. Grocery Shop) deterministically populate
    the financial engine and DPR context without cross-contamination or hardcoded saree defaults.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)
        fields = ctx.get("fields") or {}
        bp = ctx.get("business_profile") or {}
        raw = ctx.get("raw_intake") or {}
        next_q = await dpr_question_engine.get_next_question(gap_res, ctx)

        return {
            "status": "SUCCESS",
            "business_id": business_id,
            "scenario_id": scenario.scenario_id,
            "intake_lineage": {
                "raw_business_description": raw.get("raw_business_description") or bp.get("business_activity") or bp.get("specific_business"),
                "business_name": bp.get("business_name") or raw.get("business_name"),
                "specific_business": bp.get("specific_business") or bp.get("business_activity"),
                "nic_code": fields.get("nic_code", {}).get("value") or bp.get("nic_code"),
                "state": bp.get("state") or raw.get("state"),
                "district": bp.get("district") or raw.get("district"),
            },
            "upstream_cards": {
                "legal_constitution": {
                    "value": fields.get("legal_constitution", {}).get("value"),
                    "source": fields.get("legal_constitution", {}).get("source_type"),
                    "status": fields.get("legal_constitution", {}).get("status")
                },
                "premises_status": {
                    "value": fields.get("premises_status", {}).get("value"),
                    "source": fields.get("premises_status", {}).get("source_type"),
                    "status": fields.get("premises_status", {}).get("status")
                },
                "target_scheme_code": {
                    "value": fields.get("target_scheme_code", {}).get("value"),
                    "source": fields.get("target_scheme_code", {}).get("source_type"),
                    "status": fields.get("target_scheme_code", {}).get("status")
                }
            },
            "financial_engine_lineage": {
                "total_project_cost": fields.get("total_project_cost", {}).get("value"),
                "bank_term_loan_amount": fields.get("bank_term_loan_amount", {}).get("value"),
                "promoter_equity_amount": fields.get("promoter_equity_amount", {}).get("value"),
                "glance_average_dscr": fields.get("glance_average_dscr", {}).get("value"),
                "financial_integrity_status": gap_res.financial_integrity_status
            },
            "gap_and_readiness_status": {
                "dpr_readiness_status": gap_res.dpr_readiness_status.value,
                "can_proceed_to_dpr": gap_res.can_proceed_to_dpr,
                "is_ready_for_stage_14_2": gap_res.is_ready_for_stage_14_2,
                "is_ready_for_stage_2": gap_res.is_ready_for_stage_2,
                "blocking_gaps_count": len(gap_res.blocking_gaps),
                "blocking_gaps": [g.field_id for g in gap_res.blocking_gaps],
                "high_priority_gaps_count": len(gap_res.high_priority_gaps),
                "readiness_reasons": gap_res.readiness_reasons
            },
            "question_engine": {
                "has_next_question": next_q is not None,
                "next_question_field_id": next_q.field_id if next_q else None,
                "next_question_text": (next_q.question or next_q.question_text) if next_q else None,
                "next_question_example": next_q.example if next_q else None
            }
        }
    except Exception as e:
        logger.error(f"[DPR Stage 1 Debug] Error analyzing lineage for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lineage debug failed: {str(e)}")


@router.get("/14.2/lineage/{business_id}")
async def get_field_lineage_report(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Stage 14.2 Full Field Lineage Diagnostic Report.
    For every canonical DPR field, returns:
    - Resolved value (or None)
    - Resolution status
    - Source type, source stage, source module, source path
    - Sources checked (provenance trail)
    - Resolution method
    - Whether question is allowed
    Grouped by section for easy auditing.
    """
    from app.services.dpr_stage1.dpr_canonical_field_registry import (
        CANONICAL_FIELDS,
        build_resolution_trace,
        resolve_field_semantically,
    )
    from app.services.dpr_stage1.dpr_registry import CANONICAL_SECTIONS

    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        fields = ctx.get("fields") or {}
        bp = ctx.get("business_profile") or {}

        # Per-field lineage
        field_lineage = {}
        section_lineage = {}

        for fid, f_record in fields.items():
            trace = build_resolution_trace(fid, fields)
            entry = {
                "field_id": fid,
                "section": f_record.get("section_id", ""),
                "section_id": f_record.get("section_id", ""),
                "label": f_record.get("label", fid),
                "value": f_record.get("value"),
                "status": f_record.get("status"),
                "source_type": f_record.get("source_type"),
                "source_stage": f_record.get("source_stage") or f_record.get("source_id"),
                "source_module": f_record.get("source_module") or f_record.get("source_id"),
                "source_path": f_record.get("source_path") or f_record.get("source_reference"),
                "resolution_method": f_record.get("resolution_method"),
                "sources_checked": f_record.get("sources_checked", []),
                "confidence": f_record.get("confidence"),
                "previous_value": f_record.get("previous_value"),
                "previous_source": f_record.get("previous_source"),
                "overwrite_attempt": f_record.get("overwrite_attempt"),
                "overwrite_reason": f_record.get("overwrite_reason"),
                "materiality": f_record.get("materiality"),
                "applicable": f_record.get("applicable"),
                "editable": f_record.get("editable"),
                "question_allowed": trace.question_allowed,
                "trace_steps": trace.trace_steps,
            }
            field_lineage[fid] = entry

            # Group by section
            sec_id = f_record.get("section_id", "unknown")
            if sec_id not in section_lineage:
                section_lineage[sec_id] = {"fields": [], "resolved": 0, "unresolved": 0, "not_applicable": 0}
            section_lineage[sec_id]["fields"].append(fid)
            status_str = str(f_record.get("status", ""))
            if status_str.startswith("RESOLVED_") or status_str in ["DERIVED", "BENCHMARK_ACCEPTED"]:
                section_lineage[sec_id]["resolved"] += 1
            elif status_str == "NOT_APPLICABLE":
                section_lineage[sec_id]["not_applicable"] += 1
            else:
                section_lineage[sec_id]["unresolved"] += 1

        # Summary stats
        total = len(field_lineage)
        resolved = sum(1 for f in field_lineage.values() if str(f.get("status", "")).startswith("RESOLVED_") or f.get("status") in ["DERIVED", "BENCHMARK_ACCEPTED"])
        unresolved = sum(1 for f in field_lineage.values() if f.get("status") in ["USER_REQUIRED", "UNKNOWN", "DOCUMENT_PENDING", "UNRESOLVED"])
        na = sum(1 for f in field_lineage.values() if f.get("status") == "NOT_APPLICABLE")

        return {
            "status": "SUCCESS",
            "business_id": business_id,
            "scenario_id": scenario.scenario_id,
            "business_identity": {
                "business_name": bp.get("business_name"),
                "archetype": bp.get("archetype"),
                "nic_code": bp.get("nic_code"),
                "district": bp.get("district"),
                "state": bp.get("state"),
            },
            "summary": {
                "total_fields": total,
                "resolved_fields": resolved,
                "unresolved_fields": unresolved,
                "not_applicable_fields": na,
                "resolution_rate_pct": round(resolved / total * 100, 1) if total > 0 else 0,
            },
            "section_lineage": section_lineage,
            "field_lineage": field_lineage,
        }
    except Exception as e:
        logger.error(f"[DPR 14.2 Lineage] Error generating lineage for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lineage report failed: {str(e)}")


@router.post("/intake/{business_id}")
async def submit_stage14_intake(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="Intake dictionary"),
    db: Session = Depends(get_db)
):
    """
    Submits or updates raw Stage 14.1 intake fields directly.
    Normalizes all incoming field names against the canonical DPR registry.
    Stores values in scenario state and triggers context re-assembly and gap analysis.
    """
    try:
        from app.services.dpr_stage1.dpr_registry import normalize_field_id
        scenario_id = payload.get("scenario_id")
        
        for k, v in payload.items():
            if k == "scenario_id":
                continue
            if v is not None:
                canonical_fid = normalize_field_id(k)
                dpr_scenario_manager.set_user_answer(
                    business_id=business_id,
                    field_id=canonical_fid,
                    value=v,
                    scenario_id=scenario_id
                )
        
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            accepted_benchmarks=scenario.accepted_benchmarks,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)
        
        return {
            "success": True,
            "business_id": business_id,
            "scenario_id": scenario.scenario_id,
            "readiness_status": gap_res.dpr_readiness_status.value,
            "is_ready_for_stage_14_2": gap_res.is_ready_for_stage_14_2,
            "blocking_gaps_count": len(gap_res.blocking_gaps),
            "high_priority_gaps_count": len(gap_res.high_priority_gaps),
            "gap_analysis": gap_res.model_dump()
        }
    except Exception as e:
        logger.error(f"[DPR Stage 14.1] Error submitting intake for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit Stage 14.1 intake: {str(e)}")


# ============================================================================
# STAGE 14.2: DPR ENRICHMENT & DETERMINISTIC INFERENCE ENDPOINTS
# ============================================================================

@router.get("/enrichment/{business_id}")
async def get_dpr_enrichment(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Retrieves the Stage 14.2 Enriched Package. If not yet executed, runs deterministic enrichment automatically.
    """
    try:
        _log_dpr_state_trace(f"/dpr/enrichment/{business_id}", business_id, scenario_id)
        pkg = dpr_enrichment_service.get_persisted_enrichment(business_id, scenario_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        _assert_state_isolation(business_id, pkg.business_id, scenario_id, pkg.scenario_id)
        return pkg.model_dump()
    except Exception as e:
        logger.error(f"[DPR Stage 14.2] Error retrieving enrichment for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DPR enrichment: {str(e)}")


@router.post("/enrichment/run/{business_id}")
async def run_dpr_enrichment(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Forces execution of Stage 14.2 DPR Enrichment & Deterministic Inference.
    Resolves evidence, benchmarks, market, policy, runs authoritative M1-M6, and compiles 8 modules / 39 sections.
    """
    try:
        body = payload or {}
        scen_id = body.get("scenario_id") or scenario_id
        _log_dpr_state_trace(f"/dpr/enrichment/run/{business_id}", business_id, scen_id)
        pkg = await dpr_enrichment_service.run_enrichment(business_id, scen_id, db=db)
        _assert_state_isolation(business_id, pkg.business_id, scen_id, pkg.scenario_id)
        return pkg.model_dump()
    except Exception as e:
        logger.error(f"[DPR Stage 14.2] Error running enrichment for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to run DPR enrichment: {str(e)}")


@router.get("/enrichment/assumptions/{business_id}")
async def get_enrichment_assumptions(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns the 'Confirm KALPA's Assumptions' package for Stage 14.2 review.
    """
    try:
        pkg = dpr_enrichment_service.get_persisted_enrichment(business_id, scenario_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        return pkg.assumption_review.model_dump()
    except Exception as e:
        logger.error(f"[DPR Stage 14.2] Error getting assumptions for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assumption review: {str(e)}")


@router.post("/enrichment/assumption/{business_id}")
async def update_enrichment_assumption(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ field_id, action, value, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Updates an assumption in Stage 14.2 (CONFIRM_BENCHMARK or OVERRIDE),
    triggers authoritative M1-M6 recalculation, updates DPR fields, and refreshes the package.
    """
    try:
        field_id = payload.get("field_id")
        action = payload.get("action", "OVERRIDE")
        val = payload.get("value")
        scen_id = payload.get("scenario_id")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        pkg = await dpr_enrichment_service.update_assumption(
            business_id=business_id,
            field_id=field_id,
            action=action,
            value=val,
            scenario_id=scen_id,
            db=db
        )
        return pkg.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR Stage 14.2] Error updating assumption for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update assumption: {str(e)}")


@router.get("/enrichment/status/{business_id}")
async def get_enrichment_status(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Returns Stage 14.2 enrichment completeness, validation summary, and module readiness.
    """
    try:
        pkg = dpr_enrichment_service.get_persisted_enrichment(business_id, scenario_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)

        return {
            "business_id": business_id,
            "scenario_id": pkg.scenario_id,
            "is_enrichment_complete": pkg.is_enrichment_complete,
            "can_proceed_to_validation": pkg.can_proceed_to_validation,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "validation": pkg.validation.model_dump(),
            "total_assumptions_requiring_review": len(pkg.assumption_review.assumptions_requiring_review),
            "user_overridden_count": pkg.assumption_review.user_overridden_count,
            "user_confirmed_count": pkg.assumption_review.user_confirmed_count,
            "modules_status": {m_id: m.is_module_ready for m_id, m in pkg.modules.items()}
        }
    except Exception as e:
        logger.error(f"[DPR Stage 14.2] Error getting enrichment status for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check enrichment status: {str(e)}")


# ============================================================================
# STANDARDIZED 14.2 API CONTRACT ENDPOINTS (Requirement 18)
# ============================================================================

@router.get("/14.2/context/{business_id}")
async def get_dpr_14_2_context(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Retrieves DPR Stage 14.2 Context.
    """
    try:
        _log_dpr_state_trace(f"/dpr/14.2/context/{business_id}", business_id, scenario_id)
        pkg = dpr_enrichment_service.get_persisted_enrichment(business_id, scenario_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        _assert_state_isolation(business_id, pkg.business_id, scenario_id, pkg.scenario_id)
        return {
            "scenario_id": pkg.scenario_id,
            "version": pkg.version,
            "business_profile": pkg.business_profile,
            "entrepreneur_profile": pkg.entrepreneur_profile,
            "location_profile": pkg.location_profile,
            "financials": pkg.financials,
            "benchmarks": pkg.benchmarks,
            "fields": {fid: f.model_dump() for fid, f in pkg.fields.items()},
            "provenance": pkg.provenance
        }
    except Exception as e:
        logger.error(f"[DPR 14.2] Error getting context for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get 14.2 context: {str(e)}")


@router.get("/14.2/enrichment/{business_id}")
async def get_dpr_14_2_enrichment(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Retrieves the full DPR_ENRICHMENT_PACKAGE.
    """
    b_id = business_id.strip()
    s_id = scenario_id.strip() if scenario_id else None
    resolved_scen = s_id or f"DPR-{b_id[:8] if len(b_id) >= 8 else b_id}"
    _log_dpr_identity(b_id, resolved_scen, source="/dpr/14.2/enrichment")

    # Mismatch protection
    if s_id and s_id.startswith("DPR-"):
        clean_biz = b_id.replace("-", "").replace("_", "")[:5].lower()
        clean_scen = s_id.replace("DPR-", "").replace("-", "").replace("_", "")[:5].lower()
        if clean_biz and clean_scen and len(clean_scen) >= 4 and len(clean_biz) >= 4:
            if not clean_biz.startswith(clean_scen[:3]) and not clean_scen.startswith(clean_biz[:3]):
                conflict_reason = f"Scenario '{s_id}' does not belong to business '{b_id}'"
                logger.error(f"[DPR 14.2] Scenario mismatch: {conflict_reason}")
                raise HTTPException(
                    status_code=409,
                    detail={
                        "status": "BLOCKED",
                        "reason": "CONTEXT_LOAD_FAILED",
                        "http_error": 409,
                        "message": conflict_reason
                    }
                )

    try:
        _log_dpr_state_trace(f"/dpr/14.2/enrichment/{b_id}", b_id, resolved_scen)
        pkg = dpr_enrichment_service.get_persisted_enrichment(b_id, s_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(b_id, s_id, db=db)
        _assert_state_isolation(b_id, pkg.business_id, s_id, pkg.scenario_id)
        return pkg.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(
            f"[DPR_ENRICHMENT_ERROR]\n"
            f"business_id={b_id}\n"
            f"scenario_id={resolved_scen}\n"
            f"context_id=dpr_context:{b_id}:{resolved_scen}\n"
            f"financial_package_id=fin:{b_id}\n"
            f"exception_type={type(e).__name__}\n"
            f"exception_message={str(e)}\n"
            f"traceback:\n{tb}"
        )
        if isinstance(e, DPR_STATE_ISOLATION_ERROR) or "DPR_STATE_ISOLATION_ERROR" in str(e):
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "BLOCKED",
                    "reason": "CONTEXT_LOAD_FAILED",
                    "http_error": 409,
                    "message": str(e)
                }
            )
        raise HTTPException(
            status_code=500,
            detail={
                "status": "ERROR",
                "reason": "ENRICHMENT_EXECUTION_FAILED",
                "http_error": 500,
                "exception_type": type(e).__name__,
                "message": str(e)
            }
        )


@router.get("/14.2/gaps/{business_id}")
async def get_dpr_14_2_gaps(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Evaluates gap analysis and missing required fields.
    """
    try:
        scenario = dpr_scenario_manager.get_or_create_scenario(business_id, scenario_id)
        ctx = await dpr_context_builder.build_context(
            business_id=business_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        gap_res = dpr_gap_analyzer.analyze(ctx)
        return {
            "scenario_id": scenario.scenario_id,
            "version": scenario.version,
            "gaps": gap_res.model_dump(),
            "blocking_gaps": [g.model_dump() for g in gap_res.blocking_gaps],
            "high_priority_gaps": [g.model_dump() for g in gap_res.high_priority_gaps],
            "readiness_status": gap_res.dpr_readiness_status.value
        }
    except Exception as e:
        logger.error(f"[DPR 14.2] Error analyzing gaps for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze 14.2 gaps: {str(e)}")


@router.post("/14.2/answer/{business_id}")
async def post_dpr_14_2_answer(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ field_id, answer, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Resolves user answer to intent question, triggers recalculation and enrichment update.
    """
    try:
        field_id = payload.get("field_id")
        raw_answer = payload.get("answer") if "answer" in payload else payload.get("value")
        scenario_id = payload.get("scenario_id")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        res = dpr_answer_resolver.resolve_answer(field_id=field_id, raw_answer=raw_answer)
        if not res.validation_passed:
            return {
                "success": False,
                "validation_error": res.validation_error,
                "field_id": field_id
            }

        dpr_scenario_manager.set_user_answer(
            business_id=business_id,
            field_id=field_id,
            value=res.canonical_value,
            multi_updates=res.multi_field_updates,
            scenario_id=scenario_id
        )

        await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            changed_field_id=field_id,
            db=db
        )

        pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        return {
            "success": True,
            "scenario_id": pkg.scenario_id,
            "version": pkg.version,
            "resolved_value": res.canonical_value,
            "multi_field_updates": res.multi_field_updates,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "validation": pkg.validation.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR 14.2] Error processing answer for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process 14.2 answer: {str(e)}")


@router.post("/14.2/benchmark/accept/{business_id}")
async def post_dpr_14_2_benchmark_accept(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ field_id, benchmark_id, benchmark_value, source, scenario_id, category, nic_code, user_modified_value }"),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Accepts authoritative benchmark and triggers enrichment recalculation.
    """
    try:
        field_id = payload.get("field_id")
        bench_val = payload.get("benchmark_value")
        bench_id = payload.get("benchmark_id")
        source = payload.get("source")
        scenario_id = payload.get("scenario_id")
        category = payload.get("category")
        nic_code = payload.get("nic_code")
        user_modified_val = payload.get("user_modified_value")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        dpr_scenario_manager.accept_benchmark(
            business_id=business_id,
            field_id=field_id,
            benchmark_value=bench_val,
            benchmark_id=bench_id,
            source=source,
            scenario_id=scenario_id,
            category=category,
            nic_code=nic_code,
            user_modified_value=user_modified_val
        )

        await dpr_scenario_manager.recalculate_scenario(
            business_id=business_id,
            scenario_id=scenario_id,
            changed_field_id=field_id,
            db=db
        )

        pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        return {
            "success": True,
            "scenario_id": pkg.scenario_id,
            "version": pkg.version,
            "field_id": field_id,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "validation": pkg.validation.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR 14.2] Error accepting benchmark for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to accept 14.2 benchmark: {str(e)}")


@router.post("/14.2/document/{business_id}")
async def post_dpr_14_2_document(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ document_key, status, document_name, extracted_value, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Updates verified document evidence and refreshes enrichment.
    """
    try:
        doc_key = payload.get("document_key")
        status = payload.get("status", "PROVIDED")
        doc_name = payload.get("document_name")
        ext_val = payload.get("extracted_value")
        scenario_id = payload.get("scenario_id")

        if not doc_key:
            raise HTTPException(status_code=400, detail="document_key is required")

        dpr_scenario_manager.update_document(
            business_id=business_id,
            document_key=doc_key,
            status=status,
            document_name=doc_name,
            extracted_value=ext_val,
            scenario_id=scenario_id
        )

        pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        return {
            "success": True,
            "scenario_id": pkg.scenario_id,
            "version": pkg.version,
            "document_updated": doc_key,
            "status": status,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "validation": pkg.validation.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR 14.2] Error updating document for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update 14.2 document: {str(e)}")


@router.post("/14.2/assumption/{business_id}")
async def post_dpr_14_2_assumption(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Dict[str, Any] = Body(..., description="{ field_id, action, value, scenario_id }"),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Updates assumption review item (CONFIRM_BENCHMARK or OVERRIDE).
    """
    try:
        field_id = payload.get("field_id")
        action = payload.get("action", "OVERRIDE")
        val = payload.get("value")
        scen_id = payload.get("scenario_id")

        if not field_id:
            raise HTTPException(status_code=400, detail="field_id is required")

        pkg = await dpr_enrichment_service.update_assumption(
            business_id=business_id,
            field_id=field_id,
            action=action,
            value=val,
            scenario_id=scen_id,
            db=db
        )
        return {
            "success": True,
            "scenario_id": pkg.scenario_id,
            "version": pkg.version,
            "field_id": field_id,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "validation": pkg.validation.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DPR 14.2] Error updating assumption for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update 14.2 assumption: {str(e)}")


@router.get("/14.2/validation/{business_id}")
async def get_dpr_14_2_validation(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Returns comprehensive validation checks and financial authority verification.
    """
    try:
        _log_dpr_state_trace(f"/dpr/14.2/validation/{business_id}", business_id, scenario_id)
        pkg = dpr_enrichment_service.get_persisted_enrichment(business_id, scenario_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(business_id, scenario_id, db=db)
        _assert_state_isolation(business_id, pkg.business_id, scenario_id, pkg.scenario_id)
        return {
            "scenario_id": pkg.scenario_id,
            "version": pkg.version,
            "overall_valid": pkg.validation.overall_valid,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "total_checks": pkg.validation.total_checks,
            "passed_checks": pkg.validation.passed_checks,
            "failed_checks": pkg.validation.failed_checks,
            "checks": [c.model_dump() for c in pkg.validation.checks],
            "financial_authority_checks": [fc.model_dump() for fc in pkg.validation.financial_authority_checks],
            "blocking_reasons": pkg.validation.blocking_reasons
        }
    except Exception as e:
        logger.error(f"[DPR 14.2] Error getting validation for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get 14.2 validation: {str(e)}")


@router.get("/14.2/readiness/{business_id}")
async def get_dpr_14_2_readiness(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    scenario_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Standardized 14.2 Endpoint: Returns readiness gate decision for handoff to Stage 14.3.
    """
    try:
        b_id = (business_id or "").strip()
        _log_dpr_state_trace(f"/dpr/14.2/readiness/{b_id}", b_id, scenario_id)
        pkg = dpr_enrichment_service.get_persisted_enrichment(b_id, scenario_id)
        if not pkg:
            pkg = await dpr_enrichment_service.run_enrichment(b_id, scenario_id, db=db)
        _assert_state_isolation(b_id, pkg.business_id, scenario_id, pkg.scenario_id)

        # Field resolution diagnostics for development mode
        required_fields = [
            fid for fid, f in pkg.fields.items()
            if getattr(f, 'materiality', None) in ['CRITICAL', 'HIGH']
        ]
        resolved_fields = [
            fid for fid, f in pkg.fields.items()
            if getattr(f, 'status', None) not in ['UNKNOWN', 'USER_REQUIRED', 'UNRESOLVED', 'SOURCE_MAPPING_ERROR']
            and getattr(f, 'value', None) is not None
        ]
        unresolved_required_fields = [
            fid for fid, f in pkg.fields.items()
            if getattr(f, 'materiality', None) in ['CRITICAL', 'HIGH']
            and (getattr(f, 'status', None) in ['UNKNOWN', 'USER_REQUIRED', 'UNRESOLVED', 'SOURCE_MAPPING_ERROR'] or getattr(f, 'value', None) is None)
        ]

        logger.info(
            f"[DPR_14_2_READINESS]\n"
            f"business_id={b_id}\n"
            f"scenario_id={pkg.scenario_id}\n"
            f"ready_for_stage_14_3={pkg.ready_for_stage_14_3}\n"
            f"blocking_reasons={pkg.validation.blocking_reasons}"
        )

        return {
            "business_id": b_id,
            "scenario_id": pkg.scenario_id,
            "intake_id": f"intake-{pkg.scenario_id.lower()}",
            "context_key": f"dpr_context:{b_id}:{pkg.scenario_id}",
            "version": pkg.version,
            "ready_for_stage_14_3": pkg.ready_for_stage_14_3,
            "is_enrichment_complete": pkg.is_enrichment_complete,
            "reasons": pkg.readiness.get("reasons", []),
            "blocking_reasons": pkg.validation.blocking_reasons,
            "required_fields": required_fields,
            "resolved_fields": resolved_fields,
            "unresolved_required_fields": unresolved_required_fields,
            "completed_sections_count": sum(1 for s in pkg.sections.values() if s.completeness_status == "COMPLETE"),
            "total_sections_count": len(pkg.sections)
        }
    except Exception as e:
        logger.error(f"[DPR 14.2] Error checking readiness for {business_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check 14.2 readiness: {str(e)}")


# ============================================================================
# SARVAM AUDIO SPEECH (STT / TTS) ENDPOINTS FOR DPR
# ============================================================================

@router.post("/audio/transcribe")
async def transcribe_dpr_audio(
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    language_code: Optional[str] = Query(default="en")
):
    """
    Transcribes spoken voice answers using Sarvam STT. Multilingual support.
    Accepts 'file' (standard contract) or 'audio' as multipart form-data.
    """
    upload = file or audio
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "file: Field required"}
        )

    try:
        audio_bytes = await upload.read()
        if not audio_bytes or len(audio_bytes) < 100:
            return {
                "success": False,
                "transcript": "",
                "text": "",
                "language_code": language_code or "en",
                "error": "Please record audio before submitting."
            }

        transcript, detected_lang = await sarvam_stt_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=upload.filename or "recording.webm",
            content_type=upload.content_type or "audio/webm",
            language_code=language_code
        )
        return {
            "success": True,
            "transcript": transcript,
            "text": transcript,
            "language_code": detected_lang or language_code or "en"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[DPR Stage 14.1 STT] Error transcribing: {e}")
        return {
            "success": False,
            "transcript": "",
            "text": "",
            "language_code": language_code or "en",
            "error": "Couldn't understand audio. You can try again or type your answer."
        }


@router.post("/audio/synthesize")
async def synthesize_dpr_audio(
    payload: Dict[str, Any] = Body(..., description="{ text, language_code }")
):
    """
    Synthesizes speech audio for questions using Sarvam Bulbul TTS.
    """
    try:
        text = payload.get("text", "")
        lang = payload.get("language_code", "hi")
        res = await sarvam_tts_service.synthesize_speech(text=text, language_code=lang)
        audio_b64 = res.get("audio_base64", "")
        return {
            "success": True,
            "audio_base64": audio_b64,
            "audios": [audio_b64] if audio_b64 else [],
            "format": res.get("format", "audio/wav"),
            "mime_type": res.get("mime_type", "audio/wav"),
            "language_code": res.get("language_code", lang),
            "speaker": res.get("speaker", "shreya"),
            "spoken_text": res.get("spoken_text", text)
        }
    except Exception as e:
        logger.warning(f"[DPR Stage 14.1 TTS] Synthesis note: {e}")
        return {
            "success": False,
            "audio_base64": "",
            "audios": [],
            "error": f"TTS unavailable: {str(e)}"
        }


# ============================================================================
# STAGE 14.3: INSTITUTIONAL-GRADE BANK-REVIEW-READY DPR GENERATION ENGINE
# ============================================================================

@router.post("/14.3/generate/{business_id}")
async def generate_stage_14_3_dpr(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Stage 14.3: Generates the Final Institutional-Grade Bank-Review-Ready DPR.
    Consumes Stage 14.2 Enriched Package and Milestone 1-6 Financial Authority.
    Returns: document_id, status, validation_status, dpr_status, page_count, generated_at, download_reference, preview_reference.
    """
    b_id = business_id.strip()
    body = payload or {}
    s_id = body.get("scenario_id")

    _log_dpr_identity(b_id, s_id or f"DPR-{b_id[:8]}", source="/dpr/14.3/generate")
    _log_dpr_state_trace(f"/dpr/14.3/generate/{b_id}", b_id, s_id)

    try:
        from app.dpr.stage14_3 import (
            stage14_3_orchestrator,
            DPRGenerationRequest,
            DPR_FINANCIAL_RECONCILIATION_FAILED,
        )

        req = DPRGenerationRequest(
            business_id=b_id,
            scenario_id=s_id,
            format=body.get("format", "pdf"),
            language=body.get("language", "en"),
            regenerate_narrative=body.get("regenerate_narrative", False)
        )

        resp = await stage14_3_orchestrator.generate_dpr(req, db=db)
        
        # Assemble authoritative metadata from canonical context
        scenario = dpr_scenario_manager.get_or_create_scenario(b_id, s_id)
        ctx = await dpr_context_builder.build_context(
            business_id=b_id,
            db=db,
            scenario_id=scenario.scenario_id,
            user_overrides=scenario.user_overrides,
            user_answers=scenario.user_answers,
            document_statuses=scenario.document_statuses
        )
        ctx_fields = ctx.get("fields", {})
        fin_pkg = ctx.get("financial_package", {})
        from app.dpr.stage14_3.document_schema import extract_financial_scalars
        fin_scalars = extract_financial_scalars(fin_pkg)

        bp = ctx.get("business_profile", {})
        dist = ctx_fields.get("location_district", {}).get("value") or bp.get("district") or ""
        st = ctx_fields.get("location_state", {}).get("value") or bp.get("state") or ""
        loc_str = f"{dist}, {st}".strip(", ") if (dist or st) else "Operational Site"

        raw_bname = ctx_fields.get("business_name", {}).get("value") or bp.get("business_name") or bp.get("name") or b_id
        if isinstance(raw_bname, str) and "_" in raw_bname:
            friendly_bname = raw_bname.replace("_", " ").title()
        else:
            friendly_bname = str(raw_bname or "Commercial Enterprise")

        return {
            "document_id": resp.document_id,
            "business_id": resp.business_id,
            "scenario_id": resp.scenario_id,
            "status": resp.status,
            "validation_status": resp.validation_status,
            "dpr_status": resp.dpr_status.value,
            "page_count": resp.page_count,
            "generated_at": resp.generated_at,
            "download_reference": resp.download_reference,
            "preview_reference": resp.preview_reference,
            "sections_count": resp.sections_count,
            "annexures_count": resp.annexures_count,
            "financial_integrity": resp.financial_integrity.model_dump(),
            "narrative_engine": resp.narrative_engine,
            "metadata": {
                "business_name": friendly_bname,
                "business_activity": ctx_fields.get("business_activity", {}).get("value") or bp.get("activity") or "Commercial Operations",
                "promoter_name": ctx_fields.get("promoter_name", {}).get("value") or bp.get("promoter_name") or "Promoter",
                "location": loc_str,
                "total_project_cost": fin_scalars.get("total_project_cost") or ctx_fields.get("total_project_cost", {}).get("value") or ctx_fields.get("glance_total_project_cost", {}).get("value"),
                "bank_term_loan": fin_scalars.get("term_loan") or ctx_fields.get("bank_term_loan_amount", {}).get("value"),
                "working_capital": fin_scalars.get("working_capital"),
                "promoter_contribution": fin_scalars.get("promoter_contribution") or ctx_fields.get("promoter_equity_amount", {}).get("value"),
                "average_dscr": fin_scalars.get("average_dscr") or ctx_fields.get("glance_average_dscr", {}).get("value"),
                "break_even": fin_scalars.get("break_even_utilization") or ctx_fields.get("glance_break_even_utilization", {}).get("value"),
            }
        }
    except DPR_STATE_ISOLATION_ERROR as e:
        logger.error(f"[STAGE 14.3 IDENTITY ERROR] {e}")
        raise HTTPException(status_code=409, detail=f"DPR_STATE_ISOLATION_ERROR: {str(e)}")
    except DPR_FINANCIAL_RECONCILIATION_FAILED as e:
        logger.error(f"[STAGE 14.3 RECONCILIATION ERROR] {e.message}: {e.errors}")
        raise HTTPException(
            status_code=422,
            detail={
                "message": "DPR generation blocked: financial reconciliation requires correction.",
                "error_type": "DPR_FINANCIAL_RECONCILIATION_FAILED",
                "errors": e.errors
            }
        )
    except (TypeError, ValueError) as e:
        logger.error(f"[STAGE 14.3 NUMERIC TYPE ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail={
                "status": "BLOCKED",
                "stage": "14.3",
                "error_code": "DPR_NUMERIC_TYPE_MISMATCH",
                "message": f"Stage 14.3 numeric type error: {str(e)}"
            }
        )
    except Exception as e:
        logger.error(f"[STAGE 14.3 GENERATION ERROR] {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Stage 14.3 DPR generation failed: {str(e)}")


@router.get("/14.3/llm/status/{business_id}")
@router.get("/llm/status/{business_id}")
async def get_dpr_llm_status(
    business_id: str = Path(..., description="Target business identifier")
):
    """
    Exposes structured runtime diagnostics for Sarvam LLM narrative layer.
    """
    from app.dpr.stage14_3.sarvam_service import llm_status_tracker
    return llm_status_tracker.get_status(business_id)


@router.get("/14.3/status/{document_id}")
async def get_stage_14_3_status(
    document_id: str = Path(..., description="Generated DPR document ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieves status, validation state, and page count of generated DPR.
    """
    from app.dpr.stage14_3 import REPORTS_DIR
    clean_id = "".join(c for c in document_id if c.isalnum() or c in ("-", "_"))
    pdf_filename = f"{clean_id}.pdf"
    file_path = os.path.join(REPORTS_DIR, pdf_filename)

    exists = os.path.exists(file_path)
    page_count = 0
    if exists:
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
        except Exception:
            page_count = 1

    return {
        "document_id": document_id,
        "exists": exists,
        "status": "COMPLETED" if exists else "NOT_FOUND",
        "dpr_status": "BANK_REVIEW_READY" if exists else "UNKNOWN",
        "page_count": page_count,
        "download_reference": f"/dpr/14.3/download/{document_id}",
        "preview_reference": f"/dpr/14.3/preview/{document_id}"
    }


@router.get("/14.3/preview/{document_id}")
@router.get("/14.3/document/{document_id}/preview")
async def preview_stage_14_3_pdf(
    document_id: str = Path(..., description="Generated DPR document ID"),
    db: Session = Depends(get_db)
):
    """
    Returns PDF for browser preview (inline disposition). Never exposes internal file paths.
    """
    from app.dpr.stage14_3 import REPORTS_DIR
    clean_id = "".join(c for c in document_id if c.isalnum() or c in ("-", "_"))
    pdf_filename = f"{clean_id}.pdf"
    file_path = os.path.join(REPORTS_DIR, pdf_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="DPR report document not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={clean_id}.pdf"}
    )


@router.get("/14.3/download/{document_id}")
@router.get("/14.3/document/{document_id}/download")
async def download_stage_14_3_pdf(
    document_id: str = Path(..., description="Generated DPR document ID"),
    db: Session = Depends(get_db)
):
    """
    Downloads institutional DPR PDF (attachment disposition). Never exposes internal file paths.
    """
    from app.dpr.stage14_3 import REPORTS_DIR
    clean_id = "".join(c for c in document_id if c.isalnum() or c in ("-", "_"))
    pdf_filename = f"{clean_id}.pdf"
    file_path = os.path.join(REPORTS_DIR, pdf_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="DPR report document not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"KALPA_Detailed_Project_Report_{clean_id}.pdf"
    )


# ============================================================================
# EXISTING STAGE 14 GENERATION & PDF ENDPOINTS (PRESERVED)
# ============================================================================

@router.post("/generate/{business_id}", response_model=DPRDocumentMetadata)
async def generate_bankable_dpr(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Synthesizes authoritative Milestone 1–5 financial package and upstream context
    into a bankable Detailed Project Report (DPR).
    """
    try:
        body = payload or {}
        fin_pkg = body.get("financial_package") or {}
        resolved_scheme = (
            body.get("scheme_code")
            or body.get("target_scheme")
            or (fin_pkg.get("scheme_code") if isinstance(fin_pkg, dict) else None)
        )
        req = DPRDocumentRequest(
            business_id=business_id,
            session_id=body.get("session_id"),
            analysis_id=body.get("analysis_id"),
            scheme_code=resolved_scheme,
            language_code=body.get("language_code", "en"),
            report_format=body.get("report_format", "pdf"),
            financial_package=fin_pkg if fin_pkg else None,
            non_financial_context=body.get("non_financial_context"),
        )
        logger.info(f"[API STAGE 14] Generating DPR for business_id={business_id}")
        metadata = await dpr_generation_engine.generate_dpr(req, db=db)
        return metadata
    except Exception as e:
        logger.error(f"[API STAGE 14] Failed to generate DPR for business_id={business_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DPR generation failed: {str(e)}"
        )


@router.get("/report/{report_id}", response_model=DPRDocumentMetadata)
async def get_dpr_report(
    report_id: str = Path(..., description="Generated report ID or document ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieves full generated DPR metadata, report sections, and financial highlights.
    """
    from app.database.models.report import GeneratedReport
    from app.services.assistant_engine.context_builder import safe_uuid
    
    rep_uuid = safe_uuid(report_id)
    rep = None
    if rep_uuid and db:
        rep = db.query(GeneratedReport).filter(
            (GeneratedReport.id == rep_uuid) | (GeneratedReport.business_id == rep_uuid)
        ).order_by(GeneratedReport.created_at.desc()).first()

    if rep:
        pdf_path = rep.file_path or os.path.join(REPORTS_DIR, f"{report_id}.pdf")
        return DPRDocumentMetadata(
            document_id=str(rep.id),
            title=rep.report_title or f"DPR Report {report_id}",
            pages=2,
            file_format="pdf",
            status="generated",
            file_path=pdf_path,
            download_url=f"/dpr/report/{report_id}/pdf",
            report_summary=rep.report_summary,
            completeness_status="COMPLETE",
            is_dpr_eligible=True,
            financial_highlights={},
            dpr_package=rep.report_payload
        )

    # Check local disk
    pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
    if os.path.exists(pdf_path):
        return DPRDocumentMetadata(
            document_id=report_id,
            title=f"DPR Report {report_id}",
            pages=2,
            file_format="pdf",
            status="generated",
            file_path=pdf_path,
            download_url=f"/dpr/report/{report_id}/pdf",
            report_summary="Bankable DPR Report",
            completeness_status="COMPLETE",
            is_dpr_eligible=True
        )

    raise HTTPException(status_code=404, detail=f"DPR report {report_id} not found")


@router.get("/report/{report_id}/pdf")
async def download_dpr_pdf(
    report_id: str = Path(..., description="Report document identifier"),
    db: Session = Depends(get_db)
):
    """
    Downloads the institutional-grade Bankable DPR PDF file.
    """
    pdf_filename = f"{report_id}.pdf"
    file_path = os.path.join(REPORTS_DIR, pdf_filename)

    if not os.path.exists(file_path) and db:
        from app.database.models.report import GeneratedReport
        from app.services.assistant_engine.context_builder import safe_uuid
        rep_uuid = safe_uuid(report_id)
        if rep_uuid:
            rep = db.query(GeneratedReport).filter(GeneratedReport.id == rep_uuid).first()
            if rep and rep.file_path and os.path.exists(rep.file_path):
                file_path = rep.file_path

    if not os.path.exists(file_path):
        logger.info(f"[API STAGE 14] PDF {file_path} not found on disk, generating on-the-fly for {report_id}")
        req = DPRDocumentRequest(business_id=report_id)
        metadata = await dpr_generation_engine.generate_dpr(req, db=db)
        if metadata.file_path and os.path.exists(metadata.file_path):
            file_path = metadata.file_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF report file not found on server")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"Bankable_DPR_{report_id}.pdf"
    )


# =====================================================================
# DEVELOPMENT-ONLY ENDPOINTS — DO NOT EXPOSE IN PRODUCTION
# =====================================================================

@router.post("/dev/reset-scenario", tags=["Dev Tools"])
async def dev_reset_scenario(
    business_id: str = Body(..., embed=False),
    scenario_id: str = Body(None, embed=False),
    payload: Dict[str, Any] = Body(...)
):
    """
    DEVELOPMENT ONLY: Scoped reset of a single business/scenario.
    Clears scenario state, enrichment cache, enrichment persistence, and in-memory caches.
    Does NOT touch other businesses, benchmarks, ontology, or Stage 1-13 databases.
    """
    if os.environ.get("KALPA_ENV", "development").lower() == "production":
        raise HTTPException(status_code=403, detail="Reset endpoint disabled in production")

    b_id = (payload.get("business_id") or business_id or "").strip()
    s_id = (payload.get("scenario_id") or scenario_id or "").strip()
    if not b_id:
        raise HTTPException(status_code=400, detail="business_id is required")
    if not s_id:
        s_id = f"DPR-{b_id[:8] if len(b_id) >= 8 else b_id}"

    cleared = []

    # 1. Clear scenario state (in-memory + disk)
    from app.services.dpr_stage1.dpr_scenario_manager import scenario_repository
    cache_key = f"{b_id}:{s_id}"
    if cache_key in scenario_repository._store:
        del scenario_repository._store[cache_key]
        cleared.append("scenario_state_memory")
    scen_fp = scenario_repository._file_path(b_id, s_id)
    if os.path.exists(scen_fp):
        os.remove(scen_fp)
        cleared.append("scenario_state_disk")

    # 2. Clear enrichment (in-memory + disk)
    enrich_cache_key = f"{b_id}:{s_id}"
    if enrich_cache_key in dpr_enrichment_service._cache:
        del dpr_enrichment_service._cache[enrich_cache_key]
        cleared.append("enrichment_cache_memory")
    enrich_fp = dpr_enrichment_service._file_path(b_id, s_id)
    if os.path.exists(enrich_fp):
        os.remove(enrich_fp)
        cleared.append("enrichment_persistence_disk")

    # 3. Clear context builder in-memory caches if any
    if hasattr(dpr_context_builder, '_context_cache'):
        ctx_key = f"{b_id}:{s_id}"
        if ctx_key in dpr_context_builder._context_cache:
            del dpr_context_builder._context_cache[ctx_key]
            cleared.append("context_builder_cache")

    logger.info(f"[DEV_RESET] Reset scenario business_id={b_id} scenario_id={s_id} cleared={cleared}")

    return {
        "status": "RESET_COMPLETE",
        "business_id": b_id,
        "scenario_id": s_id,
        "cleared": cleared if cleared else ["nothing_found"],
        "message": f"Scenario {s_id} for business {b_id} has been reset. Frontend sessionStorage must be cleared manually."
    }


@router.post("/dev/reset", tags=["Dev Tools"])
async def dev_reset_alias(
    payload: Dict[str, Any] = Body(...)
):
    """Alias for /dev/reset-scenario"""
    return await dev_reset_scenario(
        business_id=payload.get("business_id", ""),
        scenario_id=payload.get("scenario_id"),
        payload=payload
    )


@router.post("/dev/reset-all", tags=["Dev Tools"])
async def dev_reset_all():
    """
    DEVELOPMENT ONLY: Clears ALL persisted scenario states, enrichment files, and caches.
    """
    if os.environ.get("KALPA_ENV", "development").lower() == "production":
        raise HTTPException(status_code=403, detail="Reset endpoint disabled in production")

    import glob
    cleared_files = []

    # 1. Clear in-memory stores
    from app.services.dpr_stage1.dpr_scenario_manager import scenario_repository
    scenario_repository._store.clear()
    dpr_enrichment_service._cache.clear()

    # 2. Clear scenario files on disk
    for fp in glob.glob(os.path.join(scenario_repository.storage_dir, "*.json")):
        try:
            os.remove(fp)
            cleared_files.append(os.path.basename(fp))
        except Exception as e:
            logger.warning(f"Failed to remove {fp}: {e}")

    # 3. Clear enrichment files on disk
    for fp in glob.glob(os.path.join(dpr_enrichment_service.storage_dir, "*.json")):
        try:
            os.remove(fp)
            cleared_files.append(os.path.basename(fp))
        except Exception as e:
            logger.warning(f"Failed to remove {fp}: {e}")

    logger.info(f"[DEV_RESET_ALL] Cleared all {len(cleared_files)} scenario/enrichment persistence files.")

    return {
        "status": "RESET_ALL_COMPLETE",
        "cleared_count": len(cleared_files),
        "cleared_files": cleared_files,
        "message": "All DPR scenario persistence files and memory caches have been cleared."
    }


@router.get("/debug/field-lineage/{business_id}/{scenario_id}/{field_id}", tags=["Dev Tools"])
async def debug_field_lineage(
    business_id: str,
    scenario_id: str,
    field_id: str,
    db: Session = Depends(get_db)
):
    """
    DEVELOPMENT ONLY: Traces the full resolution lineage of a single canonical DPR field.
    Shows every candidate value, its source, and its priority.
    """
    if os.environ.get("KALPA_ENV", "development").lower() == "production":
        raise HTTPException(status_code=403, detail="Debug endpoint disabled in production")

    b_id = business_id.strip()
    s_id = scenario_id.strip()
    f_id = field_id.strip()

    # Build context to get full resolution
    try:
        ctx = await dpr_context_builder.build_context(
            business_id=b_id,
            scenario_id=s_id,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context build failed: {str(e)}")

    field_data = ctx.get("fields", {}).get(f_id)
    if not field_data:
        # Try normalized
        from app.services.dpr_stage1.dpr_registry import normalize_field_id
        norm = normalize_field_id(f_id)
        field_data = ctx.get("fields", {}).get(norm)
        if not field_data:
            raise HTTPException(status_code=404, detail=f"Field '{f_id}' not found in context")

    # Build candidates list from scenario state
    from app.services.dpr_stage1.dpr_scenario_manager import scenario_repository
    scen = scenario_repository.get(b_id, s_id)
    candidates = []
    if scen:
        if f_id in scen.user_overrides:
            candidates.append({"value": scen.user_overrides[f_id], "source": "USER_OVERRIDE", "priority": 1})
        if f_id in scen.user_answers:
            candidates.append({"value": scen.user_answers[f_id], "source": "USER_ANSWER", "priority": 2})
        if f_id in scen.accepted_benchmarks:
            candidates.append({"value": scen.accepted_benchmarks[f_id], "source": "ACCEPTED_BENCHMARK", "priority": 5})

    # Also check enrichment
    try:
        enrich = dpr_enrichment_service.get_persisted_enrichment(b_id, s_id)
        if enrich and f_id in enrich.fields:
            ef = enrich.fields[f_id]
            candidates.append({
                "value": ef.value,
                "source": f"ENRICHMENT_{ef.source_type}",
                "priority": 10,
                "source_reference": ef.source_reference
            })
    except Exception:
        pass

    return {
        "field_id": f_id,
        "business_id": b_id,
        "scenario_id": s_id,
        "current_value": field_data.get("value") if isinstance(field_data, dict) else field_data,
        "status": field_data.get("status") if isinstance(field_data, dict) else "RESOLVED",
        "source_type": field_data.get("source_type") if isinstance(field_data, dict) else "UNKNOWN",
        "source_reference": field_data.get("source_reference") if isinstance(field_data, dict) else None,
        "source_business_id": field_data.get("source_business_id") if isinstance(field_data, dict) else b_id,
        "source_scenario_id": field_data.get("source_scenario_id") if isinstance(field_data, dict) else s_id,
        "candidates": candidates,
        "resolution_path": field_data.get("resolution_notes", []) if isinstance(field_data, dict) else []
    }


@router.get("/14.1/lineage/{business_id}", response_model=Dict[str, Any])
async def get_dpr_14_1_lineage(
    business_id: str = Path(..., description="Business ID or concept name"),
    scenario_id: Optional[str] = Query(None, description="Active scenario identifier"),
    db: Session = Depends(get_db)
):
    """
    Diagnostic Lineage Endpoint:
    Returns the authoritative resolution trace, data lineage, and question suppression status
    for all canonical DPR fields for the given business.
    """
    b_id = business_id.strip()
    s_id = scenario_id.strip() if scenario_id else f"DPR-{b_id[:8] if len(b_id) >= 8 else b_id}"

    try:
        ctx = await dpr_context_builder.build_context(
            business_id=b_id,
            db=db,
            scenario_id=s_id
        )
    except DPR_STATE_ISOLATION_ERROR as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context build failed: {str(e)}")

    fields = ctx.get("fields", {})
    from app.services.dpr_stage1.dpr_canonical_field_registry import (
        NON_ASKABLE_STATUSES,
        is_question_allowed,
        get_canonical_entry,
    )

    lineage_records = []
    for fid, fdata in fields.items():
        val = fdata.get("value")
        status = fdata.get("status", "UNKNOWN")
        source = fdata.get("source_id") or fdata.get("source_type") or "UNKNOWN"
        source_path = fdata.get("source_reference") or fdata.get("source_path") or "none"
        sources_checked = fdata.get("sources_checked") or []
        applicable = fdata.get("applicable", True)

        entry = get_canonical_entry(fid)
        q_allowed = is_question_allowed(fid) if entry else True

        suppressed = False
        suppression_reason = None

        if not applicable or status in ["NOT_APPLICABLE", "PENDING_CLASSIFICATION"]:
            suppressed = True
            suppression_reason = "FIELD_NOT_APPLICABLE_TO_ARCHETYPE"
        elif not q_allowed or not fdata.get("editable", True):
            suppressed = True
            suppression_reason = "CALCULATED_OR_FROZEN_ENGINE_FIELD"
        elif val is not None or status.startswith("RESOLVED_") or status in NON_ASKABLE_STATUSES:
            suppressed = True
            suppression_reason = f"RESOLVED_VIA_{status}"
        elif status in ["SOURCE_PENDING", "SOURCE_MAPPING_ERROR"]:
            suppressed = True
            suppression_reason = f"SUPPRESSED_{status}"
        elif status in ["DOCUMENT_PENDING", "DOCUMENT_REQUIRED"]:
            suppressed = True
            suppression_reason = "DOCUMENT_VERIFICATION_PENDING"

        lineage_records.append({
            "field": fid,
            "field_id": fid,
            "value": val,
            "status": status,
            "source": source,
            "source_type": fdata.get("source_type"),
            "source_path": source_path,
            "sources_checked": sources_checked,
            "applicable": applicable,
            "question_suppressed": suppressed,
            "suppression_reason": suppression_reason,
            "confidence": fdata.get("confidence"),
            "resolution_method": fdata.get("resolution_method"),
        })

    return {
        "business_id": b_id,
        "scenario_id": s_id,
        "total_fields": len(lineage_records),
        "suppressed_fields_count": sum(1 for r in lineage_records if r["question_suppressed"]),
        "unresolved_gaps_count": sum(1 for r in lineage_records if not r["question_suppressed"]),
        "lineage": lineage_records
    }


