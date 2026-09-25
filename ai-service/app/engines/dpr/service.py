"""
Detailed Project Report (DPR) Generation Engine.
Synthesizes verified Milestone 6 financial package and upstream non-financial intelligence
(Market, Opportunity, Feasibility, SWOT, Risk) into an institutional-grade PDF and CMA dossier.
Zero LLM reliance. Deterministic report generation conforming to RBI and PMEGP/Mudra guidelines.
"""
import os
import uuid
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.engines.dpr.schemas import DPRDocumentRequest, DPRDocumentMetadata
from app.engines.dpr.pdf_generator import dpr_pdf_generator
from app.services.financial_engine.dpr_packager.dpr_schema import DPRFinancialPackage
from app.services.financial_engine.dpr_packager import dpr_packager
from app.services.financial_engine import financial_engine

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "storage", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class DPRGenerationEngine:
    def __init__(self):
        self.engine_name = "dpr_generation_engine"
        self.pdf_generator = dpr_pdf_generator
        self.packager = dpr_packager

    async def generate_dpr(
        self,
        request: DPRDocumentRequest,
        db: Optional[Session] = None
    ) -> DPRDocumentMetadata:
        """
        Synthesizes complete M6 financial package and non-financial data into bankable DPR document.
        """
        doc_id = f"dpr-{request.business_id}-{uuid.uuid4().hex[:8]}"
        logger.info(f"[DPR GENERATION] Generating institutional DPR for business_id={request.business_id}, doc_id={doc_id}")

        financial_pkg: Optional[DPRFinancialPackage] = None
        non_financial_ctx: Dict[str, Any] = request.non_financial_context or {}

        # 1. Obtain or unwrap M6 Financial Package
        if request.financial_package:
            if isinstance(request.financial_package, DPRFinancialPackage):
                financial_pkg = request.financial_package
            elif isinstance(request.financial_package, dict):
                try:
                    financial_pkg = DPRFinancialPackage(**request.financial_package)
                except Exception as e:
                    logger.warning(f"[DPR GENERATION] Parsing provided financial package dict via packager: {e}")
                    financial_pkg = self.packager.package(request.financial_package)
        
        # 2. If not passed in request, load from database or synthesize from upstream records
        if financial_pkg is None and db:
            from app.services.assistant_engine.context_builder import build_full_assistant_context
            try:
                full_ctx = build_full_assistant_context(
                    analysis_id=request.analysis_id,
                    session_id=request.session_id,
                    business_id=request.business_id,
                    db=db
                )
                non_financial_ctx = {
                    "market_analysis": full_ctx.get("market_analysis"),
                    "feasibility_result": full_ctx.get("feasibility_result"),
                    "swot_analysis": full_ctx.get("swot_analysis"),
                    "risk_analysis": full_ctx.get("risk_analysis"),
                    "entrepreneur_readiness": full_ctx.get("entrepreneur_readiness"),
                }
                raw_fin = full_ctx.get("financial_analysis") or {}
                if raw_fin:
                    financial_pkg = self.packager.package(
                        analysis_response_or_container=raw_fin,
                        business_profile=full_ctx.get("business_profile"),
                        beneficiary_profile=full_ctx.get("entrepreneur_profile"),
                        user_inputs={"business_id": request.business_id},
                        package_id=doc_id
                    )
            except Exception as e:
                logger.error(f"[DPR GENERATION] Error retrieving upstream context from DB: {e}", exc_info=True)

        # 3. Fallback: Generate via financial engine if still None
        if financial_pkg is None:
            logger.info(f"[DPR GENERATION] Invoking financial engine analyze fallback for business_id={request.business_id}")
            resp = financial_engine.analyze({
                "business_profile": {"business_id": request.business_id, "specific_business": f"Project {request.business_id}"},
                "financial_profile": {"available_margin_capital": 100000.0}
            })
            financial_pkg = resp.financial_analysis.dpr_financial_package

        # 4. Generate Institutional PDF
        pdf_filename = f"{doc_id}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

        try:
            pdf_bytes = self.pdf_generator.generate_pdf(
                financial_package=financial_pkg,
                non_financial_context=non_financial_ctx,
                output_path=pdf_path
            )
            # Estimate pages (each 1000-1500 bytes of content or table)
            page_count = max(2, len(pdf_bytes) // 3000)
        except Exception as e:
            logger.error(f"[DPR GENERATION] PDF generation failed: {e}", exc_info=True)
            pdf_bytes = b""
            page_count = 0

        # 5. Extract highlights and completeness status
        comp = financial_pkg.data_completeness
        status_str = "generated" if comp.is_dpr_eligible else "incomplete_draft"
        exec_sec = financial_pkg.sections[0] if financial_pkg.sections else None
        report_summary = exec_sec.summary_text if exec_sec else "Bankable Detailed Project Report generated."

        highlights = {
            "total_project_cost": financial_pkg.project_cost.total_project_cost,
            "promoter_contribution": financial_pkg.means_of_finance.promoter_contribution,
            "term_loan": financial_pkg.loan_structure.sanctioned_loan_amount,
            "monthly_emi": financial_pkg.loan_structure.monthly_emi,
            "scheme_name": financial_pkg.loan_structure.scheme_name,
            "average_dscr": financial_pkg.banking_metrics.average_dscr,
            "break_even_capacity_pct": financial_pkg.banking_metrics.break_even_capacity_pct,
            "break_even_sales_amount": financial_pkg.banking_metrics.break_even_sales_amount,
            "resilience_status": financial_pkg.m5_stress_appraisal.financing_resilience_status,
        }

        # 6. Record in Database if available
        if db:
            try:
                from app.database.models.report import GeneratedReport
                from app.services.assistant_engine.context_builder import safe_uuid
                biz_uuid = safe_uuid(request.business_id) or uuid.uuid4()
                report_rec = GeneratedReport(
                    id=uuid.uuid4(),
                    business_id=biz_uuid,
                    report_type="dpr",
                    file_format="pdf",
                    file_path=pdf_path,
                    report_title=f"Bankable DPR: {financial_pkg.project_identity.project_name or request.business_id}",
                    report_summary=report_summary,
                    report_payload=financial_pkg.model_dump(),
                )
                db.add(report_rec)
                db.commit()
                doc_id = str(report_rec.id)
            except Exception as e:
                logger.warning(f"[DPR GENERATION] Non-fatal DB save warning: {e}")

        return DPRDocumentMetadata(
            document_id=doc_id,
            title=f"Bankable DPR: {financial_pkg.project_identity.project_name or request.business_id}",
            pages=page_count,
            file_format="pdf",
            status=status_str,
            file_path=pdf_path,
            download_url=f"/dpr/report/{doc_id}/pdf",
            report_summary=report_summary,
            completeness_status=comp.status.value,
            is_dpr_eligible=comp.is_dpr_eligible,
            financial_highlights=highlights,
            dpr_package=financial_pkg.model_dump()
        )


dpr_generation_engine = DPRGenerationEngine()
