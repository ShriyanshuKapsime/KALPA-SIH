"""
Risk Analysis API Router (Stage 11).
Exposes REST endpoints for deterministic multi-vector risk evaluation,
upstream DB evidence hydration, and health checks.
"""
from typing import Dict, Any, Optional
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.schemas.risk_analysis import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
)
from app.services.risk_engine import (
    risk_engine,
)
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine
from app.database.session import get_db
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.market import MarketEvidenceRecord, OpportunityEvaluation, MarketIntelligenceProfile
from app.database.models.finance import FinancialProfile
from app.database.models.orchestrator import OrchestrationRecord
from app.core.logging import logger

router = APIRouter(prefix="/risk-analysis", tags=["Stage 11 — Risk Engine"])


@router.post(
    "/analyze",
    response_model=RiskAnalysisResponse,
    summary="Stage 11 Deterministic Risk Engine",
    description="Evaluates Market, Financial, Operational, Seasonal, Supply Chain, Competition, and Infrastructure risks with critical risk preservation."
)
async def analyze_enterprise_risks(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    logger.info("[API STAGE 11] Received enterprise risk analysis request")
    try:
        analysis_id = payload.get("analysis_id")
        session_id = payload.get("session_id")

        # ---------------------------------------------------------------------
        # Upstream Evidence Normalization & DB Hydration
        # ---------------------------------------------------------------------
        prof_rec = None
        if analysis_id or session_id:
            # 1. Hydrate Business Profile & Entrepreneur Context from StructuredBusinessProfile
            try:
                if analysis_id:
                    try:
                        prof_rec = db.query(StructuredBusinessProfile).filter(
                            StructuredBusinessProfile.id == uuid.UUID(analysis_id)
                        ).first()
                    except Exception:
                        pass
                if not prof_rec and session_id:
                    try:
                        prof_rec = db.query(StructuredBusinessProfile).filter(
                            StructuredBusinessProfile.session_id == uuid.UUID(session_id)
                        ).order_by(StructuredBusinessProfile.created_at.desc()).first()
                    except Exception:
                        pass


                if prof_rec and prof_rec.profile_json:
                    p_json = prof_rec.profile_json
                    if not payload.get("business_profile"):
                        payload["business_profile"] = p_json.get("business_profile") or {}
                    if not payload.get("location_profile"):
                        payload["location_profile"] = p_json.get("location_profile") or {}
                    if not payload.get("financial_profile"):
                        payload["financial_profile"] = p_json.get("financial_profile") or {}
                    if not payload.get("entrepreneur_readiness") and not payload.get("entrepreneur_profile"):
                        payload["entrepreneur_profile"] = p_json.get("entrepreneur_profile") or p_json.get("user_profile") or {}
                    if not payload.get("financial_analysis") and p_json.get("financial_analysis"):
                        payload["financial_analysis"] = p_json.get("financial_analysis")
            except Exception as e:
                logger.warning(f"[API STAGE 11] StructuredBusinessProfile lookup note: {e}")

            # 2. Hydrate Stage 6 Market Intelligence from MarketEvidenceRecord
            if not payload.get("market_intelligence") and not payload.get("market_indicators"):
                try:
                    mkt_rec = None
                    if analysis_id:
                        try:
                            mkt_rec = db.query(MarketEvidenceRecord).filter(
                                MarketEvidenceRecord.id == uuid.UUID(analysis_id)
                            ).first()
                        except Exception:
                            pass
                    if not mkt_rec and session_id:
                        try:
                            mkt_rec = db.query(MarketEvidenceRecord).filter(
                                MarketEvidenceRecord.session_id == uuid.UUID(session_id)
                            ).order_by(MarketEvidenceRecord.created_at.desc()).first()
                        except Exception:
                            pass

                    if mkt_rec:
                        payload["market_intelligence"] = mkt_rec.full_profile or mkt_rec.market_evidence or {}
                        if mkt_rec.location_context and not payload.get("location_profile"):
                            payload["location_profile"] = mkt_rec.location_context
                except Exception as e:
                    logger.warning(f"[API STAGE 11] MarketEvidenceRecord lookup note: {e}")

            # 3. Hydrate Stage 9 Financial Analysis from FinancialProfile
            if not payload.get("financial_analysis"):
                try:
                    fin_rec = None
                    if analysis_id:
                        try:
                            fin_rec = db.query(FinancialProfile).filter(
                                FinancialProfile.id == uuid.UUID(analysis_id)
                            ).first()
                        except Exception:
                            pass
                    if fin_rec:
                        payload["financial_analysis"] = {
                            "debt_service": {
                                "dscr": fin_rec.debt_service_coverage_ratio,
                            },
                            "financial_viability": {
                                "debt_service_coverage_ratio": fin_rec.debt_service_coverage_ratio,
                            },
                            "break_even": {
                                "break_even_point_percentage": fin_rec.break_even_percentage,
                            },
                            "project_financing": {
                                "total_project_cost": fin_rec.total_project_cost,
                                "estimated_financeable_loan": fin_rec.bank_loan_requirement,
                                "promoter_contribution": fin_rec.promoter_contribution,
                            },
                            "breakdown": fin_rec.breakdown_json or {}
                        }
                except Exception as e:
                    logger.warning(f"[API STAGE 11] FinancialProfile lookup note: {e}")

            # 4. Hydrate Stage 8 Opportunity Evaluation from OrchestrationRecord or profile_json
            if not payload.get("opportunity_evaluation"):
                try:
                    orch_rec = None
                    if analysis_id:
                        try:
                            orch_rec = db.query(OrchestrationRecord).filter(
                                OrchestrationRecord.id == uuid.UUID(analysis_id)
                            ).first()
                        except Exception:
                            pass
                    if not orch_rec and session_id:
                        try:
                            orch_rec = db.query(OrchestrationRecord).filter(
                                OrchestrationRecord.session_id == uuid.UUID(session_id)
                            ).order_by(OrchestrationRecord.created_at.desc()).first()
                        except Exception:
                            pass

                    if orch_rec and orch_rec.orchestration_output:
                        res = orch_rec.orchestration_output.get("agent_results", {})
                        if res.get("opportunity_evaluation_engine"):
                            payload["opportunity_evaluation"] = res["opportunity_evaluation_engine"]
                except Exception as e:
                    logger.warning(f"[API STAGE 11] OpportunityEvaluation lookup note: {e}")

        # -----------------------------------------------------------------
        # 5. Dependency Validation (Stage 10 Hard Gate)
        # -----------------------------------------------------------------
        ep_data = payload.get("entrepreneur_readiness")
        if not ep_data and (payload.get("entrepreneur_profile") or (prof_rec and prof_rec.profile_json)):
            p_user = payload.get("entrepreneur_profile") or (prof_rec.profile_json.get("entrepreneur_profile") or prof_rec.profile_json.get("user_profile") if prof_rec else {})
            ep_eval = entrepreneur_profile_engine.analyze({
                "business_profile": payload.get("business_profile") or (prof_rec.profile_json.get("business_profile") if prof_rec else {}),
                "entrepreneur_profile": p_user,
                "location_profile": payload.get("location_profile")
            })
            ep_data = ep_eval
            payload["entrepreneur_readiness"] = ep_eval

        if ep_data is not None and not entrepreneur_profile_engine.is_stage10_complete(ep_data):
            missing_list = ep_data.missing_fields if hasattr(ep_data, "missing_fields") else (ep_data.get("missing_fields") or ep_data.get("pending_fields") or ["skills", "experience"])
            logger.warning(f"[API STAGE 11 BLOCKED] Stage 10 incomplete. Missing fields: {missing_list}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "STAGE_11_BLOCKED",
                    "stage": "STAGE_11_RISK",
                    "missing_dependencies": ["STAGE_10"],
                    "message": "Risk analysis requires a completed Entrepreneur Profile (Stage 10). Please answer all pending clarification questions before proceeding.",
                    "details": {"pending_fields": missing_list}
                }
            )

        result = risk_engine.analyze(payload)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API STAGE 11 ERROR] {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage 11 Risk Engine error: {str(e)}"
        )



@router.get(
    "/health",
    summary="Stage 11 Risk Engine Health Check"
)
async def get_risk_engine_health():
    return {
        "engine": "deterministic_risk_engine",
        "stage": 11,
        "status": "healthy",
        "evaluation_mode": "DETERMINISTIC_MULTI_VECTOR_SYNTHESIS",
        "categories": [
            "MARKET",
            "FINANCIAL",
            "OPERATIONAL",
            "SEASONAL",
            "SUPPLY_CHAIN",
            "COMPETITION",
            "INFRASTRUCTURE"
        ],
        "critical_ceiling_rule": "ENABLED",
        "version": "1.0.0"
    }
