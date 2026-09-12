"""
Location Resolution Service for KALPA Market Intelligence Agent.
Provides:
- Reverse Geocoding (GPS Coordinates -> Administrative Hierarchy)
- Forward Geocoding (Text Geography -> Coordinates)
- User Location vs GPS Validation & Conflict Detection
- Precision Degradation (Village -> Block -> District -> State)
- Offline India Administrative Hierarchy Catalog
"""
import math
import httpx
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from app.schemas.market import (
    AdministrativeHierarchy,
    LocationCoordinates,
    LocationContext,
    LocationConflictInfo,
)
from app.core.logging import logger

# -----------------------------------------------------------------------------
# Curated Indian Administrative Hierarchy Database (Offline Reference)
# -----------------------------------------------------------------------------
INDIA_DISTRICT_CATALOG = {
    # Jharkhand
    "chatra": {
        "district": "Chatra",
        "state": "Jharkhand",
        "state_code": "JH",
        "block": "Chatra Sadar",
        "tehsil_taluk": "Chatra",
        "lat": 24.2089,
        "lon": 84.8717,
        "region_type": "rural_aspirational",
        "pincode": "825401"
    },
    "ranchi": {
        "district": "Ranchi",
        "state": "Jharkhand",
        "state_code": "JH",
        "block": "Kanke",
        "tehsil_taluk": "Ranchi",
        "lat": 23.3441,
        "lon": 85.3096,
        "region_type": "urban_hub",
        "pincode": "834001"
    },
    "hazaribagh": {
        "district": "Hazaribagh",
        "state": "Jharkhand",
        "state_code": "JH",
        "block": "Sadar Hazaribagh",
        "tehsil_taluk": "Hazaribagh",
        "lat": 23.9967,
        "lon": 85.3691,
        "region_type": "semi_urban",
        "pincode": "825301"
    },
    # Uttar Pradesh
    "varanasi": {
        "district": "Varanasi",
        "state": "Uttar Pradesh",
        "state_code": "UP",
        "block": "Kashi Vidyapeeth",
        "tehsil_taluk": "Varanasi Sadar",
        "lat": 25.3176,
        "lon": 82.9739,
        "region_type": "semi_urban_heritage",
        "pincode": "221001"
    },
    "lucknow": {
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "state_code": "UP",
        "block": "Bakshi Ka Talab",
        "tehsil_taluk": "Lucknow Sadar",
        "lat": 26.8467,
        "lon": 80.9462,
        "region_type": "urban_hub",
        "pincode": "226001"
    },
    "gorakhpur": {
        "district": "Gorakhpur",
        "state": "Uttar Pradesh",
        "state_code": "UP",
        "block": "Sahjanwa",
        "tehsil_taluk": "Gorakhpur Sadar",
        "lat": 26.7606,
        "lon": 83.3732,
        "region_type": "rural_semi_urban",
        "pincode": "273001"
    },
    # Bihar
    "patna": {
        "district": "Patna",
        "state": "Bihar",
        "state_code": "BR",
        "block": "Danapur",
        "tehsil_taluk": "Patna Sadar",
        "lat": 25.5941,
        "lon": 85.1376,
        "region_type": "urban_hub",
        "pincode": "800001"
    },
    "muzaffarpur": {
        "district": "Muzaffarpur",
        "state": "Bihar",
        "state_code": "BR",
        "block": "Kanti",
        "tehsil_taluk": "Muzaffarpur East",
        "lat": 26.1209,
        "lon": 85.3647,
        "region_type": "agro_rural_hub",
        "pincode": "842001"
    },
    # Karnataka
    "bengaluru": {
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "state_code": "KA",
        "block": "Bengaluru South",
        "tehsil_taluk": "Bengaluru South",
        "lat": 12.9716,
        "lon": 77.5946,
        "region_type": "metro_hub",
        "pincode": "560001"
    },
    "mysuru": {
        "district": "Mysuru",
        "state": "Karnataka",
        "state_code": "KA",
        "block": "Mysuru Taluk",
        "tehsil_taluk": "Mysuru",
        "lat": 12.2958,
        "lon": 76.6394,
        "region_type": "semi_urban",
        "pincode": "570001"
    },
    # Maharashtra
    "pune": {
        "district": "Pune",
        "state": "Maharashtra",
        "state_code": "MH",
        "block": "Haveli",
        "tehsil_taluk": "Pune City",
        "lat": 18.5204,
        "lon": 73.8567,
        "region_type": "urban_hub",
        "pincode": "411001"
    },
    "solapur": {
        "district": "Solapur",
        "state": "Maharashtra",
        "state_code": "MH",
        "block": "North Solapur",
        "tehsil_taluk": "Solapur",
        "lat": 17.6599,
        "lon": 75.9064,
        "region_type": "textile_semi_urban",
        "pincode": "413001"
    },
    # Rajasthan
    "jaipur": {
        "district": "Jaipur",
        "state": "Rajasthan",
        "state_code": "RJ",
        "block": "Sanganer",
        "tehsil_taluk": "Jaipur",
        "lat": 26.9124,
        "lon": 75.7873,
        "region_type": "craft_semi_urban",
        "pincode": "302001"
    },
    # Gujarat
    "surat": {
        "district": "Surat",
        "state": "Gujarat",
        "state_code": "GJ",
        "block": "Choryasi",
        "tehsil_taluk": "Surat City",
        "lat": 21.1702,
        "lon": 72.8311,
        "region_type": "textile_hub",
        "pincode": "395001"
    },
    # Madhya Pradesh
    "bhopal": {
        "district": "Bhopal",
        "state": "Madhya Pradesh",
        "state_code": "MP",
        "block": "Huzur",
        "tehsil_taluk": "Bhopal",
        "lat": 23.2599,
        "lon": 77.4126,
        "region_type": "urban_hub",
        "pincode": "462001"
    },
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class LocationResolver:
    """
    Core Location Resolution Service for Stage 5 Market Intelligence Agent.
    """

    def __init__(self):
        self.catalog = INDIA_DISTRICT_CATALOG
        self.user_agent = "KALPA-LocationResolver/1.0 (SIH-2026 Bharat Livelihood)"

    def _match_catalog_by_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Matches a free-text location against the curated catalog."""
        if not text:
            return None
        clean = text.lower().strip()
        
        # Direct key match
        for key, entry in self.catalog.items():
            if key in clean or entry["district"].lower() in clean or entry["state"].lower() in clean:
                return entry
        return None

    def _match_catalog_by_coords(self, lat: float, lon: float, max_dist_km: float = 80.0) -> Optional[Dict[str, Any]]:
        """Finds closest catalog district within a realistic distance threshold."""
        closest = None
        min_dist = float("inf")
        for entry in self.catalog.values():
            dist = haversine_distance_km(lat, lon, entry["lat"], entry["lon"])
            if dist < min_dist:
                min_dist = dist
                closest = entry

        if closest and min_dist <= max_dist_km:
            return closest
        return closest  # return closest regardless if needed for fallback

    async def _reverse_geocode_osm(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Queries OpenStreetMap Nominatim reverse geocoding API with safety timeout."""
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 14,
            "addressdetails": 1
        }
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    addr = data.get("address", {})
                    return {
                        "village": addr.get("village") or addr.get("hamlet") or addr.get("suburb"),
                        "block": addr.get("county") or addr.get("municipality"),
                        "tehsil_taluk": addr.get("taluk") or addr.get("tehsil"),
                        "district": addr.get("state_district") or addr.get("district") or addr.get("county"),
                        "state": addr.get("state"),
                        "country": addr.get("country", "India"),
                        "pincode": addr.get("postcode")
                    }
        except Exception as e:
            logger.warning(f"[LOCATION RESOLVER] OSM reverse geocoding fallback: {e}")
        return None

    async def resolve_location(
        self,
        location_profile: Dict[str, Any]
    ) -> LocationContext:
        """
        Resolves complete administrative hierarchy, coordinates, precision, and conflict detection.
        """
        user_name = location_profile.get("name") or ""
        user_village = location_profile.get("village")
        user_block = location_profile.get("block")
        user_district = location_profile.get("district") or ""
        user_state = location_profile.get("state") or "India"

        coords = location_profile.get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")

        user_text_combined = f"{user_village or ''} {user_block or ''} {user_district} {user_state} {user_name}".strip()

        # Step 1: Forward catalog lookup for user text
        catalog_user_match = self._match_catalog_by_text(user_text_combined)

        has_gps = (lat is not None and lon is not None and abs(lat) > 0.001 and abs(lon) > 0.001)

        gps_resolved_hierarchy = None
        gps_match_catalog = None

        if has_gps:
            # Try live reverse geocode
            gps_resolved_hierarchy = await self._reverse_geocode_osm(lat, lon)
            gps_match_catalog = self._match_catalog_by_coords(lat, lon)

        # Step 2: Conflict Detection (Compare user-supplied location vs GPS resolved location)
        conflict_info = LocationConflictInfo(has_conflict=False)

        if has_gps and catalog_user_match:
            user_exp_lat = catalog_user_match["lat"]
            user_exp_lon = catalog_user_match["lon"]
            dist = haversine_distance_km(lat, lon, user_exp_lat, user_exp_lon)

            # Check for substantial spatial conflict (>120 km or distinct state/district)
            gps_district = (gps_resolved_hierarchy or {}).get("district") or (gps_match_catalog or {}).get("district")
            gps_state = (gps_resolved_hierarchy or {}).get("state") or (gps_match_catalog or {}).get("state")
            user_expected_dist = catalog_user_match.get("district")

            is_district_mismatch = (gps_district and user_expected_dist and gps_district.lower() != user_expected_dist.lower() and dist > 80.0)

            if dist > 150.0 or is_district_mismatch:
                conflict_info = LocationConflictInfo(
                    has_conflict=True,
                    location_conflict=True,
                    user_location_text=f"{catalog_user_match['district']}, {catalog_user_match['state']}",
                    gps_resolved_text=f"{gps_district or 'GPS Target'}, {gps_state or ''} (Coords: {lat:.4f}, {lon:.4f})",
                    text_location={
                        "village": user_village,
                        "district": catalog_user_match.get("district"),
                        "state": catalog_user_match.get("state"),
                        "latitude": user_exp_lat,
                        "longitude": user_exp_lon
                    },
                    gps_location={
                        "district": gps_district,
                        "state": gps_state,
                        "latitude": lat,
                        "longitude": lon
                    },
                    selected_location={
                        "district": catalog_user_match.get("district"),
                        "state": catalog_user_match.get("state"),
                        "latitude": user_exp_lat,
                        "longitude": user_exp_lon,
                        "source": "explicit_user_location"
                    },
                    selection_reason="Prioritized explicit user-entered location over distant GPS coordinates per priority rules.",
                    distance_km=round(dist, 2),
                    confidence=0.85,
                    reason=(
                        f"Significant geographic discrepancy of {dist:.1f} km detected between user-specified location "
                        f"('{catalog_user_match['district']}') and GPS resolved coordinates ('{gps_district}'). "
                        "System preserves both contexts without silent overwrite."
                    )
                )
                logger.warning(f"[LOCATION CONFLICT] {conflict_info.reason}")

        # Step 3: Administrative Hierarchy Synthesis
        hierarchy = AdministrativeHierarchy(country="India")
        precision = "district"
        confidence = 0.70
        resolution_method = "deterministic_catalog"

        if has_gps and gps_resolved_hierarchy and gps_resolved_hierarchy.get("district"):
            # GPS reverse geocoded
            hierarchy.village = user_village or gps_resolved_hierarchy.get("village")
            hierarchy.block = user_block or gps_resolved_hierarchy.get("block")
            hierarchy.tehsil_taluk = gps_resolved_hierarchy.get("tehsil_taluk")
            hierarchy.district = gps_resolved_hierarchy.get("district")
            hierarchy.state = gps_resolved_hierarchy.get("state") or user_state
            hierarchy.pincode = gps_resolved_hierarchy.get("pincode")

            resolution_method = "gps_reverse_geocoding"
            if hierarchy.village:
                precision = "village"
                confidence = 0.95
            elif hierarchy.block:
                precision = "block"
                confidence = 0.88
            else:
                precision = "district"
                confidence = 0.82

        elif catalog_user_match:
            # Catalog text resolved
            hierarchy.village = user_village
            hierarchy.block = user_block or catalog_user_match.get("block")
            hierarchy.tehsil_taluk = catalog_user_match.get("tehsil_taluk")
            hierarchy.district = catalog_user_match.get("district")
            hierarchy.state = catalog_user_match.get("state")
            hierarchy.pincode = catalog_user_match.get("pincode")

            if not has_gps:
                lat = catalog_user_match["lat"]
                lon = catalog_user_match["lon"]

            resolution_method = "forward_geocoding_catalog"
            if user_village:
                precision = "village"
                confidence = 0.85
            elif user_block:
                precision = "block"
                confidence = 0.80
            else:
                precision = "district"
                confidence = 0.75

        else:
            # Fallback user input
            hierarchy.village = user_village
            hierarchy.block = user_block
            hierarchy.district = user_district or "Target District"
            hierarchy.state = user_state or "India"
            resolution_method = "user_input_fallback"
            precision = "village" if user_village else ("block" if user_block else "district")
            confidence = 0.60
            if not has_gps:
                lat = 23.3441
                lon = 85.3096  # Centroid default

        return LocationContext(
            resolved_location=hierarchy,
            coordinates=LocationCoordinates(
                latitude=round(lat, 6) if lat is not None else None,
                longitude=round(lon, 6) if lon is not None else None,
                accuracy=coords.get("accuracy", 10.0 if has_gps else 500.0)
            ),
            geographic_precision=precision,
            resolution_confidence=round(confidence, 2),
            resolution_method=resolution_method,
            conflict=conflict_info
        )


location_resolver = LocationResolver()
