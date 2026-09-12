"""
Caching Layer for Stage 5 Market Intelligence Agent.
Provides in-memory caching with deterministic multi-key hashing, TTL expiration,
strict cache isolation per business/location/requirements, context mismatch invalidation,
and force-refresh bypass.
"""
import time
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.schemas.market import MarketExecutionContext
from app.core.logging import logger


class MarketEvidenceCache:
    """
    Deterministic in-memory cache for Stage 5 Market Intelligence tool executions.
    Guarantees strict cache isolation between different businesses, locations, and requirement sets.
    """

    def __init__(self, default_ttl_seconds: int = 3600, static_ttl_seconds: int = 86400):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds
        self.static_ttl = static_ttl_seconds

    def build_cache_key(self, tool_name: str, context: MarketExecutionContext) -> str:
        """
        Builds a deterministic cryptographic cache key fingerprint.
        Includes:
        - tool_name
        - canonical business_id
        - business_name
        - normalized user business input (normalized_concept / specific_business)
        - location (district, state, village, geographic_precision, lat, lon)
        - business profile version
        - normalized requirements
        """
        bus = context.business
        loc = context.location
        resolved = loc.resolved_location
        coords = loc.coordinates

        lat = coords.latitude
        lon = coords.longitude
        district = (resolved.district or "").lower().strip()
        state = (resolved.state or "").lower().strip()
        village = (resolved.village or "").lower().strip()
        precision = (loc.geographic_precision or "district").lower().strip()

        loc_str = f"{district}:{state}:{village}:{precision}"
        loc_hash = hashlib.md5(loc_str.encode("utf-8")).hexdigest()[:12]

        # Normalized user business concept
        norm_concept = (
            bus.normalized_concept or
            bus.specific_business or
            bus.business_name or
            bus.business_id
        ).lower().strip()

        fingerprint = {
            "tool_name": tool_name.strip(),
            "business_id": bus.business_id.lower().strip(),
            "business_name": (bus.business_name or "").lower().strip(),
            "normalized_concept": norm_concept,
            "specific_business": (bus.specific_business or "").lower().strip(),
            "business_profile_version": bus.profile_version or "1.0",
            "latitude": round(lat, 4) if lat is not None else None,
            "longitude": round(lon, 4) if lon is not None else None,
            "location_hash": loc_hash,
            "geographic_precision": precision,
            "district": district,
            "state": state,
            "normalized_requirements": sorted(context.requirements),
            "source_version": "STAGE-5-V2"
        }

        serialized = json.dumps(fingerprint, sort_keys=True)
        key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return key

    def get(
        self,
        tool_name: str,
        context: MarketExecutionContext
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached result if valid, not expired, and context-consistent.
        Performs semantic validation against current business context before returning.
        Respects force_refresh bypass.
        """
        if context.force_refresh:
            logger.info(f"[CACHE BYPASS] force_refresh=True for tool='{tool_name}', business_id='{context.business.business_id}', analysis_id='{context.analysis_id}'")
            return None

        key = self.build_cache_key(tool_name, context)
        entry = self._cache.get(key)
        if not entry:
            logger.info(f"[CACHE MISS] tool='{tool_name}', business_id='{context.business.business_id}', analysis_id='{context.analysis_id}' (key={key[:10]}...)")
            return None

        # Check TTL
        if time.time() > entry["expires_at"]:
            logger.info(f"[CACHE INVALIDATED] TTL expired for tool='{tool_name}', business_id='{context.business.business_id}', analysis_id='{context.analysis_id}'")
            self._cache.pop(key, None)
            return None

        # Context Integrity Gate Validation (Task 7):
        cached_bid = (entry.get("business_id") or "").lower().strip()
        current_bid = context.business.business_id.lower().strip()
        if cached_bid != current_bid:
            logger.warning(
                f"[CACHE INVALIDATED] BUSINESS_CONTEXT_MISMATCH: cached business_id='{cached_bid}' "
                f"!= current='{current_bid}' for tool='{tool_name}' (key={key[:10]}...). Evicting entry."
            )
            self._cache.pop(key, None)
            return None

        cached_bname = (entry.get("business_name") or "").lower().strip()
        current_bname = (context.business.business_name or context.business.specific_business or current_bid).lower().strip()
        if cached_bname and current_bname and cached_bname != current_bname and current_bid in ["uncurated", "general"]:
            logger.warning(
                f"[CACHE INVALIDATED] BUSINESS_CONTEXT_MISMATCH: cached business_name='{cached_bname}' "
                f"!= current='{current_bname}' for tool='{tool_name}'. Evicting entry."
            )
            self._cache.pop(key, None)
            return None

        logger.info(f"[CACHE HIT] tool='{tool_name}', business_id='{context.business.business_id}', analysis_id='{context.analysis_id}' (key={key[:10]}...)")
        return entry["data"]

    def set(
        self,
        tool_name: str,
        context: MarketExecutionContext,
        data: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ):
        """
        Caches tool result with full business context tags. Never caches failed results.
        """
        status = data.get("status", "success")
        if status == "failed":
            logger.debug(f"[CACHE SKIP] Not caching failed result for tool='{tool_name}'")
            return

        key = self.build_cache_key(tool_name, context)

        # Longer TTL for static knowledge hub tools
        if tool_name in ["knowledge_hub_tool", "dataset_retrieval_tool"]:
            ttl = self.static_ttl
        else:
            ttl = ttl_seconds or self.default_ttl

        self._cache[key] = {
            "data": data,
            "business_id": context.business.business_id.lower().strip(),
            "business_name": (context.business.business_name or "").lower().strip(),
            "normalized_concept": (context.business.normalized_concept or "").lower().strip(),
            "analysis_id": context.analysis_id,
            "session_id": context.session_id,
            "cached_at": datetime.utcnow().isoformat() + "Z",
            "expires_at": time.time() + ttl
        }
        logger.debug(f"[CACHE STORED] tool='{tool_name}', business_id='{context.business.business_id}', analysis_id='{context.analysis_id}'")

    def invalidate_contaminated_saree_cache(self, current_business_id: str):
        """
        Invalidates old cache entries containing business_id = saree_retail
        ONLY when the current request is not actually saree retail (Task 8).
        """
        current_clean = current_business_id.lower().strip()
        if "saree" not in current_clean:
            keys_to_purge = [
                k for k, v in list(self._cache.items())
                if v.get("business_id") in ["saree_retail", "saree"] or "saree" in str(v.get("business_id", "")).lower()
            ]
            for k in keys_to_purge:
                self._cache.pop(k, None)
            if keys_to_purge:
                logger.info(f"[CACHE PURGED] Purged {len(keys_to_purge)} stale saree entries for non-saree business '{current_business_id}'")

    def invalidate_business(self, business_id: str):
        """Invalidates all cache entries for a specific business."""
        b_clean = business_id.lower().strip()
        keys_to_delete = [k for k, v in list(self._cache.items()) if v.get("business_id") == b_clean]
        for k in keys_to_delete:
            self._cache.pop(k, None)
        logger.info(f"[CACHE INVALIDATED] Purged {len(keys_to_delete)} entries for business_id='{business_id}'")

    def clear(self):
        self._cache.clear()
        logger.info("[CACHE CLEARED] All market cache entries purged.")


# Global singleton instance
market_cache = MarketEvidenceCache()
