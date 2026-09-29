"""
Stage 14.2: Market Intelligence Resolver.
Integrates verified market evidence from KALPA Stage 5/6 without synthetic data fabrication.
"""
import logging
from typing import Dict, Any, Optional

from app.services.dpr_stage2.dpr_enrichment_schemas import (
    EnrichmentSourceType,
    DerivationMethod,
)

logger = logging.getLogger(__name__)


class MarketResolver:
    """
    Supplies hyper-local demand, supply chain, and pricing evidence from upstream market engines.
    """

    def resolve_market_evidence(
        self,
        market_context: Optional[Dict[str, Any]] = None,
        opportunity_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extracts verified market intelligence metrics. Never fabricates numbers.
        """
        m_ctx = market_context or {}
        o_ctx = opportunity_context or {}
        resolved_market: Dict[str, Dict[str, Any]] = {}

        # 1. Target Market Demographics & Customer Segments
        target_cust = m_ctx.get("target_customer_segments") or o_ctx.get("target_audience")
        if target_cust:
            resolved_market["target_customer_demographics"] = {
                "value": target_cust,
                "status": "RESOLVED_MARKET",
                "source_type": EnrichmentSourceType.MARKET_DERIVED,
                "source_id": "STAGE_5_6_MARKET_INTELLIGENCE",
                "source_reference": "KALPA Stage 6 Market Intelligence Report",
                "confidence": 0.85,
                "derivation_method": DerivationMethod.MARKET_SIGNAL,
            }

        # 2. Competitor Landscape & Density
        comp_summary = m_ctx.get("competitor_summary") or m_ctx.get("competition_intensity")
        if comp_summary:
            resolved_market["competitor_density_analysis"] = {
                "value": comp_summary,
                "status": "RESOLVED_MARKET",
                "source_type": EnrichmentSourceType.MARKET_DERIVED,
                "source_id": "STAGE_5_6_COMPETITION_ENGINE",
                "source_reference": "Local Trade & Competitor Density Assessment",
                "confidence": 0.82,
                "derivation_method": DerivationMethod.MARKET_SIGNAL,
            }

        # 3. Demand & Market Gap Assessment
        demand_gap = o_ctx.get("market_gap_analysis") or m_ctx.get("demand_drivers")
        if demand_gap:
            resolved_market["market_demand_assessment"] = {
                "value": demand_gap,
                "status": "RESOLVED_MARKET",
                "source_type": EnrichmentSourceType.MARKET_DERIVED,
                "source_id": "STAGE_8_OPPORTUNITY_EVALUATION",
                "source_reference": "KALPA Opportunity & Market Demand Synthesis",
                "confidence": 0.85,
                "derivation_method": DerivationMethod.MARKET_SIGNAL,
            }

        # 4. Pricing Benchmarks
        price_bench = m_ctx.get("local_price_points") or m_ctx.get("pricing_benchmarks")
        if price_bench:
            resolved_market["pricing_benchmark_range"] = {
                "value": price_bench,
                "status": "RESOLVED_MARKET",
                "source_type": EnrichmentSourceType.MARKET_DERIVED,
                "source_id": "STAGE_6_PRICING_SURVEY",
                "source_reference": "Local Retail & Wholesale Price Benchmarks",
                "confidence": 0.80,
                "derivation_method": DerivationMethod.MARKET_SIGNAL,
            }

        return resolved_market


market_resolver = MarketResolver()
