"""
Competition Analysis Layer for Stage 6 Market Intelligence Engine.
Evaluates multi-tier competitive pressure (DIRECT, ADJACENT, SUBSTITUTE)
using proximity-weighted decay, saturation threshold benchmarks, and cluster detection.
"""
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    CatchmentZone,
    CompetitivePressureLevel,
    CompetitorCategoryAnalysis,
    CompetitionAnalysisResult,
    CleanedCompetitorItem
)


class CompetitionAnalysisService:
    def _proximity_decay(self, distance_km: float, primary_km: float, secondary_km: float) -> float:
        """Computes proximity decay factor (1.0 in primary, 0.5 in secondary, 0.2 in extended)."""
        if distance_km <= primary_km:
            return 1.0
        elif distance_km <= secondary_km:
            return 0.5
        elif distance_km <= (secondary_km * 2.0):
            return 0.2
        return 0.05

    def analyze_competition(
        self,
        competitors: Dict[str, List[CleanedCompetitorItem]],
        demographics: Dict[str, Any],
        benchmarks: Dict[str, Any]
    ) -> CompetitionAnalysisResult:
        """
        Executes deterministic multi-tier competitor analysis.
        """
        catchment_bm = benchmarks.get("catchment", {})
        primary_km = float(catchment_bm.get("primary_radius_km", 15.0))
        secondary_km = float(catchment_bm.get("secondary_radius_km", 50.0))

        comp_bm = benchmarks.get("competition", {})
        saturation_threshold = float(comp_bm.get("saturation_threshold_units_per_10k_pop", 1.2))

        pop_val = demographics.get("total_population", 50000)
        try:
            population = float(pop_val) if pop_val else 50000.0
        except (ValueError, TypeError):
            population = 50000.0

        # 1. Analyze Category Tiers
        categories_analyzed: Dict[str, CompetitorCategoryAnalysis] = {}
        weighted_sums: Dict[str, float] = {"direct": 0.0, "adjacent": 0.0, "substitute": 0.0}
        total_competitors = 0
        drivers: List[str] = []

        category_weights = {
            "direct": 1.0,
            "adjacent": 0.5,
            "substitute": 0.25
        }

        for cat_key in ["direct", "adjacent", "substitute"]:
            items = competitors.get(cat_key, [])
            count = len(items)
            total_competitors += count
            cluster_count = sum(1 for item in items if item.is_cluster)

            proximity_weighted = 0.0
            primary_items = []
            secondary_items = []

            for item in items:
                decay = self._proximity_decay(item.distance_km, primary_km, secondary_km)
                proximity_weighted += decay
                if item.catchment_zone == CatchmentZone.PRIMARY:
                    primary_items.append(f"{item.business_name} ({item.distance_km:.1f} km)")
                else:
                    secondary_items.append(f"{item.business_name} ({item.distance_km:.1f} km)")

            weighted_sums[cat_key] = round(proximity_weighted, 2)

            categories_analyzed[cat_key] = CompetitorCategoryAnalysis(
                count=count,
                cluster_count=cluster_count,
                proximity_weighted_count=round(proximity_weighted, 2),
                items=items
            )

            # Driver explanations
            if count > 0:
                tier_label = cat_key.capitalize()
                if primary_items:
                    drivers.append(f"{len(primary_items)} {tier_label} competitor(s) in primary catchment: {', '.join(primary_items[:2])}")
                if secondary_items:
                    drivers.append(f"{len(secondary_items)} {tier_label} competitor(s) in secondary catchment: {', '.join(secondary_items[:2])}")

        # 2. Compute Composite Density and Pressure
        direct_count = categories_analyzed["direct"].count
        pop_in_10k = max(1.0, population / 10000.0)
        competition_density = round(direct_count / pop_in_10k, 3)

        # Composite weighted pressure: direct (1.0) + adjacent (0.5) + substitute (0.25)
        composite_weighted_count = (
            category_weights["direct"] * weighted_sums["direct"] +
            category_weights["adjacent"] * weighted_sums["adjacent"] +
            category_weights["substitute"] * weighted_sums["substitute"]
        )

        # Normalized pressure score (0.0 to 1.0 scale relative to saturation threshold)
        # Expected saturation unit count in catchment = saturation_threshold * pop_in_10k
        expected_saturation_units = max(1.0, saturation_threshold * min(pop_in_10k, 5.0))
        pressure_score = min(1.0, round(composite_weighted_count / (expected_saturation_units * 1.5), 3))

        # Classification level
        if pressure_score <= 0.30:
            pressure_level = CompetitivePressureLevel.LOW
        elif pressure_score <= 0.65:
            pressure_level = CompetitivePressureLevel.MODERATE
        elif pressure_score <= 0.85:
            pressure_level = CompetitivePressureLevel.HIGH
        else:
            pressure_level = CompetitivePressureLevel.SEVERE

        if not drivers:
            drivers.append("No active competitors discovered within local catchment radius")

        return CompetitionAnalysisResult(
            direct=categories_analyzed["direct"],
            adjacent=categories_analyzed["adjacent"],
            substitute=categories_analyzed["substitute"],
            total_competitors=total_competitors,
            competition_density_per_10k=competition_density,
            competitive_pressure_score=pressure_score,
            competitive_pressure=pressure_level,
            drivers=drivers,
            saturation_threshold=saturation_threshold,
            confidence=0.86,
            calculation_method="weighted_proximity_density"
        )


competition_service = CompetitionAnalysisService()
