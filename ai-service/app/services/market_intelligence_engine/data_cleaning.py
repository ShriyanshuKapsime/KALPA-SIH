"""
Data Cleaning and Normalization Layer for Stage 6 Market Intelligence Engine.
Ensures deterministic validation, unit standardization, coordinate verification,
and explicit data state tracking (ACTUAL, PROXY, MISSING, UNKNOWN, PARTIAL).
"""
import math
from typing import Dict, Any, List, Optional, Tuple, Union
from app.services.market_intelligence_engine.schemas import (
    DataStatus,
    CleanedDemographicMetric,
    CleanedCompetitorItem,
    CleanedDemandIndicator,
    CleanedSupplyHub,
    CleanedInfrastructureRequirement,
    CleanedSeasonalityFactor,
    SourceMetadata
)
from app.core.logging import logger


class DataCleaningService:
    def clean_coordinates(self, coords: Optional[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float], bool]:
        """
        Validates latitude and longitude coordinates.
        Returns (lat, lon, is_valid).
        """
        if not coords or not isinstance(coords, dict):
            return None, None, False

        lat_raw = coords.get("latitude") or coords.get("lat")
        lon_raw = coords.get("longitude") or coords.get("lon") or coords.get("lng")

        if lat_raw is None or lon_raw is None:
            return None, None, False

        try:
            lat = float(lat_raw)
            lon = float(lon_raw)
            if math.isnan(lat) or math.isnan(lon):
                return None, None, False
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return lat, lon, True
            return None, None, False
        except (ValueError, TypeError):
            return None, None, False

    def clean_demographics(self, raw_demographics: List[Dict[str, Any]]) -> List[CleanedDemographicMetric]:
        """
        Cleans, deduplicates, and validates demographic indicators.
        Preserves proxy status and source provenance.
        """
        cleaned: List[CleanedDemographicMetric] = []
        seen_metrics = set()

        for item in raw_demographics:
            if not isinstance(item, dict):
                continue
            metric = str(item.get("metric", "")).strip().lower()
            if not metric or metric in seen_metrics:
                continue

            raw_val = item.get("value")
            val: Union[int, float, None] = None
            data_status = DataStatus.ACTUAL

            if raw_val is None:
                data_status = DataStatus.MISSING
            else:
                try:
                    if isinstance(raw_val, float):
                        val = float(raw_val)
                    elif isinstance(raw_val, int):
                        val = int(raw_val)
                    else:
                        num_str = str(raw_val).replace(",", "").strip()
                        val = float(num_str) if "." in num_str else int(num_str)
                except (ValueError, TypeError):
                    val = None
                    data_status = DataStatus.MISSING

            is_proxy = bool(item.get("proxy", False))
            if is_proxy and data_status == DataStatus.ACTUAL:
                data_status = DataStatus.PROXY

            src_dict = item.get("source") or {}
            source = SourceMetadata(
                source_id=src_dict.get("source_id"),
                organization=src_dict.get("organization"),
                source_type=src_dict.get("source_type", "OFFICIAL_DATASET"),
                dataset_name=src_dict.get("dataset_name"),
                url=src_dict.get("url")
            )

            metric_obj = CleanedDemographicMetric(
                metric=metric,
                value=val,
                unit=str(item.get("unit", "")).strip(),
                geography=item.get("geography") or {},
                geographic_precision=item.get("geographic_precision") or "district",
                data_status=data_status,
                proxy=is_proxy,
                proxy_reason=item.get("proxy_reason"),
                source=source,
                reference_period=item.get("reference_period"),
                confidence=0.85 if is_proxy else 0.95
            )
            cleaned.append(metric_obj)
            seen_metrics.add(metric)

        return cleaned

    def clean_competitors(
        self,
        raw_competitors: Dict[str, Any]
    ) -> Dict[str, List[CleanedCompetitorItem]]:
        """
        Cleans competitors across direct, adjacent, and substitute categories.
        Preserves cluster/proxy nature.
        """
        categorized: Dict[str, List[CleanedCompetitorItem]] = {
            "direct": [],
            "adjacent": [],
            "substitute": []
        }

        if not isinstance(raw_competitors, dict):
            return categorized

        for category_key in ["direct", "adjacent", "substitute"]:
            raw_list = (
                raw_competitors.get(category_key)
                or raw_competitors.get(f"{category_key}s")
                or raw_competitors.get(f"{category_key}_competitors")
                or []
            )
            if not isinstance(raw_list, list):
                continue

            seen_names = set()
            for comp in raw_list:
                if not isinstance(comp, dict):
                    continue
                name = str(comp.get("business_name", "")).strip()
                if not name or name.lower() in seen_names:
                    continue

                dist_raw = comp.get("distance_km")
                dist = 0.0
                try:
                    if dist_raw is not None:
                        dist = float(dist_raw)
                except (ValueError, TypeError):
                    dist = 5.0

                is_cluster = "cluster" in name.lower() or "farmers" in name.lower() or "vendors" in name.lower() or "sellers" in name.lower()
                is_proxy = is_cluster or bool(comp.get("proxy", False))

                src_dict = comp.get("source") or {}
                source = SourceMetadata(
                    source_id=src_dict.get("source_id"),
                    organization=src_dict.get("organization"),
                    source_type=src_dict.get("source_type", "OFFICIAL_DATASET"),
                    dataset_name=src_dict.get("dataset_name"),
                    url=src_dict.get("url")
                )

                item = CleanedCompetitorItem(
                    competitor_type=category_key,
                    business_name=name,
                    category=comp.get("category"),
                    location=comp.get("location") or {},
                    distance_km=dist,
                    is_cluster=is_cluster,
                    is_proxy=is_proxy,
                    source=source,
                    confidence=float(comp.get("confidence") or (0.75 if is_cluster else 0.85))
                )
                categorized[category_key].append(item)
                seen_names.add(name.lower())

        return categorized

    def clean_demand_indicators(
        self,
        raw_indicators: List[Dict[str, Any]]
    ) -> List[CleanedDemandIndicator]:
        """
        Cleans demand indicators and consumption proxies.
        """
        cleaned: List[CleanedDemandIndicator] = []
        if not isinstance(raw_indicators, list):
            return cleaned

        seen = set()
        for ind in raw_indicators:
            if not isinstance(ind, dict):
                continue
            name = str(ind.get("indicator_name", "")).strip()
            if not name or name.lower() in seen:
                continue

            raw_val = ind.get("value")
            norm_val = None
            if raw_val is not None:
                try:
                    norm_val = float(str(raw_val).replace(",", "").strip())
                except (ValueError, TypeError):
                    norm_val = None

            is_proxy = "proxy" in name.lower() or bool(ind.get("proxy", False))

            src_dict = ind.get("source") or {}
            source = SourceMetadata(
                source_id=src_dict.get("source_id"),
                organization=src_dict.get("organization"),
                source_type=src_dict.get("source_type", "OFFICIAL_DATASET"),
                dataset_name=src_dict.get("dataset_name"),
                url=src_dict.get("url")
            )

            obj = CleanedDemandIndicator(
                indicator_name=name,
                category=str(ind.get("category", "general_demand")),
                raw_value=raw_val,
                normalized_value=norm_val,
                unit=str(ind.get("unit", "")).strip(),
                business_relevance=ind.get("business_relevance"),
                geography=ind.get("geography") or {},
                geographic_precision=ind.get("geographic_precision") or "district",
                data_status=DataStatus.PROXY if is_proxy else DataStatus.ACTUAL,
                proxy=is_proxy,
                source=source,
                confidence=0.80 if is_proxy else 0.90
            )
            cleaned.append(obj)
            seen.add(name.lower())

        return cleaned

    def clean_supply_access(
        self,
        raw_supply: List[Dict[str, Any]]
    ) -> List[CleanedSupplyHub]:
        """
        Cleans and normalizes supply access hubs and available commodities.
        """
        cleaned: List[CleanedSupplyHub] = []
        if not isinstance(raw_supply, list):
            return cleaned

        seen_hubs = set()
        for item in raw_supply:
            if not isinstance(item, dict):
                continue
            name = str(item.get("hub_name", "")).strip()
            if not name or name.lower() in seen_hubs:
                continue

            dist_raw = item.get("distance_km")
            dist = 10.0
            try:
                if dist_raw is not None:
                    dist = float(dist_raw)
            except (ValueError, TypeError):
                dist = 10.0

            commodities = item.get("commodities_available", [])
            if isinstance(commodities, str):
                commodities = [commodities]

            src_dict = item.get("source") or {}
            source = SourceMetadata(
                source_id=src_dict.get("source_id"),
                organization=src_dict.get("organization"),
                source_type=src_dict.get("source_type", "OFFICIAL_DATASET"),
                dataset_name=src_dict.get("dataset_name"),
                url=src_dict.get("url")
            )

            hub = CleanedSupplyHub(
                hub_name=name,
                hub_type=str(item.get("hub_type", "market")),
                distance_km=dist,
                commodities_available=commodities,
                accessibility_rating=str(item.get("accessibility_rating", "high")).lower(),
                source=source,
                data_status=DataStatus.ACTUAL,
                confidence=0.88
            )
            cleaned.append(hub)
            seen_hubs.add(name.lower())

        return cleaned

    def clean_infrastructure(
        self,
        raw_infra: List[Dict[str, Any]],
        expected_requirements: List[str]
    ) -> Tuple[List[CleanedInfrastructureRequirement], DataStatus]:
        """
        CRITICAL: If raw_infra is empty or missing, marks as UNKNOWN_DATA_GAP.
        Never falsely marks missing evidence as UNAVAILABLE or ASSUMED_AVAILABLE.
        """
        requirements: List[CleanedInfrastructureRequirement] = []

        if not raw_infra:
            # Evidence missing in Stage 5
            for req in expected_requirements:
                requirements.append(
                    CleanedInfrastructureRequirement(
                        requirement=req,
                        status="UNKNOWN",
                        evidence_available=False,
                        evidence_detail="No empirical infrastructure record in Stage 5 data",
                        impact="HIGH",
                        data_status=DataStatus.MISSING
                    )
                )
            return requirements, DataStatus.MISSING

        # If evidence was provided
        for item in raw_infra:
            if not isinstance(item, dict):
                continue
            name = str(item.get("infrastructure_type") or item.get("requirement", "")).strip()
            status_val = str(item.get("status", "AVAILABLE")).upper()
            requirements.append(
                CleanedInfrastructureRequirement(
                    requirement=name,
                    status=status_val if status_val in ["AVAILABLE", "PARTIAL", "UNAVAILABLE"] else "UNKNOWN",
                    evidence_available=True,
                    evidence_detail=item.get("detail"),
                    impact="HIGH",
                    data_status=DataStatus.ACTUAL
                )
            )

        return requirements, DataStatus.ACTUAL


data_cleaning_service = DataCleaningService()
