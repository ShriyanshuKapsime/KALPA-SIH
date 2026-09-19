"""
FastAPI Routes for Stage 12: Feasibility Engine.
Provides endpoints for multivariate feasibility analysis, calculation provenance retrieval,
SWOT inspection, and pivot advisory.
"""
from typing import Dict, Any, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.feasibility import FeasibilityResult
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.market import MarketEvidenceRecord
from app.database.models.finance import FinancialProfile
from app.database.models.orchestrator import OrchestrationRecord
from app.schemas.feasibility import (
    FeasibilityEvaluationRequest,
    FeasibilityAnalysisResponse,
    PivotCandidate
)
from app.services.feasibility_engine import feasibility_engine, pivot_advisor_engine, feasibility_feature_vector_builder
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine
from app.services.risk_engine import risk_engine
from app.core.logging import logger

router = APIRouter(prefix="/feasibility", tags=["Stage 12 - Feasibility Engine"])


@router.post(
    "/analyze",
    response_model=FeasibilityAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Stage 12 Multivariate Feasibility Analysis",
    description="Consumes Stage 8 Opportunity, Stage 9 Finance, Stage 10 Readiness, and Stage 11 Risk to synthesize venture feasibility."
)
async def analyze_feasibility(
    request: FeasibilityEvaluationRequest,
    db: Session = Depends(get_db)
):
    try:
        analysis_id = request.analysis_id
        session_id = request.session_id

        # -------------------------------------------------------------
        # 1. Hydrate Missing Upstream Context from Database
        # -------------------------------------------------------------
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

        raw_market_evidence = None

        if target_uuid:
            # A. StructuredBusinessProfile (Stage 3 & Stage 10)
            prof = db.query(StructuredBusinessProfile).filter(
                (StructuredBusinessProfile.id == target_uuid) | (StructuredBusinessProfile.session_id == target_uuid)
            ).order_by(StructuredBusinessProfile.created_at.desc()).first()

            if prof and prof.profile_json:
                p_json = prof.profile_json
                if not request.business_profile:
                    request.business_profile = p_json.get("business_profile") or {
                        "specific_business": prof.specific_business,
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
                if not request.entrepreneur_readiness:
                    # Evaluate Stage 10 live from profile if not yet evaluated
                    ep_res = entrepreneur_profile_engine.evaluate_profile(
                        business_node_id=prof.specific_business or "retail_general",
                        user_profile_data=p_json.get("entrepreneur_profile") or p_json.get("user_profile") or {},
                        business_title=prof.specific_business
                    )
                    request.entrepreneur_readiness = ep_res.model_dump()

            # B. MarketEvidenceRecord (Stage 6)
            mkt = db.query(MarketEvidenceRecord).filter(
                (MarketEvidenceRecord.id == target_uuid) | (MarketEvidenceRecord.session_id == target_uuid)
            ).order_by(MarketEvidenceRecord.created_at.desc()).first()
            if mkt:
                raw_market_evidence = mkt.full_profile or mkt.market_evidence or {}

            # C. FinancialProfile (Stage 9)
            if not request.financial_analysis:
                fin = db.query(FinancialProfile).filter(
                    (FinancialProfile.id == target_uuid) | (FinancialProfile.business_id == target_uuid)
                ).first()
                if fin:
                    request.financial_analysis = {
                        "dscr": fin.debt_service_coverage_ratio,
                        "debt_service": {"dscr": fin.debt_service_coverage_ratio},
                        "break_even": {"break_even_point_percentage": fin.break_even_percentage},
                        "break_even_point_percentage": fin.break_even_percentage,
                        "total_project_cost": fin.total_project_cost,
                        "estimated_financeable_loan": fin.bank_loan_requirement,
                        "monthly_emi": fin.breakdown_json.get("monthly_emi") if fin.breakdown_json else 8500.0,
                        "project_financing": {
                            "total_project_cost": fin.total_project_cost,
                            "estimated_financeable_loan": fin.bank_loan_requirement,
                            "promoter_contribution": fin.promoter_contribution
                        }
                    }

            # D. OrchestrationRecord (Stage 8, 9, 11)
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
                        or res.get("stage8_opportunity_evaluation")
                        or out.get("opportunity_evaluation")
                        or out.get("opportunity_result")
                    )
                if not request.financial_analysis:
                    request.financial_analysis = (
                        res.get("finance_engine")
                        or res.get("financial_analysis")
                        or res.get("stage9_financial_analysis")
                        or out.get("financial_analysis")
                        or out.get("financial_planning")
                    )
                if not request.risk_analysis:
                    request.risk_analysis = (
                        res.get("risk_engine")
                        or res.get("risk_analysis")
                        or res.get("stage11_risk_analysis")
                        or out.get("risk_analysis")
                    )

        # -------------------------------------------------------------
        # Strict Upstream Dependency Validation (Stages 8, 9, 10, 11)
        # -------------------------------------------------------------
        missing_deps = []
        if not request.opportunity_result and not raw_market_evidence:
            missing_deps.append("STAGE_8")
        if not request.financial_analysis:
            missing_deps.append("STAGE_9")
        if not request.entrepreneur_readiness or not entrepreneur_profile_engine.is_stage10_complete(request.entrepreneur_readiness):
            missing_deps.append("STAGE_10")
        if not request.risk_analysis:
            missing_deps.append("STAGE_11")

        if missing_deps:
            logger.warning(f"[FEASIBILITY API BLOCKED] Dependencies not ready: {missing_deps}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "DEPENDENCY_NOT_READY",
                    "stage": "STAGE_12_FEASIBILITY",
                    "missing": missing_deps,
                    "missing_dependencies": missing_deps,
                    "message": f"Feasibility analysis requires completion of upstream stages: {', '.join(missing_deps)}."
                }
            )

        # -------------------------------------------------------------
        # 2. Execute Stage 12 Feasibility Engine
        # -------------------------------------------------------------
        response = feasibility_engine.evaluate_feasibility(
            request=request,
            raw_market_evidence=raw_market_evidence
        )


        # -------------------------------------------------------------
        # 3. Persist to PostgreSQL FeasibilityResult table
        # -------------------------------------------------------------
        if target_uuid:
            try:
                existing = db.query(FeasibilityResult).filter(
                    (FeasibilityResult.id == target_uuid) | (FeasibilityResult.session_id == target_uuid)
                ).first()

                out_json = response.model_dump()

                if existing:
                    existing.overall_feasibility_score = response.overall_feasibility_score
                    existing.viability_status = response.decision
                    existing.recommendation = response.recommendation
                    existing.confidence_score = response.confidence_score
                    existing.market_score = response.pillar_scores.get("market_opportunity", {}).score if hasattr(response.pillar_scores.get("market_opportunity"), "score") else 0.0
                    existing.financial_score = response.pillar_scores.get("financial_viability", {}).score if hasattr(response.pillar_scores.get("financial_viability"), "score") else 0.0
                    existing.entrepreneur_fit_score = response.pillar_scores.get("entrepreneur_readiness", {}).score if hasattr(response.pillar_scores.get("entrepreneur_readiness"), "score") else 0.0
                    existing.risk_resilience_score = response.pillar_scores.get("risk_resilience", {}).score if hasattr(response.pillar_scores.get("risk_resilience"), "score") else 0.0
                    existing.pillar_scores = out_json.get("pillar_scores", {})
                    existing.critical_gates = out_json.get("critical_gates", [])
                    existing.positive_drivers = out_json.get("positive_drivers", [])
                    existing.key_constraints = out_json.get("key_constraints", [])
                    existing.conditions = out_json.get("conditions", [])
                    existing.strengths = out_json.get("dynamic_swot", {}).get("strengths", [])
                    existing.weaknesses = out_json.get("dynamic_swot", {}).get("weaknesses", [])
                    existing.opportunities = out_json.get("dynamic_swot", {}).get("opportunities", [])
                    existing.threats = out_json.get("dynamic_swot", {}).get("threats", [])
                    existing.pivot_recommendations = out_json.get("pivot_recommendations", [])
                    existing.calculation_provenance = out_json.get("calculation_provenance", [])
                    existing.ml_prediction = out_json.get("ml_prediction", {})
                    db.commit()
                else:
                    rec = FeasibilityResult(
                        id=target_uuid,
                        session_id=uuid.UUID(session_id) if session_id else target_uuid,
                        overall_feasibility_score=response.overall_feasibility_score,
                        viability_status=response.decision,
                        recommendation=response.recommendation,
                        confidence_score=response.confidence_score,
                        market_score=response.pillar_scores.get("market_opportunity", {}).score if hasattr(response.pillar_scores.get("market_opportunity"), "score") else 0.0,
                        financial_score=response.pillar_scores.get("financial_viability", {}).score if hasattr(response.pillar_scores.get("financial_viability"), "score") else 0.0,
                        entrepreneur_fit_score=response.pillar_scores.get("entrepreneur_readiness", {}).score if hasattr(response.pillar_scores.get("entrepreneur_readiness"), "score") else 0.0,
                        risk_resilience_score=response.pillar_scores.get("risk_resilience", {}).score if hasattr(response.pillar_scores.get("risk_resilience"), "score") else 0.0,
                        pillar_scores=out_json.get("pillar_scores", {}),
                        critical_gates=out_json.get("critical_gates", []),
                        positive_drivers=out_json.get("positive_drivers", []),
                        key_constraints=out_json.get("key_constraints", []),
                        conditions=out_json.get("conditions", []),
                        strengths=out_json.get("dynamic_swot", {}).get("strengths", []),
                        weaknesses=out_json.get("dynamic_swot", {}).get("weaknesses", []),
                        opportunities=out_json.get("dynamic_swot", {}).get("opportunities", []),
                        threats=out_json.get("dynamic_swot", {}).get("threats", []),
                        pivot_recommendations=out_json.get("pivot_recommendations", []),
                        calculation_provenance=out_json.get("calculation_provenance", []),
                        ml_prediction=out_json.get("ml_prediction", {})
                    )
                    db.add(rec)
                    db.commit()
            except Exception as db_err:
                logger.warning(f"[FEASIBILITY DB PERSIST WARNING] {db_err}")
                db.rollback()

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FEASIBILITY API ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feasibility engine evaluation failed: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Stage 12 Feasibility Engine Health Check"
)
async def feasibility_health():
    return {
        "service": "feasibility-engine",
        "status": "healthy",
        "stage": 12,
        "engine": "KALPA_FEASIBILITY_SYNTHESIS_ENGINE",
        "version": "1.0.0",
        "dependencies": {
            "database": "healthy",
            "stage8": "available",
            "stage9": "available",
            "stage10": "available",
            "stage11": "available"
        },
        "pillars_configured": ["MARKET_OPPORTUNITY", "FINANCIAL_VIABILITY", "ENTREPRENEUR_READINESS", "RISK_RESILIENCE"],
        "critical_gates_configured": ["FINANCIAL_CAPACITY", "CRITICAL_INFRASTRUCTURE", "MARKET_CAPACITY", "STATUTORY_COMPLIANCE"],
        "ml_adapter_status": "NOT_CONFIGURED"
    }



@router.post(
    "/pivot-suggestions",
    response_model=List[PivotCandidate],
    status_code=status.HTTP_200_OK,
    summary="Get Contextual Pivot Recommendations"
)
async def get_pivot_suggestions(
    business_profile: Optional[Dict[str, Any]] = None,
    entrepreneur_profile: Optional[Dict[str, Any]] = None,
    available_capital: Optional[float] = 500000.0
):
    feature_vector = feasibility_feature_vector_builder.build_feature_vector(
        financial_data={"total_project_cost": available_capital},
        entrepreneur_data=entrepreneur_profile or {}
    )
    return pivot_advisor_engine.recommend_pivots(
        feature_vector=feature_vector,
        business_profile=business_profile,
        entrepreneur_data=entrepreneur_profile
    )


@router.get(
    "/{analysis_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Feasibility Result by Analysis ID"
)
async def get_feasibility_by_analysis_id(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    try:
        target_uuid = uuid.UUID(analysis_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis_id UUID format")

    record = db.query(FeasibilityResult).filter(
        (FeasibilityResult.id == target_uuid) | (FeasibilityResult.session_id == target_uuid)
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No feasibility evaluation record found for analysis_id='{analysis_id}'"
        )

    return {
        "analysis_id": str(record.id),
        "session_id": str(record.session_id) if record.session_id else str(record.id),
        "overall_feasibility_score": record.overall_feasibility_score,
        "decision": record.viability_status,
        "recommendation": record.recommendation,
        "confidence_score": record.confidence_score,
        "pillar_scores": record.pillar_scores,
        "critical_gates": record.critical_gates,
        "positive_drivers": record.positive_drivers,
        "key_constraints": record.key_constraints,
        "conditions": record.conditions,
        "dynamic_swot": {
            "strengths": record.strengths or [],
            "weaknesses": record.weaknesses or [],
            "opportunities": record.opportunities or [],
            "threats": record.threats or []
        },
        "pivot_recommendations": record.pivot_recommendations or [],
        "calculation_provenance": record.calculation_provenance or [],
        "ml_prediction": record.ml_prediction or {}
    }


@router.get(
    "/{analysis_id}/calculation",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Feasibility Calculation Audit Trail"
)
async def get_feasibility_calculation_trace(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    try:
        target_uuid = uuid.UUID(analysis_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis_id UUID format")

    record = db.query(FeasibilityResult).filter(
        (FeasibilityResult.id == target_uuid) | (FeasibilityResult.session_id == target_uuid)
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No feasibility evaluation record found for analysis_id='{analysis_id}'"
        )

    return record.calculation_provenance or []

