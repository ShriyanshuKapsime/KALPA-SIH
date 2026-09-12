"""
Base Tool Interface for KALPA Stage 5 Market Intelligence Agent.
Provides abstract contract, execution context, and standardized result container.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.market import (
    MarketExecutionContext,
    CanonicalBusinessContext,
    LocationContext,
    EvidenceDataStatus,
)


import uuid


class ToolExecutionContext(BaseModel):
    """
    Standard Tool Execution Context.
    Can be instantiated directly or converted from MarketExecutionContext.
    """
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_profile: Dict[str, Any] = Field(default_factory=dict)
    location_context: Dict[str, Any] = Field(default_factory=dict)
    knowledge_pack: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    canonical_business: Optional[CanonicalBusinessContext] = None
    canonical_location: Optional[LocationContext] = None
    force_refresh: bool = False

    def to_market_execution_context(self) -> MarketExecutionContext:
        """Converts to immutable MarketExecutionContext."""
        from app.agents.market_intelligence.context_normalizer import context_normalizer
        bus = self.canonical_business or context_normalizer.normalize(
            self.business_profile,
            analysis_id=self.analysis_id,
            session_id=self.session_id
        )
        loc = self.canonical_location or LocationContext(**(self.location_context or {}))
        return MarketExecutionContext(
            analysis_id=self.analysis_id,
            session_id=self.session_id,
            business=bus,
            location=loc,
            requirements=[],
            knowledge_context=self.knowledge_pack,
            execution_mode="live",
            force_refresh=self.force_refresh
        )


class ToolResult(BaseModel):
    tool_name: str
    status: str = "success"  # "success" | "partial" | "failed" | "unavailable"
    data_status: str = "OFFICIAL_STATIC_DATA"  # EvidenceDataStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    geographic_precision: str = "district"
    target_geographic_precision: str = "village"
    data_geographic_precision: str = "district"
    confidence: float = 0.85
    source: Dict[str, Any] = Field(default_factory=dict)
    reference_period: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    retrieval_method: str = "CURATED_DATASET"
    is_proxy: bool = False
    proxy_reason: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class BaseMarketTool(ABC):
    """
    Abstract Base Class for all Stage 5 Market Intelligence Tools.
    """

    def __init__(
        self,
        name: str,
        description: str,
        supported_requirements: List[str]
    ):
        self.name = name
        self.description = description
        self.supported_requirements = supported_requirements

    @abstractmethod
    async def execute(self, context: Union[ToolExecutionContext, MarketExecutionContext]) -> ToolResult:
        """Executes tool logic and returns standardized ToolResult."""
        pass

    def validate_input(self, context: Union[ToolExecutionContext, MarketExecutionContext]) -> bool:
        """Validates that mandatory fields in context exist before execution."""
        if isinstance(context, MarketExecutionContext):
            return bool(context.business and context.location)
        if not context.business_profile or not context.location_context:
            return False
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Returns tool health status and metadata."""
        return {
            "name": self.name,
            "tool": self.__class__.__name__,
            "status": "available",
            "supported_requirements": self.supported_requirements
        }
