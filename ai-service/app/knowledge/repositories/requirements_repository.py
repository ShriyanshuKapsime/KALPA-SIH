import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import BusinessRequirementSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class RequirementsRepository:
    """
    Repository for business technical requirements: equipment, space, power, manpower, and compliance.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(CURATED_DATA_DIR, "business", "business_requirements.json")
        self._requirements: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._requirements = json.load(f)
                logger.info(f"Loaded {len(self._requirements)} business domain requirements")
            else:
                logger.warning(f"Business requirements file not found: {self.file_path}")
                self._requirements = []
        except Exception as e:
            logger.error(f"Failed to load business requirements: {e}")
            self._requirements = []

    def get_by_business(self, business_node_id: str) -> Optional[BusinessRequirementSchema]:
        for req in self._requirements:
            if req.get("business_node_id") == business_node_id:
                return BusinessRequirementSchema(**req)
        return None

    def get_all(self) -> List[BusinessRequirementSchema]:
        return [BusinessRequirementSchema(**req) for req in self._requirements]
