"""
Geospatial Analysis Layer for Stage 6 Market Intelligence Engine.
Computes deterministic Haversine distance, dynamically assigns catchment zones
(PRIMARY, SECONDARY, EXTENDED, OUTSIDE) based on business benchmarks,
and transparently identifies geographic precision gaps.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
from app.services.market_intelligence_engine.data_cleaning import data_cleaning_service
from app.services.market_intelligence_engine.schemas import (
    CatchmentZone,
    GeospatialAnalysisResult,
    CleanedCompetitorItem,
    CleanedSupplyHub
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


class GeospatialAnalysisService:
    def classify_catchment_zone(
        self,
        distance_km: float,
        primary_radius_km: float,
        secondary_radius_km: float
    ) -> CatchmentZone:
        """
        Classifies an entity's distance relative to business catchment benchmarks.
        """
        if distance_km <= primary_radius_km:
            return CatchmentZone.PRIMARY
        elif distance_km <= secondary_radius_km:
            return CatchmentZone.SECONDARY
        elif distance_km <= (secondary_radius_km * 2.0):
            return CatchmentZone.EXTENDED
        else:
            return CatchmentZone.OUTSIDE

    def analyze_geospatial_context(
        self,
        location_context: Dict[str, Any],
        competitors: Dict[str, List[CleanedCompetitorItem]],
        supply_hubs: List[CleanedSupplyHub],
        benchmarks: Dict[str, Any]
    ) -> GeospatialAnalysisResult:
        """
        Executes complete geospatial intelligence analysis.
        """
        resolved = location_context.get("resolved_location") or {}
        raw_coords = location_context.get("coordinates") or {}
        lat, lon, has_valid_coords = data_cleaning_service.clean_coordinates(raw_coords)

        # Catchment thresholds from benchmark
        catchment_bm = benchmarks.get("catchment", {})
        primary_radius = float(catchment_bm.get("primary_radius_km", 15.0))
        secondary_radius = float(catchment_bm.get("secondary_radius_km", 50.0))

        # Precision analysis
        target_precision = location_context.get("geographic_precision") or "village"
        data_precision = "village" if has_valid_coords else ("district" if resolved.get("district") else "state")
        precision_hierarchy = {"village": 1, "gram_panchayat": 2, "block": 3, "tehsil": 3, "district": 4, "state": 5}
        precision_gap = precision_hierarchy.get(data_precision.lower(), 4) > precision_hierarchy.get(target_precision.lower(), 1)

        primary_entities_count = 0
        secondary_entities_count = 0

        # Assign catchment zones to competitors
        for comp_category in competitors.values():
            for comp in comp_category:
                comp.catchment_zone = self.classify_catchment_zone(
                    comp.distance_km,
                    primary_radius,
                    secondary_radius
                )
                if comp.catchment_zone == CatchmentZone.PRIMARY:
                    primary_entities_count += 1
                elif comp.catchment_zone == CatchmentZone.SECONDARY:
                    secondary_entities_count += 1

        # Assign catchment zones to supply hubs
        for hub in supply_hubs:
            hub.catchment_zone = self.classify_catchment_zone(
                hub.distance_km,
                primary_radius,
                secondary_radius
            )
            if hub.catchment_zone == CatchmentZone.PRIMARY:
                primary_entities_count += 1
            elif hub.catchment_zone == CatchmentZone.SECONDARY:
                secondary_entities_count += 1

        confidence = float(location_context.get("resolution_confidence") or 0.90)
        if precision_gap:
            confidence = round(confidence * 0.85, 2)

        return GeospatialAnalysisResult(
            coordinates={"latitude": lat, "longitude": lon} if has_valid_coords else {},
            resolved_location=resolved,
            target_precision=target_precision,
            data_precision=data_precision,
            precision_gap=precision_gap,
            primary_radius_km=primary_radius,
            secondary_radius_km=secondary_radius,
            entities_in_primary_zone=primary_entities_count,
            entities_in_secondary_zone=secondary_entities_count,
            confidence=confidence
        )


geospatial_service = GeospatialAnalysisService()
