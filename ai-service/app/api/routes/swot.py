"""
FastAPI Routes for Stage 13: Dynamic SWOT Agent.
Exposes REST endpoints for strategic interpretation, evidence hydration,
database caching/idempotency, persistence, and LLM readiness checks.
"""
from typing import Dict, Any, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.database.session import get_db
from app.database.models.swot import SwotResult
from app.database.models.feasibility import FeasibilityResult
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.market import MarketEvidenceRecord
from app.database.models.finance import FinancialProfile
from app.database.models.orchestrator import OrchestrationRecord
from app.schemas.swot import (
    SWOTEvaluationRequest,
    SWOTAnalysisResponse,
    SWOTCategoryBreakdown,
    SWOTGenerationMeta,
    StrategicSummary,
    SWOTRecommendation,
    ImmediateAction,
    SWOTEvidenceSummary,
    ModelMetadata
)
from app.services.swot_engine import dynamic_swot_agent

router = APIRouter(prefix="/swot", tags=["Stage 13 — Dynamic SWOT Agent"])


@router.post(
    "/analyze",
    response_model=SWOTAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Stage 13 Strategic SWOT Analysis",
    description="Synthesizes verified facts across Stages 6–12 to produce evidence-grounded SWOT matrix and strategic priorities."
)
async def analyze_swot(
    request: SWOTEvaluationRequest,
    db: Session = Depends(get_db)
):
    logger.info(f"[STAGE 13 SWOT API] Received request for analysis_id={request.analysis_id}, session_id={request.session_id}, force_refresh={request.force_refresh}")
    try:
        analysis_id = request.analysis_id
        session_id = request.session_id

        target_uuid = None
        if analysis_id:
            try:
                target_uuid = uuid.UUID(analysis_id)
            except Exception:
                pass
        if not target_uuid and session_id:
            try:
                target_uuid = uuid.UUID(session_id)
            except Exception:
                pass

        # -------------------------------------------------------------
        # 1. Idempotency & Caching Check (Skip LLM if already persisted)
        # -------------------------------------------------------------
        if target_uuid and not request.force_refresh:
            cached_rec = db.query(SwotResult).filter(
                (SwotResult.id == target_uuid) | (SwotResult.session_id == target_uuid)
            ).order_by(SwotResult.created_at.desc()).first()

            if cached_rec and cached_rec.status == "COMPLETED" and cached_rec.swot_json:
                logger.info(f"[STAGE 13 SWOT CACHE HIT] Returning persisted SWOT for target_uuid={target_uuid}")
                gen_data = (cached_rec.model_metadata_json or {}).get("generation") or {
                    "mode": "SARVAM_LLM" if (cached_rec.model_metadata_json or {}).get("provider") == "sarvam" else "DETERMINISTIC_FALLBACK",
                    "model": (cached_rec.model_metadata_json or {}).get("model", "sarvam-105b"),
                    "llm_status": "success"
                }
                return SWOTAnalysisResponse(
                    status=cached_rec.status,
                    analysis_id=str(cached_rec.id),
                    session_id=str(cached_rec.session_id) if cached_rec.session_id else None,
                    generation=SWOTGenerationMeta(**gen_data) if isinstance(gen_data, dict) else None,
                    swot=cached_rec.swot_json if cached_rec.swot_json else None,
                    provenance={
                        "market": "STAGE_6",
                        "opportunity": "STAGE_8",
                        "finance": "STAGE_9",
                        "entrepreneur": "STAGE_10",
                        "risk": "STAGE_11",
                        "feasibility": "STAGE_12"
                    },
                    strategic_summary=cached_rec.strategic_summary_json if cached_rec.strategic_summary_json else None,
                    recommendations=cached_rec.recommendations_json or [],
                    immediate_actions=cached_rec.immediate_actions_json or [],
                    evidence_summary=cached_rec.evidence_summary_json if cached_rec.evidence_summary_json else None,
                    confidence=cached_rec.confidence_score,
                    model_metadata=cached_rec.model_metadata_json if cached_rec.model_metadata_json else None
                )

        # -------------------------------------------------------------
        # 2. Hydrate Missing Upstream Context from PostgreSQL
        # -------------------------------------------------------------
        if target_uuid:
            # A. FeasibilityResult (Stage 12)
            if not request.feasibility_result:
                feas = db.query(FeasibilityResult).filter(
                    (FeasibilityResult.id == target_uuid) | (FeasibilityResult.session_id == target_uuid)
                ).first()
                if feas:
                    request.feasibility_result = {
                        "overall_feasibility_score": feas.overall_feasibility_score,
                        "decision": feas.viability_status,
                        "viability_status": feas.viability_status,
                        "recommendation": feas.recommendation,
                        "pillar_scores": feas.pillar_scores or {},
                        "critical_gates": feas.critical_gates or [],
                        "positive_drivers": feas.positive_drivers or [],
                        "key_constraints": feas.key_constraints or [],
                        "conditions": feas.conditions or [],
                    }

            # B. StructuredBusinessProfile (Stage 3 & 10)
            prof = db.query(StructuredBusinessProfile).filter(
                (StructuredBusinessProfile.id == target_uuid) | (StructuredBusinessProfile.session_id == target_uuid)
            ).order_by(StructuredBusinessProfile.created_at.desc()).first()

            if prof and prof.profile_json:
                p_json = prof.profile_json
                if not request.business_profile:
                    request.business_profile = p_json.get("business_profile") or {
                        "specific_business": prof.specific_business,
                        "business_name": prof.specific_business,
                        "business_id": prof.specific_business,
                        "category": p_json.get("category"),
                        "sector": p_json.get("sector")
                    }
                if not request.location_profile:
                    request.location_profile = p_json.get("location_profile") or {
                        "village": prof.district,
                        "district": prof.district,
                        "state": prof.state
                    }
                if not request.entrepreneur_readiness and p_json.get("entrepreneur_readiness"):
                    request.entrepreneur_readiness = p_json.get("entrepreneur_readiness")
                if not request.financial_context and p_json.get("financial_context"):
                    request.financial_context = p_json.get("financial_context")
                if not request.financial_analysis and p_json.get("financial_analysis"):
                    request.financial_analysis = p_json.get("financial_analysis")

            # C. FinancialProfile (Stage 9)
            if not request.financial_analysis or not request.financial_context:
                fin = db.query(FinancialProfile).filter(
                    (FinancialProfile.id == target_uuid) |
                    (FinancialProfile.business_id == target_uuid) |
                    (FinancialProfile.business_id == prof.id if prof else False)
                ).first()
                if fin:
                    bk = fin.breakdown_json if isinstance(fin.breakdown_json, dict) else {}
                    if not request.financial_context and bk.get("financial_context"):
                        request.financial_context = bk.get("financial_context")
                    if not request.financial_analysis:
                        request.financial_analysis = bk or {
                            "dscr": fin.debt_service_coverage_ratio,
                            "debt_service": {"dscr": fin.debt_service_coverage_ratio},
                            "break_even": {"break_even_point_percentage": fin.break_even_percentage},
                            "break_even_point_percentage": fin.break_even_percentage,
                            "total_project_cost": fin.total_project_cost,
                            "estimated_financeable_loan": fin.bank_loan_requirement,
                            "monthly_emi": bk.get("monthly_emi") or 8500.0,
                        }

            # Cross-sync financial_context and financial_analysis
            if not request.financial_context and request.financial_analysis and isinstance(request.financial_analysis, dict):
                request.financial_context = request.financial_analysis.get("financial_context")
            if request.financial_context and not request.financial_analysis:
                request.financial_analysis = {"financial_context": request.financial_context}
            elif request.financial_context and isinstance(request.financial_analysis, dict) and "financial_context" not in request.financial_analysis:
                request.financial_analysis["financial_context"] = request.financial_context

            # D. OrchestrationRecord (Stages 8, 9, 10, 11)
            orch = db.query(OrchestrationRecord).filter(
                (OrchestrationRecord.id == target_uuid) | (OrchestrationRecord.session_id == target_uuid)
            ).order_by(OrchestrationRecord.created_at.desc()).first()
            if orch and orch.orchestration_output:
                out = orch.orchestration_output
                res = out.get("agent_results", {}) if isinstance(out, dict) else {}
                if not request.opportunity_result:
                    request.opportunity_result = (
                        res.get("opportunity_evaluation_engine")
                        or res.get("opportunity_evaluation")
                        or out.get("opportunity_evaluation")
                        or out.get("opportunity_result")
                    )
                if not request.financial_analysis:
                    request.financial_analysis = (
                        res.get("finance_engine")
                        or res.get("financial_analysis")
                        or out.get("financial_analysis")
                    )
                if not request.entrepreneur_readiness:
                    request.entrepreneur_readiness = (
                        res.get("entrepreneur_profile_engine")
                        or res.get("entrepreneur_profile")
                        or out.get("entrepreneur_profile")
                    )
                if not request.risk_analysis:
                    request.risk_analysis = (
                        res.get("risk_engine")
                        or res.get("risk_analysis")
                        or out.get("risk_analysis")
                    )

            # E. MarketEvidenceRecord (Stage 6)
            if not request.market_analysis:
                mkt_rec = db.query(MarketEvidenceRecord).filter(
                    (MarketEvidenceRecord.id == target_uuid) | (MarketEvidenceRecord.session_id == target_uuid)
                ).order_by(MarketEvidenceRecord.created_at.desc()).first()
                if mkt_rec:
                    request.market_analysis = mkt_rec.market_evidence or mkt_rec.full_profile or {}

        # -------------------------------------------------------------
        # 3. Execute Stage 13 Dynamic SWOT Agent
        # -------------------------------------------------------------
        response = await dynamic_swot_agent.generate_swot_analysis(request)

        # -------------------------------------------------------------
        # 4. Persist to PostgreSQL swot_results Table
        # -------------------------------------------------------------
        if target_uuid:
            try:
                existing = db.query(SwotResult).filter(
                    (SwotResult.id == target_uuid) | (SwotResult.session_id == target_uuid)
                ).first()

                out_json = response.model_dump()

                if existing:
                    existing.status = response.status
                    existing.confidence_score = response.confidence
                    existing.swot_json = out_json.get("swot") or {}
                    existing.strategic_summary_json = out_json.get("strategic_summary") or {}
                    existing.recommendations_json = out_json.get("recommendations") or []
                    existing.immediate_actions_json = out_json.get("immediate_actions") or []
                    existing.evidence_summary_json = out_json.get("evidence_summary") or {}
                    existing.model_metadata_json = {
                        **(out_json.get("model_metadata") or {}),
                        "generation": out_json.get("generation")
                    }
                    existing.error_json = {"error_code": response.error_code, "message": response.message} if response.error_code else None
                    db.commit()
                else:
                    rec = SwotResult(
                        id=target_uuid,
                        session_id=uuid.UUID(session_id) if session_id else target_uuid,
                        status=response.status,
                        confidence_score=response.confidence,
                        swot_json=out_json.get("swot") or {},
                        strategic_summary_json=out_json.get("strategic_summary") or {},
                        recommendations_json=out_json.get("recommendations") or [],
                        immediate_actions_json=out_json.get("immediate_actions") or [],
                        evidence_summary_json=out_json.get("evidence_summary") or {},
                        model_metadata_json={
                            **(out_json.get("model_metadata") or {}),
                            "generation": out_json.get("generation")
                        },
                        error_json={"error_code": response.error_code, "message": response.message} if response.error_code else None
                    )
                    db.add(rec)
                    db.commit()
            except Exception as db_err:
                logger.warning(f"[STAGE 13 SWOT DB PERSIST WARNING] {db_err}")
                db.rollback()

        return response

    except Exception as e:
        logger.error(f"[STAGE 13 SWOT API ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 13 Dynamic SWOT Agent failed: {str(e)}"
        )


@router.get(
    "/{id}",
    response_model=SWOTAnalysisResponse,
    summary="Get Persisted SWOT Analysis",
    description="Retrieves a persisted Stage 13 SWOT analysis record by analysis_id or session_id."
)
async def get_swot_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    try:
        target_uuid = uuid.UUID(id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for analysis or session ID"
        )

    rec = db.query(SwotResult).filter(
        (SwotResult.id == target_uuid) | (SwotResult.session_id == target_uuid)
    ).order_by(SwotResult.created_at.desc()).first()

    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No SWOT analysis found for identifier '{id}'"
        )

    gen_meta = (rec.model_metadata_json or {}).get("generation") if rec.model_metadata_json else None
    if not gen_meta and rec.model_metadata_json:
        gen_meta = {
            "mode": "SARVAM_LLM" if rec.model_metadata_json.get("provider") == "sarvam" else "DETERMINISTIC_FALLBACK",
            "model": rec.model_metadata_json.get("model", "sarvam-105b"),
            "llm_status": "success" if rec.status == "COMPLETED" else "unavailable"
        }

    return SWOTAnalysisResponse(
        status=rec.status,
        analysis_id=str(rec.id),
        session_id=str(rec.session_id) if rec.session_id else None,
        generation=SWOTGenerationMeta(**gen_meta) if isinstance(gen_meta, dict) else None,
        swot=rec.swot_json if rec.swot_json else None,
        provenance={
            "market": "STAGE_6",
            "opportunity": "STAGE_8",
            "finance": "STAGE_9",
            "entrepreneur": "STAGE_10",
            "risk": "STAGE_11",
            "feasibility": "STAGE_12"
        },
        strategic_summary=rec.strategic_summary_json if rec.strategic_summary_json else None,
        recommendations=rec.recommendations_json or [],
        immediate_actions=rec.immediate_actions_json or [],
        evidence_summary=rec.evidence_summary_json if rec.evidence_summary_json else None,
        confidence=rec.confidence_score,
        model_metadata=rec.model_metadata_json if rec.model_metadata_json else None,
        error_code=(rec.error_json or {}).get("error_code") if rec.error_json else None,
        message=(rec.error_json or {}).get("message") if rec.error_json else None,
    )


@router.get(
    "/health",
    summary="Check Stage 13 SWOT Agent Health",
    description="Returns configuration and readiness state of Stage 13 Dynamic SWOT Agent and Sarvam LLM."
)
async def check_swot_health():
    return {
        "status": "healthy",
        "stage": "STAGE_13",
        "service": "Dynamic SWOT Agent",
        "sarvam_configured": settings.is_sarvam_configured,
        "sarvam_llm_enabled": settings.is_sarvam_llm_enabled,
        "model": settings.SARVAM_LLM_MODEL,
        "endpoint": settings.SARVAM_LLM_ENDPOINT,
    }
