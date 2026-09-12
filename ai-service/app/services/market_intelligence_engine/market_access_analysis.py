"""
Market Access Analysis Layer for Stage 6 Market Intelligence Engine.
Evaluates catchment reachability, transport connectivity, and customer access channels.
"""
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    MarketAccessAnalysisResult,
    CleanedDemographicMetric,
    CleanedSupplyHub,
    CleanedCompetitorItem
)


class MarketAccessAnalysisService:
    def analyze_market_access(
        self,
        demographics: List[CleanedDemographicMetric],
        supply_hubs: List[CleanedSupplyHub],
        substitutes: List[CleanedCompetitorItem],
        benchmarks: Dict[str, Any]
    ) -> MarketAccessAnalysisResult:
        """
        Executes deterministic market access analysis.
        """
        catchment_bm = benchmarks.get("catchment", {})
        primary_km = float(catchment_bm.get("primary_radius_km", 15.0))
        secondary_km = float(catchment_bm.get("secondary_radius_km", 50.0))

        demo_map = {d.metric: d.value for d in demographics}
        pop_val = demo_map.get("total_population") or 25000

        # Estimate primary vs secondary population reach
        primary_reach = int(pop_val * 0.45)
        secondary_reach = int(pop_val * 0.55)

        # Access rating based on trading hubs / bazaars in catchment
        has_local_hub = any(h.distance_km <= primary_km for h in supply_hubs)
        has_weekly_haat = any("haat" in s.business_name.lower() or "bazaar" in s.business_name.lower() for s in substitutes)

        if has_local_hub and has_weekly_haat:
            accessibility = "HIGH"
            geo_score = 0.88
        elif has_local_hub or has_weekly_haat:
            accessibility = "MODERATE"
            geo_score = 0.72
        else:
            accessibility = "RESTRICTED"
            geo_score = 0.50

        return MarketAccessAnalysisResult(
            catchment={
                "primary_radius_km": primary_km,
                "secondary_radius_km": secondary_km,
                "primary_population_reach": primary_reach,
                "secondary_population_reach": secondary_reach
            },
            population_reach=int(pop_val),
            accessibility=accessibility,
            geographic_accessibility_score=geo_score,
            transport_reach_km=primary_km,
            confidence=0.82
        )


market_access_service = MarketAccessAnalysisService()
