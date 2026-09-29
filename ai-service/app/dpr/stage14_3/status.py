"""
Stage 14.3: Deterministic DPR Status Determination.
Computes institutional status strictly via deterministic criteria:
- DRAFT_DPR: Critical project information missing or validation failed.
- BANK_REVIEW_READY: Core project cost, financing, P&L, DSCR reconciled, but supporting documents pending.
- READY_FOR_SUBMISSION: All required evidence present, zero reconciliation failures, full readiness passed.
"""
from typing import Dict, Any, List, Tuple
from app.dpr.stage14_3.document_schema import DPRStatus, FinancialIntegritySummary


class DPRStatusEngine:
    """
    Evaluates data completeness, financial reconciliation, and document verification to assign DPR status.
    """

    @classmethod
    def evaluate_status(
        cls,
        package: Any,
        financial_integrity: FinancialIntegritySummary,
        missing_critical_fields: List[str],
        documents_summary: Dict[str, Any]
    ) -> Tuple[DPRStatus, List[str]]:
        reasons: List[str] = []

        # 1. Any critical financial validation FAIL immediately results in DRAFT_DPR
        if financial_integrity.overall_status == "FAIL" or financial_integrity.failed_count > 0:
            reasons.append(f"Financial reconciliation failed ({financial_integrity.failed_count} errors)")
            return DPRStatus.DRAFT_DPR, reasons

        # 2. Critical fields missing -> DRAFT_DPR
        if missing_critical_fields:
            reasons.append(f"Critical inputs not resolved: {', '.join(missing_critical_fields[:3])}")
            return DPRStatus.DRAFT_DPR, reasons

        # 3. Check document completeness for READY_FOR_SUBMISSION
        # Check if verified documents exist and whether any essential documents are pending
        pending_docs = []
        if isinstance(documents_summary, dict):
            for doc_name, doc_info in documents_summary.items():
                st = ""
                if isinstance(doc_info, dict):
                    st = doc_info.get("status", "")
                elif isinstance(doc_info, str):
                    st = doc_info
                if st in ("PENDING", "DOCUMENT_PENDING", "REQUIRED"):
                    pending_docs.append(doc_name)

        if pending_docs:
            reasons.append(f"Core financials balanced; pending supporting documents: {', '.join(pending_docs[:3])}")
            return DPRStatus.BANK_REVIEW_READY, reasons

        # 4. Check warnings in financial integrity
        if financial_integrity.warning_count > 0:
            reasons.append("Minor financial warnings noted; suitable for institutional review")
            return DPRStatus.BANK_REVIEW_READY, reasons

        reasons.append("All core financials reconciled and required documentation verified")
        return DPRStatus.READY_FOR_SUBMISSION, reasons
