"""
Confidence and Evidence Quality Propagation Service for Stage 6 Market Intelligence Engine.
Computes explainable component-level confidence, overall market confidence,
proxy dependency scoring, and tracks evidence gaps.
"""
from typing import Dict, Any, List
from app.services.market_intelligence_engine.schemas import (
    EvidenceQuality,
    EvidenceGap,
    MarketIndicators,
    CleanedDemographicMetric,
    CleanedInfrastructureRequirement,
    DataStatus
)


class ConfidenceService:
    def calculate_evidence_quality(
        self,
        indicators: MarketIndicators,
        demographics: List[CleanedDemographicMetric],
        infrastructure_reqs: List[CleanedInfrastructureRequirement],
        stage5_quality: Dict[str, Any]
    ) -> EvidenceQuality:
        """
        Synthesizes component-level confidence scores and identifies explicit evidence gaps.
        """
        geo_conf = indicators.geospatial_analysis.confidence
        comp_conf = indicators.competition.confidence
        infra_conf = indicators.infrastructure.confidence
        sup_conf = indicators.supply_ecosystem.confidence
        dem_conf = indicators.demand_evidence.confidence
        cap_conf = indicators.market_capacity.confidence

        component_confidence = {
            "geospatial_analysis": geo_conf,
            "competition_analysis": comp_conf,
            "infrastructure_analysis": infra_conf,
            "supply_ecosystem_analysis": sup_conf,
            "demand_evidence_analysis": dem_conf,
            "market_capacity_analysis": cap_conf
        }

        # Calculate Proxy Dependency Score
        total_items = max(1, len(demographics) + indicators.competition.total_competitors + indicators.supply_ecosystem.hub_count)
        proxy_items = sum(1 for d in demographics if d.proxy)
        proxy_items += indicators.competition.direct.cluster_count + indicators.competition.adjacent.cluster_count
        proxy_dependency = round(min(1.0, proxy_items / total_items), 2)

        # Collect Evidence Gaps
        data_gaps: List[EvidenceGap] = []

        # 1. Infrastructure Gaps
        if indicators.infrastructure.readiness.value == "UNKNOWN_DATA_GAP" or infra_conf < 0.50:
            data_gaps.append(
                EvidenceGap(
                    gap_id="GAP-INFRA-001",
                    category="INFRASTRUCTURE",
                    description="No empirical infrastructure access records retrieved in Stage 5 data; utility and shed readiness unverified.",
                    severity="HIGH",
                    impact="Infrastructure confidence discounted to 0.30; requires on-ground validation."
                )
            )

        # 2. Precision Gap
        if indicators.geospatial_analysis.precision_gap:
            data_gaps.append(
                EvidenceGap(
                    gap_id="GAP-GEO-002",
                    category="GEOSPATIAL",
                    description=f"Data geographic precision ({indicators.geospatial_analysis.data_precision}) is coarser than target resolution ({indicators.geospatial_analysis.target_precision}).",
                    severity="MEDIUM",
                    impact="Catchment demographic counts are district-level scaled proxies."
                )
            )

        # 3. Supply Gaps
        if indicators.supply_ecosystem.supply_risk.value in ["HIGH", "ELEVATED_DUE_TO_DATA_GAP"]:
            data_gaps.append(
                EvidenceGap(
                    gap_id="GAP-SUPPLY-003",
                    category="SUPPLY_CHAIN",
                    description="Critical inputs lack dedicated local sourcing hubs within primary catchment radius.",
                    severity="MEDIUM",
                    impact="Raw material logistics risk is elevated."
                )
            )

        # Weighted Overall Confidence
        # Demographics/Demand (25%) + Competition (25%) + Geospatial (15%) + Supply (15%) + Capacity (10%) + Infra (10%)
        overall_confidence = round(
            (0.25 * dem_conf) +
            (0.25 * comp_conf) +
            (0.15 * geo_conf) +
            (0.15 * sup_conf) +
            (0.10 * cap_conf) +
            (0.10 * infra_conf),
            2
        )

        return EvidenceQuality(
            overall_confidence=overall_confidence,
            component_confidence=component_confidence,
            proxy_dependency=proxy_dependency,
            data_gaps=data_gaps
        )


confidence_service = ConfidenceService()
