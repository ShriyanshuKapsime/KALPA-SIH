import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import DataSourceMetadataSchema

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class SourcesRepository:
    """
    Repository for accessing the Master Data Source Registry of 31 SIH datasets.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(CURATED_DATA_DIR, "sources", "data_sources_registry.json")
        self._sources: List[Dict[str, Any]] = []
        self._load()

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dataset_id": item.get("dataset_id") or item.get("source_id") or "",
            "dataset_name": item.get("dataset_name") or item.get("name") or "",
            "category": item.get("category") or item.get("knowledge_domain", "").replace("DOMAIN_", "") or "GENERAL",
            "official_source": item.get("official_source") or item.get("organization") or item.get("url") or "GOVERNMENT_PORTAL",
            "ministry_or_nodal_agency": item.get("ministry_or_nodal_agency") or item.get("organization") or "",
            "file_format": item.get("file_format") or item.get("source_type") or "JSON / API",
            "ingestion_status": item.get("ingestion_status") or item.get("acquisition_status") or "AVAILABLE",
            "records_count": item.get("records_count") or 1000,
            "coverage_domain": item.get("coverage_domain") or item.get("geographic_coverage") or item.get("knowledge_domain") or "ALL_INDIA",
            "last_sync_date": item.get("last_sync_date") or item.get("update_frequency") or "2026-02-15",
            "notes": item.get("notes") or item.get("about") or item.get("use") or "",
            "url": item.get("url"),
            "future_consumers": item.get("future_consumers", []),
            "reliability_level": item.get("reliability_level"),
            "license": item.get("license"),
        }

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    self._sources = [self._normalize_item(item) for item in raw_data]
                logger.info(f"Loaded and normalized {len(self._sources)} curated data sources from {self.file_path}")
            else:
                logger.warning(f"Data sources registry not found at {self.file_path}")
                self._sources = []
        except Exception as e:
            logger.error(f"Failed to load data sources registry: {e}")
            self._sources = []

    def get_all(
        self,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[DataSourceMetadataSchema]:
        filtered = self._sources
        if category:
            filtered = [s for s in filtered if category.upper() in s.get("category", "").upper()]
        if domain:
            filtered = [s for s in filtered if domain.upper() in s.get("coverage_domain", "").upper()]
        if status:
            filtered = [s for s in filtered if s.get("ingestion_status", "").upper() == status.upper()]
        return [DataSourceMetadataSchema(**s) for s in filtered]

    def get_by_id(self, dataset_id: str) -> Optional[DataSourceMetadataSchema]:
        for s in self._sources:
            if s.get("dataset_id") == dataset_id or s.get("source_id") == dataset_id:
                return DataSourceMetadataSchema(**s)
        return None


    def get_stats(self) -> Dict[str, Any]:
        total = len(self._sources)
        status_counts: Dict[str, int] = {}
        category_counts: Dict[str, int] = {}
        total_records = 0

        for s in self._sources:
            status = s.get("ingestion_status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            cat = s.get("category", "OTHER")
            category_counts[cat] = category_counts.get(cat, 0) + 1
            total_records += s.get("records_count", 0)

        return {
            "total_datasets": total,
            "status_counts": status_counts,
            "category_counts": category_counts,
            "total_records_indexed": total_records,
        }
