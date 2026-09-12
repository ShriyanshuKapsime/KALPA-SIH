"""
Feature Builder for Stage 6 Market Intelligence Engine.
Constructs the standardized 'market_features' dictionary serving as the strict contract
between Stage 6 Market Intelligence Engine and Stage 7 Demand Prediction ML Model.
"""
from typing import Dict, Any, List
from app.services.market_intelligence_engine.schemas import (
    MarketFeatures,
    MarketIndicators,
    CleanedDemographicMetric
)


class FeatureBuilderService:
    def build_market_features(
        self,
        business_context: Dict[str, Any],
        location_context: Dict[str, Any],
        demographics: List[CleanedDemographicMetric],
        indicators: MarketIndicators,
        benchmarks: Dict[str, Any]
    ) -> MarketFeatures:
        """
        Compiles the complete 10-tier feature dictionary for Stage 7 ML ingestion.
        """
        geo = indicators.geospatial_analysis
        comp = indicators.competition
        dem = indicators.demand_evidence
        inf = indicators.infrastructure
        sup = indicators.supply_ecosystem
        acc = indicators.market_access
        sea = indicators.seasonality
        cap = indicators.market_capacity

        # 1. Business Features
        bus_features = {
            "business_id": business_context.get("business_id") or benchmarks.get("business_node_id", "general"),
            "business_title": business_context.get("specific_business") or benchmarks.get("business_title", "Enterprise"),
            "sector": business_context.get("sector") or "Agriculture & Allied",
            "nic_code": business_context.get("nic_code") or "01461",
            "target_population_min": benchmarks.get("catchment", {}).get("target_population_min", 10000),
            "saturation_threshold_per_10k": benchmarks.get("competition", {}).get("saturation_threshold_units_per_10k_pop", 1.2)
        }

        # 2. Location Features
        coords = geo.coordinates or {}
        resolved = geo.resolved_location or {}
        loc_features = {
            "latitude": coords.get("latitude", 0.0),
            "longitude": coords.get("longitude", 0.0),
            "state": resolved.get("state", ""),
            "district": resolved.get("district", ""),
            "target_precision": geo.target_precision,
            "data_precision": geo.data_precision,
            "precision_gap": geo.precision_gap
        }

        # 3. Demographic Features
        demo_map = {d.metric: d.value for d in demographics}
        demo_features = {
            "total_population": demo_map.get("total_population", 0),
            "total_households": demo_map.get("total_households", 0),
            "female_population": demo_map.get("female_population", 0),
            "rural_percentage": demo_map.get("rural_percentage", 50.0),
            "population_density": demo_map.get("population_density", 0),
            "sex_ratio": demo_map.get("sex_ratio", 900)
        }

        # 4. Economic Features
        cons_proxy = dem.consumption_proxy or {}
        eco_features = {
            "consumption_proxy_raw": cons_proxy.get("raw_value", 3000.0),
            "consumption_normalized_score": cons_proxy.get("normalized_score", 0.65),
            "purchasing_power_tier": dem.purchasing_power_proxy.get("purchasing_power_tier", "TIER_3_RURAL_GROWTH"),
            "purchasing_power_index": dem.purchasing_power_proxy.get("estimated_index", 65.0)
        }

        # 5. Market Access Features
        access_features = {
            "primary_radius_km": geo.primary_radius_km,
            "secondary_radius_km": geo.secondary_radius_km,
            "primary_population_reach": acc.catchment.get("primary_population_reach", 0),
            "accessibility_rating": acc.accessibility,
            "geographic_accessibility_score": acc.geographic_accessibility_score,
            "transport_reach_km": acc.transport_reach_km
        }

        # 6. Competition Features
        comp_features = {
            "direct_competitor_count": comp.direct.count,
            "direct_proximity_weighted": comp.direct.proximity_weighted_count,
            "adjacent_competitor_count": comp.adjacent.count,
            "substitute_channel_count": comp.substitute.count,
            "competition_density_per_10k": comp.competition_density_per_10k,
            "competitive_pressure_score": comp.competitive_pressure_score,
            "competitive_pressure_level": comp.competitive_pressure.value
        }

        # 7. Supply Features
        supply_features = {
            "supply_hub_count": sup.hub_count,
            "nearest_hub_distance_km": sup.nearest_hub_distance_km or 25.0,
            "input_coverage_ratio": sup.critical_input_coverage.get("coverage_ratio", 0.50),
            "supply_accessibility": sup.accessibility,
            "supply_risk_level": sup.supply_risk.value,
            "supply_risk_score": sup.supply_risk_score
        }

        # 8. Infrastructure Features
        infra_features = {
            "infrastructure_readiness": inf.readiness.value,
            "infrastructure_readiness_score": inf.readiness_score,
            "satisfied_requirements_count": inf.satisfied_requirements_count,
            "total_requirements_count": inf.total_requirements_count,
            "critical_data_gaps_count": len(inf.critical_gaps)
        }

        # 9. Seasonal Features
        sea_features = {
            "peak_multiplier": sea.peak_multiplier,
            "lean_multiplier": sea.lean_multiplier,
            "annual_seasonal_volatility": sea.annual_volatility,
            "seasonal_risk_level": sea.seasonal_risk.value,
            "peak_months_count": len(sea.peak_months),
            "lean_months_count": len(sea.lean_months)
        }

        # 10. Demand Evidence Features
        demand_features = {
            "demand_signal_strength": dem.demand_signal_strength.value,
            "demand_signal_score": dem.demand_signal_score,
            "data_coverage_ratio": dem.data_coverage,
            "net_market_capacity_score": cap.net_capacity_score,
            "market_capacity_status": cap.status.value,
            "market_capacity_signal": cap.capacity_signal
        }

        return MarketFeatures(
            business_features=bus_features,
            location_features=loc_features,
            demographic_features=demo_features,
            economic_features=eco_features,
            market_access_features=access_features,
            competition_features=comp_features,
            supply_features=supply_features,
            infrastructure_features=infra_features,
            seasonal_features=sea_features,
            demand_evidence_features=demand_features
        )


feature_builder_service = FeatureBuilderService()
