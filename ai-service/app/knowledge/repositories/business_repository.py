import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import BusinessProfileSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class BusinessRepository:
    """
    Repository for Layer 2: Business Domain Knowledge & Profiles across the 15 Priority Rural Enterprises.
    """

    def __init__(self, profiles_file: Optional[str] = None):
        self.profiles_file = profiles_file or os.path.join(CURATED_DATA_DIR, "business", "business_profiles.json")
        self._profiles: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, "r", encoding="utf-8") as f:
                    self._profiles = json.load(f)
                logger.info(f"Loaded {len(self._profiles)} business domain profiles")
            else:
                logger.warning(f"Business profiles file not found: {self.profiles_file}")
                self._profiles = []
        except Exception as e:
            logger.error(f"Failed to load business profiles: {e}")
            self._profiles = []

    def _matches_identifier(self, profile: Dict[str, Any], query_id: str) -> bool:
        q = query_id.strip().lower()
        node_id = str(profile.get("business_node_id") or profile.get("business_id") or "").strip().lower()
        if node_id:
            if node_id == q or node_id.replace("_", "") == q.replace("_", ""):
                return True
            if node_id.replace("ont_", "") == q.replace("ont_", ""):
                return True
            if node_id.replace("ont_", "").replace("_", "") == q.replace("ont_", "").replace("_", ""):
                return True

        aliases = [str(a).strip().lower() for a in profile.get("aliases", [])]
        for a in aliases:
            if a == q or a.replace(" ", "_") == q or a.replace("_", " ") == q:
                return True
            if a.replace("ont_", "").replace(" ", "_") == q.replace("ont_", "").replace(" ", "_"):
                return True
        return False

    def get_profile(self, business_id: str) -> Optional[BusinessProfileSchema]:
        for p in self._profiles:
            if self._matches_identifier(p, business_id):
                return BusinessProfileSchema(**p)
        return None

    def get_profile_by_nic(self, nic_code: str) -> Optional[BusinessProfileSchema]:
        q_nic = str(nic_code).strip()
        for p in self._profiles:
            nic = str(p.get("nic_code", "")).strip()
            if not nic and p.get("classification") and p["classification"].get("nic_codes"):
                nic = str(p["classification"]["nic_codes"][0]).strip()
            if nic and (nic == q_nic or nic.startswith(q_nic[:4]) or q_nic.startswith(nic[:4])):
                return BusinessProfileSchema(**p)
        return None

    def get_all_profiles(self) -> List[BusinessProfileSchema]:
        return [BusinessProfileSchema(**p) for p in self._profiles]

    def get_profiles_by_category(self, category: str) -> List[BusinessProfileSchema]:
        cat_lower = category.strip().lower()
        return [
            BusinessProfileSchema(**p)
            for p in self._profiles
            if p.get("category", "").strip().lower() == cat_lower
            or (p.get("classification") and p["classification"].get("category", "").strip().lower() == cat_lower)
        ]
