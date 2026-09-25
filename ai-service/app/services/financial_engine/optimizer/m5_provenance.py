"""
Provenance Tracker for M5 Stress Testing & Financing Optimizer.
Provides end-to-end transparent data lineage for every metric, scenario calculation,
and policy optimization decision.
"""
from typing import List, Any, Optional
from app.services.financial_engine.optimizer.m5_schema import M5ProvenanceRecord


class M5ProvenanceBuilder:
    """
    Collects and serializes data lineage records across M5 sub-engines.
    """

    def __init__(self) -> None:
        self.records: List[M5ProvenanceRecord] = []

    def record(
        self,
        metric: str,
        value: Any,
        source: str,
        source_reference: Optional[str] = None,
        calculation_method: Optional[str] = None,
        input_dependencies: Optional[List[str]] = None,
        status: str = "RESOLVED",
        confidence: float = 1.0,
        scenario_id: Optional[str] = None
    ) -> M5ProvenanceRecord:
        rec = M5ProvenanceRecord(
            metric=metric,
            value=value,
            source=source,
            source_reference=source_reference,
            calculation_method=calculation_method,
            input_dependencies=input_dependencies or [],
            status=status,
            confidence=confidence,
            scenario_id=scenario_id
        )
        self.records.append(rec)
        return rec

    def get_records(self) -> List[M5ProvenanceRecord]:
        return list(self.records)
