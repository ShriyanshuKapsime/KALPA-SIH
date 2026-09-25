"""
Confidence & Provenance Models for Financial Intelligence Foundation.
Every financial assumption carries source_type, confidence, status, and provenance.
No value is silently zero. Unknown values are explicitly represented.
"""
from enum import Enum
from typing import Any, Optional, Dict
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Origin of a financial assumption value."""
    USER_INPUT = "USER_INPUT"
    BENCHMARK = "BENCHMARK"
    MARKET_ENGINE = "MARKET_ENGINE"
    CALCULATED = "CALCULATED"
    DERIVED = "DERIVED"
    SCHEME_CONFIG = "SCHEME_CONFIG"
    KNOWLEDGE_REPO = "KNOWLEDGE_REPO"
    MODEL_ASSUMPTION = "MODEL_ASSUMPTION"
    UNKNOWN = "UNKNOWN"


class AssumptionStatus(str, Enum):
    """Resolution status of a financial assumption."""
    RESOLVED = "RESOLVED"
    BENCHMARKED = "BENCHMARKED"
    CALCULATED = "CALCULATED"
    USER_REQUIRED = "USER_REQUIRED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AssumptionType(str, Enum):
    """Classification of the assumption's epistemic basis."""
    FACT = "FACT"
    USER_INPUT = "USER_INPUT"
    VERIFIED_EVIDENCE = "VERIFIED_EVIDENCE"
    BENCHMARK = "BENCHMARK"
    DERIVED = "DERIVED"
    MODEL_ASSUMPTION = "MODEL_ASSUMPTION"


class Provenance(BaseModel):
    """Audit trail for a single data point."""
    source_type: SourceType = SourceType.UNKNOWN
    source_id: Optional[str] = None
    source_stage: Optional[str] = None
    description: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: Optional[str] = None


class ResolvedAssumption(BaseModel):
    """
    A financial driver value with full provenance and confidence metadata.
    NEVER silently replace unknown with zero.
    """
    driver_id: str
    value: Optional[Any] = None
    unit: Optional[str] = None
    source_type: SourceType = SourceType.UNKNOWN
    source_id: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: AssumptionStatus = AssumptionStatus.UNKNOWN
    assumption_type: AssumptionType = AssumptionType.MODEL_ASSUMPTION
    user_confirmed: bool = False
    required: bool = False
    criticality: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    provenance: Optional[Provenance] = None
    notes: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return self.status in (
            AssumptionStatus.RESOLVED,
            AssumptionStatus.BENCHMARKED,
            AssumptionStatus.CALCULATED,
        ) and self.value is not None

    @property
    def needs_user_input(self) -> bool:
        return self.status == AssumptionStatus.USER_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class FoundationStatus(str, Enum):
    """Overall status of the Financial Intelligence Foundation analysis."""
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    USER_INPUT_REQUIRED = "USER_INPUT_REQUIRED"
    FAILED = "FAILED"


class FoundationConfidenceSummary(BaseModel):
    """Structured confidence and resolution tracking summary."""
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    resolved: int = 0
    total: int = 0
    user_required: int = 0
    unknown: int = 0
