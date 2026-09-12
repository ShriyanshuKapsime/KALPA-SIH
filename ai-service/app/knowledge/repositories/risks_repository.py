import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import RiskItemSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class RisksRepository:
    """
    Repository for the enterprise risk library catalog.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(CURATED_DATA_DIR, "risks", "risk_library.json")
        self._risks: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._risks = json.load(f)
                logger.info(f"Loaded {len(self._risks)} curated risk catalog items")
            else:
                logger.warning(f"Risk library file not found: {self.file_path}")
                self._risks = []
        except Exception as e:
            logger.error(f"Failed to load risk library: {e}")
            self._risks = []

    def get_all(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[RiskItemSchema]:
        filtered = self._risks
        if category:
            filtered = [r for r in filtered if r.get("category", "").upper() == category.upper()]
        if severity:
            filtered = [r for r in filtered if r.get("severity", "").upper() == severity.upper()]
        return [RiskItemSchema(**r) for r in filtered]

    def get_by_id(self, risk_id: str) -> Optional[RiskItemSchema]:
        for r in self._risks:
            if r.get("risk_id") == risk_id:
                return RiskItemSchema(**r)
        return None

    def get_for_business(self, business_node_id: str) -> List[RiskItemSchema]:
        matched = []
        for r in self._risks:
            nodes = r.get("applicable_business_nodes", [])
            if "ALL_RURAL_MICRO_ENTERPRISES" in nodes or business_node_id in nodes:
                matched.append(RiskItemSchema(**r))
        return matched
