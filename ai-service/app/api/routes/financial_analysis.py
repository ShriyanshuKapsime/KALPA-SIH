"""
Financial Analysis API Router (Stage 9).
Exposes REST endpoints for deterministic project financing, scheme routing,
loan management, amortization, profitability projections, and standalone loan calculator.
"""
import logging
from typing import Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models.finance import FinancialProfile
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.swot import SwotResult

from app.schemas.financial_analysis import (
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    FinancialCalculatorRequest,
    FinancialCalculatorResponse
)
from app.services.financial_engine import financial_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial-analysis", tags=["Stage 9: Financial Engine"])


def _persist_financial_record(
    payload: FinancialAnalysisRequest,
    response: FinancialAnalysisResponse,
    db: Session
) -> None:
    try:
        import uuid
        target_uuid = None
        for cand in [payload.analysis_id, payload.session_id]:
            if cand:
                try:
                    target_uuid = uuid.UUID(str(cand))
                    break
                except Exception:
                    pass

        fa = response.financial_analysis
        if not fa:
            return

        tot_cost = fa.project_cost_analysis.total_project_cost if fa.project_cost_analysis else (
            fa.project_financing.total_project_cost if fa.project_financing else 0.0
        )
        prom_margin = fa.capital_structure.promoter_contribution if fa.capital_structure else (
            fa.project_financing.promoter_contribution if fa.project_financing else 0.0
        )
        loan_amt = fa.loan_management.principal if fa.loan_management else (
            fa.project_financing.financeable_loan if fa.project_financing else 0.0
        )
        scheme_name = None
        if fa.scheme_recommendation and fa.scheme_recommendation.recommended_scheme:
            scheme_name = getattr(fa.scheme_recommendation.recommended_scheme, "value", str(fa.scheme_recommendation.recommended_scheme))

        ann_rev = 0.0
        ann_opex = 0.0
        ann_pat = 0.0
        if fa.profit_loss_statement and fa.profit_loss_statement.years:
            y1 = fa.profit_loss_statement.years[0]
            ann_rev = y1.total_revenue or 0.0
            ann_opex = y1.operating_expenses or 0.0
            ann_pat = y1.profit_after_tax or 0.0

        dscr_val = 0.0
        if fa.debt_service:
            dscr_val = fa.debt_service.average_dscr or fa.debt_service.minimum_dscr or 0.0

        bep_val = 0.0
        if fa.break_even_analysis:
            bep_val = fa.break_even_analysis.break_even_capacity_utilization_percentage or 0.0

        avail_margin = float(payload.financial_profile.available_margin_capital) if (payload.financial_profile and payload.financial_profile.available_margin_capital is not None) else prom_margin
        breakdown = {
            "total_project_cost": tot_cost,
            "promoter_contribution": prom_margin,
            "bank_loan_requirement": loan_amt,
            "term_loan": loan_amt,
            "applicable_scheme_name": scheme_name,
            "projected_annual_revenue": ann_rev,
            "projected_operating_expenses": ann_opex,
            "projected_net_profit": ann_pat,
            "dscr": dscr_val,
            "break_even_percentage": bep_val,
            "monthly_emi": fa.loan_management.monthly_emi if fa.loan_management else None,
            "annual_interest_rate": fa.loan_management.annual_interest_rate if fa.loan_management else None,
            "tenure_months": fa.loan_management.tenure_months if fa.loan_management else None,
            "retained_reserve": max(0.0, round(avail_margin - float(prom_margin), 2)),
            "scheme_matches": [sc.model_dump() for sc in (fa.scheme_recommendation.eligible_schemes or [])] if fa.scheme_recommendation else [],
            "dpr_financial_package": fa.dpr_financial_package.model_dump() if fa.dpr_financial_package else None,
        }

        fin_ctx_dict = None
        if hasattr(fa, "financial_context") and fa.financial_context:
            fin_ctx_dict = fa.financial_context.model_dump() if hasattr(fa.financial_context, "model_dump") else fa.financial_context
        elif hasattr(response, "financial_context") and response.financial_context:
            fin_ctx_dict = response.financial_context.model_dump() if hasattr(response.financial_context, "model_dump") else response.financial_context

        if fin_ctx_dict:
            breakdown["financial_context"] = fin_ctx_dict

        if target_uuid:
            prof = db.query(StructuredBusinessProfile).filter(
                (StructuredBusinessProfile.id == target_uuid) |
                (StructuredBusinessProfile.session_id == target_uuid)
            ).first()
            if prof and isinstance(prof.profile_json, dict):
                pj = dict(prof.profile_json)
                pj["financial_analysis"] = breakdown
                if fin_ctx_dict:
                    pj["financial_context"] = fin_ctx_dict
                prof.profile_json = pj

            # Invalidate any stale cached SWOT result so recalculating finance immediately refreshes SWOT
            try:
                db.query(SwotResult).filter(
                    (SwotResult.id == target_uuid) | (SwotResult.session_id == target_uuid)
                ).delete(synchronize_session=False)
            except Exception as swot_err:
                logger.debug(f"[API STAGE 9] SWOT cache invalidation notice: {swot_err}")

            fin_rec = db.query(FinancialProfile).filter(
                (FinancialProfile.id == target_uuid) |
                (FinancialProfile.business_id == target_uuid)
            ).first()
            if fin_rec:
                fin_rec.total_project_cost = tot_cost
                fin_rec.promoter_contribution = prom_margin
                fin_rec.bank_loan_requirement = loan_amt
                fin_rec.applicable_scheme_name = scheme_name
                fin_rec.projected_annual_revenue = ann_rev
                fin_rec.projected_operating_expenses = ann_opex
                fin_rec.projected_net_profit = ann_pat
                fin_rec.debt_service_coverage_ratio = dscr_val
                fin_rec.break_even_percentage = bep_val
                fin_rec.breakdown_json = breakdown
            db.commit()
    except Exception as ex:
        db.rollback()
        logger.warning(f"[API STAGE 9] Non-fatal financial profile persistence notice: {ex}")


@router.post("/analyze", response_model=FinancialAnalysisResponse)
async def analyze_financial_profile(
    payload: FinancialAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Executes deterministic Stage 9 financial analysis for an active MSME profile.
    Calculates project financing, scheme routing, capital allocation, loan management,
    amortization schedule, profitability, cash flows, break-even, DSCR, and financial viability.
    """
    try:
        logger.info(
            f"[API STAGE 9] Received financial analysis request: "
            f"analysis_id={payload.analysis_id}, session_id={payload.session_id}, "
            f"margin_capital={payload.financial_profile.available_margin_capital}"
        )
        response = financial_engine.analyze(payload)
        _persist_financial_record(payload, response, db)
        return response
    except Exception as e:
        logger.error(f"[API STAGE 9] Error during financial evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Financial evaluation failed: {str(e)}"
        )


@router.post("/calculator", response_model=FinancialCalculatorResponse)
async def calculate_loan_and_scheme(payload: FinancialCalculatorRequest):
    """
    Standalone interactive loan and margin calculator endpoint.
    Supports margin-to-loan, cost-to-margin, and loan-to-EMI calculation modes.
    """
    try:
        logger.info(f"[API STAGE 9] Received standalone calculator request: {payload}")
        response = financial_engine.calculate(payload)
        return response
    except Exception as e:
        logger.error(f"[API STAGE 9] Error during standalone calculation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Financial calculation failed: {str(e)}"
        )


@router.post("/dpr-package")
async def get_dpr_financial_package(payload: Union[FinancialAnalysisRequest, Dict[str, Any]] = Body(...)):
    """
    Milestone 6: Returns the canonical Bankable DPR / CMA Financial Package.
    Orchestrates verified M1–M5 outputs, 18 deterministic report sections,
    CMA statements, and data completeness audit with zero metric recalculation.
    """
    try:
        logger.info("[API STAGE 9/M6] Received request for canonical DPR Financial Package")
        if isinstance(payload, dict) and "financial_analysis" in payload:
            # Already analyzed response passed
            pkg = financial_engine.get_dpr_package(payload)
        else:
            resp = financial_engine.analyze(payload)
            pkg = resp.financial_analysis.dpr_financial_package
        return pkg
    except Exception as e:
        logger.error(f"[API STAGE 9/M6] Error generating DPR Financial Package: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"DPR financial packaging failed: {str(e)}"
        )


@router.get("/health")
async def get_financial_engine_health():
    """
    Returns the operational status and capabilities of the Deterministic Financial Engine.
    """
    return financial_engine.health()

