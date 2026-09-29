"""
Alias package for Stage 14.3 supporting 'from backend.dpr.stage14_3 import ...'
"""
import sys
import os

# Add ai-service to sys.path if not present
ai_service_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../ai-service"))
if ai_service_dir not in sys.path:
    sys.path.insert(0, ai_service_dir)

from app.dpr.stage14_3 import *
from app.dpr.stage14_3 import (
    Stage14_3Orchestrator,
    stage14_3_orchestrator,
    DPRStatus,
    DPR_STATE_ISOLATION_ERROR,
    DPRDocumentControl,
    ProjectAtAGlanceData,
    SectionNarrative,
    NarrativePlan,
    NarrativeValidationResult,
    DPRGenerationRequest,
    DPRGenerationResponse,
    FinancialIntegritySummary,
    SarvamDPRNarrativeService,
    DPRNarrativePlanner,
    DPRNarrativeGenerator,
    narrative_cache,
    DPRNarrativeValidator,
    DPRDocumentAssembler,
    DPRPDFRenderer,
    dpr_pdf_renderer,
    REPORTS_DIR,
    DPRValidator,
    DPRStatusEngine,
    ProvenanceRegistry,
    DPRChartBuilder,
    DPRProcessFlowBuilder,
    DPRAnnexureBuilder,
    DPRTableBuilder,
)
