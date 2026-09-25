"""
Evidence Resolver.
Resolves financial driver values from existing KALPA data sources
following strict priority order. Never silently returns zero.
"""
import logging
from typing import Dict, Any, Optional
from app.services.financial_engine.intelligence.confidence import (
    ResolvedAssumption, SourceType, AssumptionStatus, AssumptionType, Provenance
)
from app.services.financial_engine.intelligence.driver_registry import DriverDefinition

logger = logging.getLogger(__name__)


class EvidenceResolver:
    """
    For every required financial driver, resolves using priority:
    1. User-provided value
    2. Existing verified business-specific value
    3. Existing KALPA market/location evidence
    4. Existing knowledge/benchmark repository
    5. Scheme/configuration data
    6. Explicit configured benchmark/range
    7. Mark as USER_REQUIRED if materially important
    NEVER silently replace unknown with zero.
    """

    def resolve_driver(
        self,
        driver_def: DriverDefinition,
        user_inputs: Optional[Dict[str, Any]] = None,
        benchmark_data: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        scheme_data: Optional[Dict[str, Any]] = None,
    ) -> ResolvedAssumption:
        user_inputs = user_inputs or {}
        benchmark_data = benchmark_data or {}
        market_data = market_data or {}
        scheme_data = scheme_data or {}
        did = driver_def.driver_id

        # 1. Priority 1: User-provided value
        if did in user_inputs and user_inputs[did] is not None:
            val = user_inputs[did]
            logger.debug(f"[EVIDENCE RESOLVER] driver={did} resolved via USER_INPUT value={val}")
            return ResolvedAssumption(
                driver_id=did, value=val, unit=driver_def.unit,
                source_type=SourceType.USER_INPUT, confidence=1.0,
                status=AssumptionStatus.RESOLVED, assumption_type=AssumptionType.USER_INPUT,
                user_confirmed=True, required=True, criticality=driver_def.criticality,
                provenance=Provenance(source_type=SourceType.USER_INPUT, description="User-provided value", confidence=1.0),
            )

        # 2. Priority 2: Verified business-specific evidence
        verified_dict = user_inputs.get("verified_evidence") if isinstance(user_inputs.get("verified_evidence"), dict) else {}
        ver_val = verified_dict.get(did) if did in verified_dict else user_inputs.get(f"{did}_verified")
        if ver_val is not None:
            logger.debug(f"[EVIDENCE RESOLVER] driver={did} resolved via VERIFIED_EVIDENCE value={ver_val}")
            return ResolvedAssumption(
                driver_id=did, value=ver_val, unit=driver_def.unit,
                source_type=SourceType.DERIVED, source_id="VERIFIED_PROFILE",
                confidence=0.95, status=AssumptionStatus.RESOLVED,
                assumption_type=AssumptionType.VERIFIED_EVIDENCE, user_confirmed=True,
                required=True, criticality=driver_def.criticality,
                provenance=Provenance(source_type=SourceType.DERIVED, source_id="VERIFIED_PROFILE",
                                      description="Verified business profile evidence", confidence=0.95),
            )

        # 3. Priority 3: Market intelligence engine evidence
        mkt_val = market_data.get(did)
        if mkt_val is None and did == "monthly_rent":
            mkt_val = market_data.get("commercial_rent_monthly") or market_data.get("commercial_rent_pm")
        if mkt_val is not None:
            logger.debug(f"[EVIDENCE RESOLVER] driver={did} resolved via MARKET_ENGINE value={mkt_val}")
            return ResolvedAssumption(
                driver_id=did, value=mkt_val, unit=driver_def.unit,
                source_type=SourceType.MARKET_ENGINE, source_id="STAGE_6_MARKET",
                confidence=0.75, status=AssumptionStatus.RESOLVED,
                assumption_type=AssumptionType.VERIFIED_EVIDENCE, user_confirmed=False,
                required=True, criticality=driver_def.criticality,
                provenance=Provenance(source_type=SourceType.MARKET_ENGINE, source_id="STAGE_6_MARKET",
                                      description="Market intelligence engine evidence", confidence=0.75),
            )

        # 4. Priority 4: Curated Benchmark / Knowledge repository
        bm_val = None
        if driver_def.default_benchmark_key and driver_def.default_benchmark_key in benchmark_data:
            bm_val = benchmark_data[driver_def.default_benchmark_key]
        elif did in benchmark_data:
            bm_val = benchmark_data[did]

        if bm_val is not None:
            logger.debug(f"[EVIDENCE RESOLVER] driver={did} resolved via BENCHMARK value={bm_val}")
            return ResolvedAssumption(
                driver_id=did, value=bm_val, unit=driver_def.unit,
                source_type=SourceType.BENCHMARK, source_id="KALPA_BENCHMARK_DB",
                confidence=0.82, status=AssumptionStatus.BENCHMARKED,
                assumption_type=AssumptionType.BENCHMARK, user_confirmed=False,
                required=True, criticality=driver_def.criticality,
                provenance=Provenance(source_type=SourceType.BENCHMARK, source_id="KALPA_BENCHMARK_DB",
                                      description=f"Curated industry benchmark ({driver_def.default_benchmark_key or did})",
                                      confidence=0.82),
            )

        # 5. Priority 5: Scheme configuration data
        sch_val = scheme_data.get(did)
        if sch_val is not None:
            logger.debug(f"[EVIDENCE RESOLVER] driver={did} resolved via SCHEME_CONFIG value={sch_val}")
            return ResolvedAssumption(
                driver_id=did, value=sch_val, unit=driver_def.unit,
                source_type=SourceType.SCHEME_CONFIG, confidence=0.90,
                status=AssumptionStatus.RESOLVED, assumption_type=AssumptionType.FACT,
                user_confirmed=False, required=True, criticality=driver_def.criticality,
                provenance=Provenance(source_type=SourceType.SCHEME_CONFIG,
                                      description="Government financing scheme rule", confidence=0.90),
            )

        # 6. Priority 6: Unknown — mark as USER_REQUIRED if high criticality (Never silently substitute zero)
        if driver_def.criticality == "HIGH":
            logger.info(f"[EVIDENCE RESOLVER] driver={did} UNRESOLVED criticality=HIGH -> USER_REQUIRED")
            return ResolvedAssumption(
                driver_id=did, value=None, unit=driver_def.unit,
                source_type=SourceType.UNKNOWN, confidence=0.0,
                status=AssumptionStatus.USER_REQUIRED,
                assumption_type=AssumptionType.MODEL_ASSUMPTION,
                user_confirmed=False, required=True, criticality="HIGH",
                notes="No benchmark or evidence available. User input required.",
            )

        # 7. Low/Medium criticality unknown — leave as UNKNOWN (Never silently substitute zero)
        return ResolvedAssumption(
            driver_id=did, value=None, unit=driver_def.unit,
            source_type=SourceType.UNKNOWN, confidence=0.0,
            status=AssumptionStatus.UNKNOWN,
            assumption_type=AssumptionType.MODEL_ASSUMPTION,
            user_confirmed=False, required=False, criticality=driver_def.criticality,
            notes="No benchmark data available. Non-critical driver.",
        )


# Global singleton
evidence_resolver = EvidenceResolver()
