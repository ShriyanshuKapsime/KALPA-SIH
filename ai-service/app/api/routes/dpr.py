"""
DPR Generation API Router (Stage 14).
Exposes REST endpoints for generating institutional-grade Bankable DPRs,
fetching DPR reports, and downloading PDF files.
"""
import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.engines.dpr.schemas import DPRDocumentRequest, DPRDocumentMetadata
from app.engines.dpr.service import dpr_generation_engine, REPORTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dpr", tags=["Stage 14: Bankable DPR Generator"])


@router.post("/generate/{business_id}", response_model=DPRDocumentMetadata)
async def generate_bankable_dpr(
    business_id: str = Path(..., description="Target business identifier or UUID"),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    Synthesizes authoritative Milestone 1–5 financial package and upstream context
    into a bankable Detailed Project Report (DPR) conforming to PMEGP / Mudra / MSME guidelines.
    Returns dossier metadata, 18-section summary, and PDF download link.
    """
    try:
        body = payload or {}
        req = DPRDocumentRequest(
            business_id=business_id,
            session_id=body.get("session_id"),
            analysis_id=body.get("analysis_id"),
            scheme_code=body.get("scheme_code") or body.get("target_scheme") or "PMEGP",
            language_code=body.get("language_code", "en"),
            report_format=body.get("report_format", "pdf"),
            financial_package=body.get("financial_package"),
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
    Retrieves full generated DPR metadata, 18 report sections, and financial highlights.
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
    # 1. Check local file by report_id
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
        # Auto-generate on the fly if needed
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
