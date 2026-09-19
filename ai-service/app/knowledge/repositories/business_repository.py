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
        if not query_id:
            return False
        q = query_id.strip().lower().replace("-", "_")
        q_clean = q.replace(" ", "_").replace("ont_", "")
        
        node_id = str(profile.get("business_node_id") or profile.get("business_id") or "").strip().lower()
        node_clean = node_id.replace("-", "_").replace("ont_", "")

        if node_clean:
            if node_clean == q_clean or node_clean.replace("_", "") == q_clean.replace("_", ""):
                return True
            if node_clean in q_clean or q_clean in node_clean:
                return True

        b_name = str(profile.get("business_name") or "").strip().lower()
        if b_name and (q in b_name or b_name in q):
            return True

        aliases = [str(a).strip().lower() for a in profile.get("aliases", [])]
        for a in aliases:
            a_clean = a.replace("-", "_").replace(" ", "_").replace("ont_", "")
            if a_clean == q_clean or a_clean in q_clean or q_clean in a_clean:
                return True
            if a == q or q in a or a in q:
                return True

        # Check classification sector / category
        cls_dict = profile.get("classification") or {}
        cat = str(cls_dict.get("category") or "").strip().lower()
        sub_cat = str(cls_dict.get("sub_category") or "").strip().lower()
        if cat and (q_clean in cat.replace(" ", "_") or cat.replace(" ", "_") in q_clean):
            return True
        if sub_cat and (q_clean in sub_cat.replace(" ", "_") or sub_cat.replace(" ", "_") in q_clean):
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
