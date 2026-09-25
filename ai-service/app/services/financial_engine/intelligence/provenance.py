"""
Provenance Tracker.
Collects and manages provenance records for all resolved assumptions.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, Provenance, SourceType
)

logger = logging.getLogger(__name__)


class ProvenanceTracker:
    """Tracks provenance for all financial assumptions in an analysis."""

    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(self, assumption: ResolvedAssumption, analysis_id: Optional[str] = None):
        entry = {
            "analysis_id": analysis_id,
            "driver_id": assumption.driver_id,
            "value": assumption.value,
            "unit": assumption.unit,
            "source_type": assumption.source_type.value if assumption.source_type else "UNKNOWN",
            "source_id": assumption.source_id,
            "confidence": assumption.confidence,
            "status": assumption.status.value if assumption.status else "UNKNOWN",
            "user_confirmed": assumption.user_confirmed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._records.append(entry)

    def get_records(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def clear(self):
        self._records.clear()

    def summary(self) -> Dict[str, Any]:
        total = len(self._records)
        if total == 0:
            return {"total": 0, "resolved": 0, "unknown": 0, "user_required": 0}
        resolved = sum(1 for r in self._records if r["status"] in ("RESOLVED", "BENCHMARKED", "CALCULATED"))
        unknown = sum(1 for r in self._records if r["status"] == "UNKNOWN")
        user_req = sum(1 for r in self._records if r["status"] == "USER_REQUIRED")
        avg_conf = sum(r["confidence"] for r in self._records) / total if total else 0
        return {
            "total": total,
            "resolved": resolved,
            "unknown": unknown,
            "user_required": user_req,
            "average_confidence": round(avg_conf, 3),
        }


# Global singleton
provenance_tracker = ProvenanceTracker()
