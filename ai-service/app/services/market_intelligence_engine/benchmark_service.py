"""
Centralized Benchmark Service for Stage 6 Market Intelligence Engine.
Loads, normalizes, and queries curated business-specific benchmarks from KALPA knowledge repositories.
Provides deterministic comparison metrics against NABARD, NSSO, Census, and industry standards.
"""
import json
import os
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import BenchmarkComparison
from app.core.logging import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


class BenchmarkService:
    def __init__(self):
        self._market_benchmarks: Dict[str, Dict[str, Any]] = {}
        self._financial_benchmarks: Dict[str, Dict[str, Any]] = {}
        self._business_profiles: Dict[str, Dict[str, Any]] = {}
        self._ontology_nodes: Dict[str, Dict[str, Any]] = {}
        self._alias_map: Dict[str, str] = {}
        self._loaded = False
        self._load_benchmarks()

    def _load_benchmarks(self):
        if self._loaded:
            return

        # 1. Load market_benchmarks.json
        mb_path = os.path.join(DATA_DIR, "curated", "benchmarks", "market_benchmarks.json")
        if os.path.exists(mb_path):
            try:
                with open(mb_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        bid = item.get("business_node_id")
                        if bid:
                            self._market_benchmarks[bid] = item
                            self._alias_map[bid.lower()] = bid
                            for alias in item.get("aliases", []):
                                self._alias_map[alias.lower()] = bid
                logger.info(f"[BENCHMARK SERVICE] Loaded {len(self._market_benchmarks)} market benchmark profiles")
            except Exception as e:
                logger.warning(f"[BENCHMARK SERVICE] Could not load market_benchmarks.json: {e}")

        # 2. Load business_profiles.json
        bp_path = os.path.join(DATA_DIR, "curated", "business", "business_profiles.json")
        if os.path.exists(bp_path):
            try:
                with open(bp_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        bid = item.get("business_id")
                        if bid:
                            self._business_profiles[bid] = item
                            self._alias_map[bid.lower()] = bid
                            for alias in item.get("aliases", []):
                                self._alias_map[alias.lower()] = bid
            except Exception as e:
                logger.warning(f"[BENCHMARK SERVICE] Could not load business_profiles.json: {e}")

        # 3. Load business_ontology.json
        onto_path = os.path.join(DATA_DIR, "ontology", "business_ontology.json")
        if os.path.exists(onto_path):
            try:
                with open(onto_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        oid = item.get("id")
                        spec = item.get("specific_business")
                        if oid:
                            self._ontology_nodes[oid] = item
                            self._alias_map[oid.lower()] = oid
                        if spec:
                            self._alias_map[spec.lower()] = oid or spec.lower()
                        for syn in item.get("synonyms", []):
                            if oid:
                                self._alias_map[syn.lower()] = oid
            except Exception as e:
                logger.warning(f"[BENCHMARK SERVICE] Could not load business_ontology.json: {e}")

        self._loaded = True

    def resolve_business_id(self, identifier: Optional[str]) -> str:
        """Resolves alias or concept text to canonical business_node_id."""
        if not identifier:
            return "general_enterprise"
        cleaned = identifier.strip().lower().replace(" ", "_").replace("-", "_")
        if cleaned in self._alias_map:
            return self._alias_map[cleaned]
        for k, v in self._alias_map.items():
            if k in cleaned or cleaned in k:
                return v
        return cleaned

    def get_benchmarks_for_business(self, business_id_or_concept: Optional[str]) -> Dict[str, Any]:
        """
        Retrieves consolidated benchmarks for a specific business concept.
        Falls back gracefully to realistic generic enterprise benchmarks if not found.
        """
        self._load_benchmarks()
        canonical_id = self.resolve_business_id(business_id_or_concept)

        mb = self._market_benchmarks.get(canonical_id, {})
        bp = self._business_profiles.get(canonical_id, {})
        onto = self._ontology_nodes.get(canonical_id, {})

        # If direct lookup missed, search by partial match
        if not mb:
            for k, v in self._market_benchmarks.items():
                if k in canonical_id or canonical_id in k:
                    mb = v
                    break

        # Fallback defaults
        default_catchment = {
            "primary_radius_km": 10.0,
            "secondary_radius_km": 30.0,
            "target_population_min": 10000,
            "target_household_count_min": 2000
        }
        default_competition = {
            "saturation_threshold_units_per_10k_pop": 1.5,
            "healthy_competition_ratio": 0.7,
            "direct_competitors": ["Same category independent units"],
            "indirect_competitors": ["Adjacent regional suppliers"]
        }
        default_seasonality = {
            "jan": 1.0, "feb": 1.0, "mar": 1.0, "apr": 1.0,
            "may": 1.0, "jun": 1.0, "jul": 1.0, "aug": 1.0,
            "sep": 1.0, "oct": 1.1, "nov": 1.1, "dec": 1.1
        }
        default_infrastructure = [
            "all_weather_road_access",
            "electricity_grid_connection",
            "potable_water_source"
        ]

        catchment = mb.get("catchment", default_catchment)
        competition = mb.get("competition_and_saturation", default_competition)
        seasonality = mb.get("seasonality_factors", default_seasonality)
        seasonality_notes = mb.get("seasonality_notes", "Stable baseline demand across year")

        # Infrastructure requirements from ontology or profile
        infra_reqs = (
            onto.get("infrastructure_requirements") or
            [d.get("license_name") for d in bp.get("licenses_and_registrations", [])] or
            default_infrastructure
        )

        provenance = mb.get("provenance", {
            "source_id": "NABARD_MSME_NORMS",
            "organization": "National Bank for Agriculture and Rural Development",
            "document_name": "NABARD / MSME Sector Analysis & Model Enterprise Guidelines",
            "publication_year": 2024
        })

        return {
            "business_node_id": canonical_id,
            "business_title": mb.get("business_title") or bp.get("business_name") or canonical_id.replace("_", " ").title(),
            "catchment": catchment,
            "competition": competition,
            "seasonality": seasonality,
            "seasonality_notes": seasonality_notes,
            "infrastructure_requirements": infra_reqs,
            "supply_access": {
                "ideal_distance_km": catchment.get("primary_radius_km", 15.0),
                "acceptable_distance_km": catchment.get("secondary_radius_km", 50.0),
                "critical_inputs": bp.get("cost_drivers") or ["Raw materials", "Operating energy", "Logistics"]
            },
            "demand_drivers": mb.get("demand_drivers", []),
            "target_customer_segments": mb.get("target_customer_segments", []),
            "provenance": provenance
        }

    def compare_metric(
        self,
        benchmark_id: str,
        benchmark_name: str,
        actual_value: Any,
        benchmark_value: Any,
        unit: str = "",
        higher_is_better: bool = True,
        source: Optional[str] = None
    ) -> BenchmarkComparison:
        """
        Calculates deterministic comparison result and variance percentage.
        """
        if actual_value is None or benchmark_value is None:
            return BenchmarkComparison(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                benchmark_value=benchmark_value,
                actual_value=actual_value,
                comparison_result="UNAVAILABLE",
                variance_percentage=None,
                source=source
            )

        try:
            act_num = float(actual_value)
            bm_num = float(benchmark_value)
            if bm_num == 0:
                variance = 0.0
            else:
                variance = round(((act_num - bm_num) / bm_num) * 100.0, 2)

            if higher_is_better:
                if variance >= 10.0:
                    result = "FAVORABLE_EXCEEDS_BENCHMARK"
                elif variance >= -15.0:
                    result = "MEETS_BENCHMARK_STANDARD"
                else:
                    result = "BELOW_RECOMMENDED_BENCHMARK"
            else:
                # Lower is better (e.g. competition saturation, distance to supply)
                if variance <= -10.0:
                    result = "FAVORABLE_BELOW_THRESHOLD"
                elif variance <= 15.0:
                    result = "WITHIN_ACCEPTABLE_LIMITS"
                else:
                    result = "EXCEEDS_RISK_THRESHOLD"

            return BenchmarkComparison(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                benchmark_value=benchmark_value,
                actual_value=actual_value,
                comparison_result=result,
                variance_percentage=variance,
                source=source
            )
        except (ValueError, TypeError):
            return BenchmarkComparison(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                benchmark_value=benchmark_value,
                actual_value=actual_value,
                comparison_result="QUALITATIVE_MATCH" if str(actual_value).lower() in str(benchmark_value).lower() else "DIVERGENT",
                variance_percentage=None,
                source=source
            )


benchmark_service = BenchmarkService()
