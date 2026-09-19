"""
FastAPI Routes for Stage 4: KALPA Manager Agent / LangGraph Orchestrator.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
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
    response_model=OrchestratorResponse,
    status_code=status.HTTP_200_OK,
    summary="Start LangGraph Agentic Orchestration",
    description="Loads Stage 3 Canonical Profile, executes LangGraph multi-agent orchestration, and persists results."
)
async def start_orchestrator(
    request: StartOrchestratorRequest,
    db: Session = Depends(get_db)
):
    try:
        response = await orchestrator_service.run_orchestrator(request, db=db)
        return response
    except ValueError as ve:
        logger.warning(f"[ORCHESTRATOR API WARNING] {ve}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"[ORCHESTRATOR API ERROR] Execution failure: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator execution error: {str(e)}"
        )


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
