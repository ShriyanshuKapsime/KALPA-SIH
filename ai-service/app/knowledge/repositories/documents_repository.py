import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import InstitutionalDocumentSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class DocumentsRepository:
    """
    Repository for official institutional documents from NABARD, RBI, MSME, SIDBI, FSSAI.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(CURATED_DATA_DIR, "documents", "institutional_documents.json")
        self._documents: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._documents = json.load(f)
                logger.info(f"Loaded {len(self._documents)} institutional documents from {self.file_path}")
            else:
                logger.warning(f"Institutional documents file not found: {self.file_path}")
                self._documents = []
        except Exception as e:
            logger.error(f"Failed to load institutional documents: {e}")
            self._documents = []

    def get_all(
        self,
        institution: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[InstitutionalDocumentSchema]:
        filtered = self._documents
        if institution:
            filtered = [d for d in filtered if institution.upper() in d.get("institution", "").upper()]
        if category:
            filtered = [d for d in filtered if d.get("category", "").upper() == category.upper()]
        if status:
            filtered = [d for d in filtered if d.get("ingestion_status", "").upper() == status.upper()]
        return [InstitutionalDocumentSchema(**d) for d in filtered]

    def get_by_id(self, document_id: str) -> Optional[InstitutionalDocumentSchema]:
        for d in self._documents:
            if d.get("document_id") == document_id:
                return InstitutionalDocumentSchema(**d)
        return None

    def get_for_business(self, business_node_id: str) -> List[InstitutionalDocumentSchema]:
        matched = []
        for d in self._documents:
            nodes = d.get("applicable_business_nodes", [])
            if "ALL_RURAL_MICRO_ENTERPRISES" in nodes or business_node_id in nodes:
                matched.append(InstitutionalDocumentSchema(**d))
        return matched
