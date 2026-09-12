import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import DynamicDataRequirementSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class DynamicRequirementsRepository:
    """
    Repository defining dynamic external data specifications required by future KALPA engines.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(CURATED_DATA_DIR, "dynamic", "dynamic_data_requirements.json")
        self._requirements: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._requirements = json.load(f)
                logger.info(f"Loaded {len(self._requirements)} dynamic data requirements")
            else:
                logger.warning(f"Dynamic data requirements file not found: {self.file_path}")
                self._requirements = []
        except Exception as e:
            logger.error(f"Failed to load dynamic data requirements: {e}")
            self._requirements = []

    def get_all(
        self,
        domain: Optional[str] = None,
        consuming_engine: Optional[str] = None,
    ) -> List[DynamicDataRequirementSchema]:
        filtered = self._requirements
        if domain:
            filtered = [r for r in filtered if r.get("domain", "").upper() == domain.upper()]
        if consuming_engine:
            filtered = [r for r in filtered if consuming_engine.upper() in [e.upper() for e in r.get("consuming_engines", [])]]
        return [DynamicDataRequirementSchema(**r) for r in filtered]

    def get_by_id(self, requirement_id: str) -> Optional[DynamicDataRequirementSchema]:
        for r in self._requirements:
            if r.get("requirement_id") == requirement_id:
                return DynamicDataRequirementSchema(**r)
        return None
