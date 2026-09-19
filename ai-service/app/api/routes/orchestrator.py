"""
FastAPI Routes for Stage 4: KALPA Manager Agent / LangGraph Orchestrator.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.orchestrator import StartOrchestratorRequest, OrchestratorResponse, CanonicalWorkflowState
from app.services.orchestration.orchestrator_service import orchestrator_service
from app.core.logging import logger

router = APIRouter(prefix="/orchestrator", tags=["Stage 4 - KALPA Manager Agent"])


@router.get(
    "/workflow/{identifier}",
    response_model=CanonicalWorkflowState,
    status_code=status.HTTP_200_OK,
    summary="Get Canonical Workflow State by Analysis ID or Session ID"
)
async def get_canonical_workflow_state(
    identifier: str,
    db: Session = Depends(get_db)
):
    workflow_state = await orchestrator_service.get_workflow_state(identifier, db=db)
    if not workflow_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workflow state found for identifier='{identifier}'"
        )
    return workflow_state


@router.get(
    "/workflow-context/{identifier}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Consolidated Authoritative Workflow Context (Stage 3 -> 6 -> 8 -> 9 -> 10 -> 11)",
    description="Returns the unified workflow context containing business metadata and outputs across all pipeline stages."
)
async def get_consolidated_workflow_context(
    identifier: str,
    db: Session = Depends(get_db)
):
    ctx = await orchestrator_service.get_authoritative_workflow_context(identifier, db=db)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No workflow context found for identifier='{identifier}'"
        )
    return ctx


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start LangGraph Agentic Orchestration Asynchronously",
    description="Loads Stage 3 Profile, initializes LangGraph multi-agent orchestration in background, and returns HTTP 202 Accepted immediately."
)
async def start_orchestrator(
    request: StartOrchestratorRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    try:
        if request.sync:
            sync_res = await orchestrator_service.run_orchestrator(request, db=db)
            response.status_code = status.HTTP_200_OK
            return sync_res

        res = await orchestrator_service.start_orchestrator_async(request, db=db)
        if res.get("status") == "ALREADY_COMPLETE":
            response.status_code = status.HTTP_200_OK
        else:
            response.status_code = status.HTTP_202_ACCEPTED
        return res
    except ValueError as ve:
        logger.warning(f"[ORCHESTRATOR API WARNING] {ve}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"[ORCHESTRATOR API ERROR] Execution failure: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator start error: {str(e)}"
        )


@router.get(
    "/status/{analysis_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Live / Persisted Orchestrator Pipeline Status",
    description="Returns real-time progress (0-100%), current stage, active agent, completed stages, and final result."
)
async def get_orchestrator_status(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    st = await orchestrator_service.get_orchestrator_status(analysis_id, db=db)
    if not st:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active or persisted orchestrator pipeline found for analysis_id='{analysis_id}'"
        )
    return st


@router.get(
    "/{analysis_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Orchestration Record by Analysis ID"
)
async def get_orchestrator_by_analysis_id(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    record = await orchestrator_service.get_by_analysis_id(analysis_id, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No orchestration record found for analysis_id='{analysis_id}'"
        )
    return record


@router.get(
    "/session/{session_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Orchestration Record by Session ID"
)
async def get_orchestrator_by_session_id(
    session_id: str,
    db: Session = Depends(get_db)
):
    record = await orchestrator_service.get_by_session_id(session_id, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No orchestration record found for session_id='{session_id}'"
        )
    return record
