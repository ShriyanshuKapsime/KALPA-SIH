"""
Provenance engine for M4 Banking Appraisal & Viability Engine.
Tracks lineage, authoritative sources, formulas, and dependencies for all material metrics.
Strict rule: Derived metrics must never be labeled USER. Inherited Stage 9 values must be labeled STAGE9.
"""
from typing import List, Optional, Any, Union
from app.services.financial_engine.appraisal.appraisal_schema import (
    MetricProvenanceRecord,
    MetricSource,
    AppraisalStatus
)


class ProvenanceBuilder:
    """
    Builds auditable provenance records for M4 metrics.
    """

    def __init__(self):
        self.records: List[MetricProvenanceRecord] = []

    def record(
        self,
        metric: str,
        value: Optional[Any],
        source: MetricSource,
        source_reference: Optional[str] = None,
        calculation_method: Optional[str] = None,
        status: AppraisalStatus = AppraisalStatus.RESOLVED,
        dependencies: Optional[List[str]] = None,
        confidence: float = 1.0,
        period: Optional[Union[int, str]] = None
    ) -> MetricProvenanceRecord:
        # Enforce non-fabrication provenance invariants
        if source == MetricSource.USER and calculation_method is not None:
            # Derived metrics cannot be marked as pure USER input
            source = MetricSource.DERIVED

        rec = MetricProvenanceRecord(
            metric=metric,
            period=period,
            value=value,
            source=source,
            source_reference=source_reference,
            calculation_method=calculation_method,
            status=status,
            dependencies=dependencies or [],
            confidence=confidence
        )
        self.records.append(rec)
        return rec

    def get_records(self) -> List[MetricProvenanceRecord]:
        return list(self.records)


provenance_builder = ProvenanceBuilder
