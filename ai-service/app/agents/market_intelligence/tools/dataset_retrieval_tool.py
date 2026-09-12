"""
Dataset Retrieval Tool (Tool 8).
Connects to the Stage 4.5 31-Dataset Master Registry, finds relevant domain layers,
checks acquisition status, and marks dynamic API access requirements.
"""
import time
from typing import Dict, Any, List, Union
from app.agents.market_intelligence.tools.base_tool import BaseMarketTool, ToolExecutionContext, ToolResult
from app.knowledge.services.knowledge_service import KnowledgeService
from app.schemas.market import MarketExecutionContext


class DatasetRetrievalTool(BaseMarketTool):
    def __init__(self, knowledge_service: KnowledgeService = None):
        super().__init__(
            name="dataset_retrieval_tool",
            description="Queries the Stage 4.5 Master Data Source Registry to retrieve local curated datasets or flag dynamic API requirements.",
            supported_requirements=[
                "required_datasets",
                "dataset_retrieval",
                "data_source_registry",
                "dynamic_data_fetch"
            ]
        )
        self.knowledge_service = knowledge_service or KnowledgeService()

    async def execute(self, context: Union[ToolExecutionContext, MarketExecutionContext]) -> ToolResult:
        start_t = time.perf_counter()

        # Fetch all available data sources from Stage 4.5
        all_sources = self.knowledge_service.get_data_sources()

        matched_datasets = []
        for s in all_sources:
            d_name = s.dataset_name or ""
            d_notes = s.notes or ""
            cat_match = s.category in ["ENTERPRISE_REGISTRY", "DEMOGRAPHICS", "MARKET_BENCHMARK", "INFRASTRUCTURE"]

            if cat_match or len(matched_datasets) < 4:
                status_mapped = "available" if s.ingestion_status == "AVAILABLE" else ("partial" if s.ingestion_status == "PARTIAL" else "dynamic_fetch_required")
                matched_datasets.append({
                    "dataset_id": s.dataset_id,
                    "dataset_name": s.dataset_name,
                    "status": status_mapped,
                    "data_status": "OFFICIAL_STATIC_DATA" if s.ingestion_status == "AVAILABLE" else "UNAVAILABLE",
                    "source": {
                        "organization": s.official_source or s.ministry_or_nodal_agency,
                        "source_type": "OFFICIAL_DATASET",
                        "url": s.url,
                        "category": s.category,
                        "retrieval_method": "STAGE_4.5_REGISTRY"
                    },
                    "coverage": {
                        "geographic_coverage": s.coverage_domain,
                        "file_format": s.file_format
                    },
                    "data": {
                        "notes": s.notes,
                        "ministry": s.ministry_or_nodal_agency,
                        "records_count": s.records_count
                    }
                })

        elapsed = (time.perf_counter() - start_t) * 1000.0

        return ToolResult(
            tool_name=self.name,
            status="success",
            data_status="OFFICIAL_STATIC_DATA",
            geographic_precision="national",
            target_geographic_precision="village",
            data_geographic_precision="national",
            confidence=0.95,
            source={
                "source_id": "SRC-REGISTRY",
                "organization": "KALPA Stage 4.5 Data Governance & Catalog",
                "source_type": "OFFICIAL_REGISTRY",
                "dataset_name": "Stage 4.5 Master Data Source Registry",
                "retrieval_method": "STAGE_4.5_REGISTRY"
            },
            data={
                "datasets": matched_datasets[:6],
                "total_matched_datasets": len(matched_datasets)
            },
            execution_time_ms=round(elapsed, 2)
        )
