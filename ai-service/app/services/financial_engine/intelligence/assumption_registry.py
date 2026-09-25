"""
Assumption Resolver.
Orchestrates driver resolution for an entire financial archetype.
Produces a complete set of ResolvedAssumptions with provenance.
"""
import logging
from typing import Dict, Any, Optional, List
from app.services.financial_engine.intelligence.archetype_registry import (
    FinancialArchetype, archetype_registry
)
from app.services.financial_engine.intelligence.driver_registry import driver_registry
from app.services.financial_engine.intelligence.evidence_resolver import evidence_resolver
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, AssumptionStatus, FoundationStatus
)
from app.services.financial_engine.intelligence.provenance import ProvenanceTracker

logger = logging.getLogger(__name__)


class AssumptionResolver:
    """
    Resolves all required financial drivers for a given archetype.
    Returns structured assumptions with provenance + overall status.
    """

    def resolve_all(
        self,
        archetype: FinancialArchetype,
        user_inputs: Optional[Dict[str, Any]] = None,
        benchmark_data: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        scheme_data: Optional[Dict[str, Any]] = None,
        analysis_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns:
        {
            "archetype": "INVENTORY_RETAIL",
            "assumptions": [ResolvedAssumption, ...],
            "assumption_status": "COMPLETE" | "PARTIAL" | "USER_INPUT_REQUIRED",
            "resolved_count": int,
            "total_count": int,
            "user_required_count": int,
            "unknown_count": int,
            "assumption_confidence": float | None,
            "provenance": [...]
        }
        """
        user_inputs = user_inputs or {}
        benchmark_data = benchmark_data or {}
        market_data = market_data or {}
        scheme_data = scheme_data or {}

        drivers = driver_registry.get_drivers_for_archetype(archetype)
        tracker = ProvenanceTracker()
        assumptions: List[ResolvedAssumption] = []

        logger.info(f"[FINANCE FOUNDATION] Driver resolution started for archetype={archetype.value}, drivers={len(drivers)}")

        for drv in drivers:
            resolved = evidence_resolver.resolve_driver(
                driver_def=drv,
                user_inputs=user_inputs,
                benchmark_data=benchmark_data,
                market_data=market_data,
                scheme_data=scheme_data,
            )
            assumptions.append(resolved)
            tracker.record(resolved, analysis_id=analysis_id)

            status_label = resolved.status.value if resolved.status else "UNKNOWN"
            conf_label = f"{resolved.confidence:.2f}" if resolved.confidence else "0.00"
            logger.info(f"[FINANCE FOUNDATION] driver={drv.driver_id} status={status_label} confidence={conf_label}")

        # Compute overall status
        resolved_count = sum(1 for a in assumptions if a.is_resolved)
        user_required_count = sum(1 for a in assumptions if a.needs_user_input)
        unknown_count = sum(1 for a in assumptions if a.status == AssumptionStatus.UNKNOWN)
        total = len(assumptions)

        if user_required_count > 0:
            overall_status = FoundationStatus.USER_INPUT_REQUIRED
        elif unknown_count > 0:
            overall_status = FoundationStatus.PARTIAL
        elif resolved_count == total:
            overall_status = FoundationStatus.COMPLETE
        else:
            overall_status = FoundationStatus.PARTIAL

        # Average confidence of resolved assumptions
        resolved_confs = [a.confidence for a in assumptions if a.is_resolved]
        avg_confidence = round(sum(resolved_confs) / len(resolved_confs), 3) if resolved_confs else 0.0

        confidence_summary = {
            "overall": avg_confidence,
            "resolved": resolved_count,
            "total": total,
            "user_required": user_required_count,
            "unknown": unknown_count,
        }

        logger.info(
            f"[FINANCE FOUNDATION] Resolution complete: status={overall_status.value}, "
            f"resolved={resolved_count}/{total}, user_required={user_required_count}, unknown={unknown_count}, overall_conf={avg_confidence:.2f}"
        )

        return {
            "archetype": archetype.value,
            "assumptions": [a.to_dict() for a in assumptions],
            "assumption_status": overall_status.value,
            "resolved_count": resolved_count,
            "total_count": total,
            "user_required_count": user_required_count,
            "unknown_count": unknown_count,
            "assumption_confidence": confidence_summary,
            "provenance": tracker.get_records(),
        }


# Global singleton
assumption_resolver = AssumptionResolver()
