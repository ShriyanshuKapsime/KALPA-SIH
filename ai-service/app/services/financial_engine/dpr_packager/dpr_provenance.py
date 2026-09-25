"""
Milestone 6: DPR Provenance Preservation Layer.
Collects and preserves upstream provenance records from M1 (Intelligence Foundation),
M2 (Project Cost & Working Capital), M3 (Projections & Statements),
M4 (Banking Appraisal & Viability), M5 (Stress Testing & Financing Optimizer),
and Stage 9 Core.
Adds non-destructive packaging metadata without altering originating evidence.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.services.financial_engine.dpr_packager.dpr_schema import ProvenanceTag


class DPRProvenanceManager:
    """
    Manages provenance tracking across the DPR Financial Package.
    Ensures zero loss of upstream evidence and tags packaging operations transparently.
    """

    def __init__(self):
        self.packaging_timestamp = datetime.now(timezone.utc).isoformat()

    def consolidate_provenance(
        self,
        m1_provenance: Optional[List[Any]] = None,
        m2_provenance: Optional[List[Any]] = None,
        m3_provenance: Optional[List[Any]] = None,
        m4_provenance: Optional[List[Any]] = None,
        m5_provenance: Optional[List[Any]] = None,
        audit_metadata: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Consolidates upstream provenance records into an auditable registry,
        preserving all source references, timestamps, confidence scores, and formulas.
        """
        consolidated: List[Dict[str, Any]] = []

        def _add_records(records: Optional[List[Any]], tag: ProvenanceTag, module_name: str):
            if not records:
                return
            for rec in records:
                if isinstance(rec, dict):
                    entry = dict(rec)
                elif hasattr(rec, "model_dump"):
                    entry = rec.model_dump()
                elif hasattr(rec, "__dict__"):
                    entry = dict(rec.__dict__)
                else:
                    entry = {"raw_record": str(rec)}
                
                # Non-destructive packaging stamp
                entry["packaging_metadata"] = {
                    "packaging_tag": tag.value,
                    "packaged_at": self.packaging_timestamp,
                    "originating_milestone": module_name
                }
                consolidated.append(entry)

        _add_records(m1_provenance, ProvenanceTag.PACKAGED_FROM_M1, "Milestone 1 (Intelligence Foundation)")
        _add_records(m2_provenance, ProvenanceTag.PACKAGED_FROM_M2, "Milestone 2 (Project Cost & Working Capital)")
        _add_records(m3_provenance, ProvenanceTag.PACKAGED_FROM_M3, "Milestone 3 (Financial Projection Engine)")
        _add_records(m4_provenance, ProvenanceTag.PACKAGED_FROM_M4, "Milestone 4 (Banking Appraisal & Viability)")
        _add_records(m5_provenance, ProvenanceTag.PACKAGED_FROM_M5, "Milestone 5 (Optimizer & Stress Testing)")

        # If audit metadata has benchmark sources, preserve them
        if audit_metadata:
            benchmark_sources = getattr(audit_metadata, "benchmark_sources", None)
            if benchmark_sources and isinstance(benchmark_sources, list):
                for b_src in benchmark_sources:
                    consolidated.append({
                        "source_type": "BENCHMARK_DOCUMENT",
                        "benchmark_details": b_src,
                        "packaging_metadata": {
                            "packaging_tag": ProvenanceTag.PACKAGED_FROM_STAGE9_CORE.value,
                            "packaged_at": self.packaging_timestamp,
                            "originating_milestone": "Stage 9 Benchmark Adapter"
                        }
                    })

        return consolidated

    @staticmethod
    def get_section_provenance_tag(section_code: str) -> str:
        """
        Returns the primary authoritative upstream module tag for any given DPR section.
        """
        mapping = {
            "SEC_01_EXEC_SUMMARY": ProvenanceTag.PACKAGED_FROM_STAGE9_CORE.value,
            "SEC_02_PROJECT_COST": ProvenanceTag.PACKAGED_FROM_M2.value,
            "SEC_03_MEANS_OF_FINANCE": ProvenanceTag.PACKAGED_FROM_M3.value,
            "SEC_04_WORKING_CAPITAL": ProvenanceTag.PACKAGED_FROM_M2.value,
            "SEC_05_REVENUE_ASSUMPTIONS": ProvenanceTag.PACKAGED_FROM_M1.value,
            "SEC_06_PROFIT_LOSS": ProvenanceTag.PACKAGED_FROM_M3.value,
            "SEC_07_BALANCE_SHEET": ProvenanceTag.PACKAGED_FROM_M3.value,
            "SEC_08_CASH_FLOW": ProvenanceTag.PACKAGED_FROM_M3.value,
            "SEC_09_DEPRECIATION": ProvenanceTag.PACKAGED_FROM_M3.value,
            "SEC_10_LOAN_REPAYMENT": ProvenanceTag.PACKAGED_FROM_STAGE9_CORE.value,
            "SEC_11_BREAK_EVEN": ProvenanceTag.PACKAGED_FROM_M4.value,
            "SEC_12_DSCR_RATIOS": ProvenanceTag.PACKAGED_FROM_M4.value,
            "SEC_13_STRESS_SENSITIVITY": ProvenanceTag.PACKAGED_FROM_M5.value,
            "SEC_14_SCHEME_STRUCTURE": ProvenanceTag.PACKAGED_FROM_M5.value,
            "SEC_15_FINANCIAL_RISKS": ProvenanceTag.PACKAGED_FROM_M4.value,
            "SEC_16_ASSUMPTIONS": ProvenanceTag.PACKAGED_FROM_M1.value,
            "SEC_17_EVIDENCE_PROVENANCE": ProvenanceTag.PACKAGED_FROM_M1.value,
            "SEC_18_VALIDATION_COMPLETENESS": ProvenanceTag.PACKAGED_FROM_M5.value,
        }
        return mapping.get(section_code, ProvenanceTag.PACKAGED_FROM_STAGE9_CORE.value)


dpr_provenance_manager = DPRProvenanceManager()
