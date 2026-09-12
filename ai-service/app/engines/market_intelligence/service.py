"""
Market Intelligence Engine Interface.
Bridges legacy engine calls to the deterministic Stage 6 Market Intelligence Engine.
"""
from app.services.market_intelligence_engine import (
    MarketIntelligenceEngine,
    market_intelligence_engine
)

__all__ = ["MarketIntelligenceEngine", "market_intelligence_engine"]
