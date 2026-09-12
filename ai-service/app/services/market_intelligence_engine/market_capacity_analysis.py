"""
Market Capacity Analysis Layer for Stage 6 Market Intelligence Engine.
Synthesizes demand evidence signals, multi-tier competitive pressure,
catchment scaling, and benchmark saturation limits to estimate enterprise market capacity.
"""
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    MarketCapacityStatus,
    EvidenceConfidenceLevel,
    MarketCapacityAnalysisResult,
    DemandEvidenceAnalysisResult,
    CompetitionAnalysisResult,
    SupplyEcosystemAnalysisResult
)


class MarketCapacityAnalysisService:
    def analyze_market_capacity(
        self,
        demand_analysis: DemandEvidenceAnalysisResult,
        competition_analysis: CompetitionAnalysisResult,
        supply_analysis: SupplyEcosystemAnalysisResult,
        benchmarks: Dict[str, Any]
    ) -> MarketCapacityAnalysisResult:
        """
        Executes deterministic market capacity synthesis.
        """
        d_score = demand_analysis.demand_signal_score
        c_score = competition_analysis.competitive_pressure_score
        s_risk = supply_analysis.supply_risk_score

        # Net capacity score: high demand raises capacity, high competition reduces capacity
        net_score = round(d_score - (0.60 * c_score) - (0.15 * s_risk), 3)

        limitations: List[str] = []

        if demand_analysis.data_coverage < 0.60:
            limitations.append("Catchment demand estimated using district-level expenditure proxies rather than micro-census surveys")

        if competition_analysis.direct.cluster_count > 0:
            limitations.append("Aggregated competitor clusters detected; individual competitor throughput is proxy-estimated")

        if supply_analysis.accessibility != "HIGH":
            limitations.append("Supply chain logistics add friction to full market capacity utilization")

        # Classification Status
        if net_score >= 0.35:
            status = MarketCapacityStatus.AVAILABLE
            signal = "HIGH_EXPANSION_CAPACITY"
        elif net_score >= 0.05:
            status = MarketCapacityStatus.LIMITED
            signal = "MODERATE_PRESSURE"
        else:
            status = MarketCapacityStatus.SATURATED
            signal = "HIGH_SATURATION_PRESSURE"

        # Evidence Confidence Level
        if demand_analysis.confidence >= 0.85 and competition_analysis.confidence >= 0.85:
            ev_level = EvidenceConfidenceLevel.HIGH
        elif demand_analysis.confidence >= 0.70:
            ev_level = EvidenceConfidenceLevel.MODERATE
        else:
            ev_level = EvidenceConfidenceLevel.LOW

        confidence = round(
            (demand_analysis.confidence * 0.40) +
            (competition_analysis.confidence * 0.40) +
            (supply_analysis.confidence * 0.20),
            2
        )

        return MarketCapacityAnalysisResult(
            status=status,
            capacity_signal=signal,
            net_capacity_score=net_score,
            competition_pressure=competition_analysis.competitive_pressure.value,
            demand_signal=demand_analysis.demand_signal_strength.value,
            evidence_level=ev_level,
            limitations=limitations,
            confidence=confidence
        )


market_capacity_service = MarketCapacityAnalysisService()
