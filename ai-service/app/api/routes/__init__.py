from app.api.routes.health import router as health_router
from app.api.routes.intake import router as intake_router
from app.api.routes.classification import router as classification_router
from app.api.routes.profile import router as profile_router
from app.api.routes.orchestrator import router as orchestrator_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.market_intelligence import router as market_intelligence_router
from app.api.routes.opportunity_evaluation import router as opportunity_evaluation_router
from app.api.routes.financial_analysis import router as financial_analysis_router
from app.api.routes.entrepreneur_profile import router as entrepreneur_profile_router
from app.api.routes.risk_analysis import router as risk_analysis_router
from app.api.routes.feasibility import router as feasibility_router
from app.api.routes.swot import router as swot_router
from app.api.routes.assistant import router as assistant_router
from app.api.routes.dpr import router as dpr_router
from app.api.routes.translation import router as translation_router

__all__ = [
    "health_router",
    "intake_router",
    "classification_router",
    "profile_router",
    "orchestrator_router",
    "knowledge_router",
    "market_intelligence_router",
    "opportunity_evaluation_router",
    "financial_analysis_router",
    "entrepreneur_profile_router",
    "risk_analysis_router",
    "feasibility_router",
    "swot_router",
    "assistant_router",
    "dpr_router",
    "translation_router",
]



