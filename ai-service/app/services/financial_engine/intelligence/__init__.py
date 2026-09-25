"""
Financial Intelligence Foundation (Milestone 1).
Modular internal architecture for financial archetype mapping,
driver registry, assumption resolution, confidence tracking,
provenance, and question generation.

Architecture principle:
- LLMs understand/retrieve/explain.
- Engines calculate.
- Financial calculations remain deterministic.
- Stage 2/3 owns business classification — Finance consumes it.
"""
from app.services.financial_engine.intelligence.confidence import (
    SourceType,
    AssumptionStatus,
    AssumptionType,
    ResolvedAssumption,
    Provenance,
    FoundationStatus,
    FoundationConfidenceSummary,
)
from app.services.financial_engine.intelligence.archetype_registry import (
    FinancialArchetype,
    archetype_registry,
    ArchetypeRegistry,
)
from app.services.financial_engine.intelligence.driver_registry import (
    DriverDefinition,
    driver_registry,
    DriverRegistry,
)
from app.services.financial_engine.intelligence.assumption_registry import (
    assumption_resolver,
    AssumptionResolver,
)
from app.services.financial_engine.intelligence.question_engine import (
    question_engine,
    QuestionEngine,
    RequiredUserInput,
)
from app.services.financial_engine.intelligence.evidence_resolver import (
    evidence_resolver,
    EvidenceResolver,
)
from app.services.financial_engine.intelligence.provenance import (
    provenance_tracker,
    ProvenanceTracker,
)

__all__ = [
    "SourceType",
    "AssumptionStatus",
    "AssumptionType",
    "ResolvedAssumption",
    "Provenance",
    "FoundationStatus",
    "FoundationConfidenceSummary",
    "FinancialArchetype",
    "archetype_registry",
    "ArchetypeRegistry",
    "DriverDefinition",
    "driver_registry",
    "DriverRegistry",
    "assumption_resolver",
    "AssumptionResolver",
    "question_engine",
    "QuestionEngine",
    "RequiredUserInput",
    "evidence_resolver",
    "EvidenceResolver",
    "provenance_tracker",
    "ProvenanceTracker",
]
