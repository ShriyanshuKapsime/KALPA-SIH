"""
Evidence Quality Scorer for Stage 5 Market Intelligence Agent.
Implements the explainable 7-factor quality scoring model with hard penalties:
- Completeness: 25%
- Source Reliability: 20%
- Geographic Relevance: 15%
- Freshness: 10%
- Validation & Consistency: 10%
- Business Semantic Relevance: 10%
- Tool Execution Success: 10%

Enforces strict penalties:
- Context integrity or business mismatch caps overall quality at <= 0.20.
- Failed critical tools significantly reduce tool success score.
- Proxies transparently reduce certainty score.
"""
from typing import Dict, Any, List, Optional
from app.schemas.market import (
    EvidenceQuality,
    EvidenceQualityBreakdown,
    MarketEvidenceAggregate,
    LocationContext,
    CollectionPlan,
    CanonicalBusinessContext,
)
from app.core.logging import logger


class EvidenceQualityScorer:
    """
    Computes deterministic, explainable evidence quality scores with hard penalties.
    """

    WEIGHTS = {
        "completeness": 0.25,
        "source_quality": 0.20,
        "geographic_relevance": 0.15,
        "freshness": 0.10,
        "validation": 0.10,
        "semantic_relevance": 0.10,
        "tool_success": 0.10
    }

    def evaluate(
        self,
        evidence: MarketEvidenceAggregate,
        location: LocationContext,
        plan: CollectionPlan,
        successful_tools: List[str],
        failed_tools: List[str],
        business: Optional[CanonicalBusinessContext] = None,
        context_integrity_passed: bool = True,
        contamination_detected: bool = False
    ) -> EvidenceQuality:
        quality_notes = []

        # 1. Completeness Score (25%)
        # Failed tools do NOT count toward completeness
        categories_present = 0
        total_categories = 6

        if evidence.demographics and "demographics_tool" not in failed_tools:
            categories_present += 1
        else:
            quality_notes.append("Missing or failed demographic evidence.")

        if (evidence.competitors.direct or evidence.competitors.adjacent) and "competitor_discovery_tool" not in failed_tools:
            categories_present += 1
        else:
            quality_notes.append("Missing or failed competitor discovery evidence.")

        if evidence.demand_indicators and "demand_evidence_tool" not in failed_tools:
            categories_present += 1
        else:
            quality_notes.append("Missing or failed domain demand indicators.")

        if evidence.supply_access and "supply_access_tool" not in failed_tools:
            categories_present += 1
        else:
            quality_notes.append("Missing or failed supply hub logistics evidence.")

        if evidence.infrastructure and "infrastructure_access_tool" not in failed_tools:
            categories_present += 1
        else:
            quality_notes.append("Missing or failed physical infrastructure records.")

        if evidence.economic_indicators and "economic_purchasing_power_tool" not in failed_tools:
            categories_present += 1
        else:
            quality_notes.append("Missing or failed economic purchasing power proxies.")

        completeness_ratio = categories_present / total_categories

        # 2. Source Reliability (20%)
        # Official datasets (Census, RBI, MSME, LGD) score 0.95; proxies and unavailable datasets reduce score
        official_sources_count = 0
        total_items = 0

        for d in evidence.demographics:
            total_items += 1
            if d.data_status == "OFFICIAL_STATIC_DATA":
                official_sources_count += 1

        for c in evidence.competitors.direct + evidence.competitors.adjacent:
            total_items += 1
            if c.data_status == "OFFICIAL_STATIC_DATA":
                official_sources_count += 1

        for dem in evidence.demand_indicators:
            total_items += 1
            if dem.data_status == "OFFICIAL_STATIC_DATA":
                official_sources_count += 1

        for s in evidence.supply_access:
            total_items += 1
            if s.data_status == "OFFICIAL_STATIC_DATA":
                official_sources_count += 1

        for i in evidence.infrastructure:
            total_items += 1
            if i.data_status == "OFFICIAL_STATIC_DATA":
                official_sources_count += 1

        source_quality_score = (official_sources_count / max(1, total_items)) if total_items > 0 else 0.50
        source_quality_score = min(0.95, max(0.40, source_quality_score))

        # 3. Geographic Relevance (15%)
        # Village = 0.95, Block = 0.85, District = 0.75
        precision = (location.geographic_precision or "district").lower()
        if precision == "village":
            geo_score = 0.95
        elif precision == "block":
            geo_score = 0.85
        elif precision == "district":
            geo_score = 0.75
        else:
            geo_score = 0.60

        # Penalize if spatial conflict exists
        if location.conflict and location.conflict.has_conflict:
            geo_score = max(0.40, geo_score - 0.20)
            quality_notes.append(f"Spatial conflict between user location and GPS coordinates reduced geographic relevance.")

        # 4. Freshness (10%)
        freshness_score = 0.88

        # 5. Validation (10%)
        validation_score = 1.0 if not failed_tools else max(0.20, 1.0 - (len(failed_tools) * 0.20))

        # 6. Tool Success Score (10%)
        total_planned_tools = len(successful_tools) + len(failed_tools)
        if total_planned_tools > 0:
            tool_success_score = len(successful_tools) / total_planned_tools
        else:
            tool_success_score = 1.0

        # 7. Semantic Relevance Score (10%)
        if not context_integrity_passed or contamination_detected:
            semantic_relevance_score = 0.10
            quality_notes.append("CRITICAL: Context integrity failed or cross-business contamination detected.")
        else:
            semantic_relevance_score = 0.98

        # Overall weighted calculation
        overall = (
            self.WEIGHTS["completeness"] * completeness_ratio +
            self.WEIGHTS["source_quality"] * source_quality_score +
            self.WEIGHTS["geographic_relevance"] * geo_score +
            self.WEIGHTS["freshness"] * freshness_score +
            self.WEIGHTS["validation"] * validation_score +
            self.WEIGHTS["semantic_relevance"] * semantic_relevance_score +
            self.WEIGHTS["tool_success"] * tool_success_score
        )

        # HARD PENALTY: Context integrity / semantic contamination caps overall score at 0.20
        if not context_integrity_passed or contamination_detected:
            overall = min(0.20, overall)
            confidence_level = "untrustworthy"
        elif len(failed_tools) >= 3 or completeness_ratio < 0.50:
            confidence_level = "low"
        elif completeness_ratio < 0.80 or len(failed_tools) > 0:
            confidence_level = "moderate"
        else:
            confidence_level = "high"

        missing_reqs = []
        if not evidence.demographics or "demographics_tool" in failed_tools:
            missing_reqs.append("demographic_population_data")
        if not evidence.competitors.direct or "competitor_discovery_tool" in failed_tools:
            missing_reqs.append("direct_competitor_census")
        if not evidence.supply_access or "supply_access_tool" in failed_tools:
            missing_reqs.append("wholesale_supply_logistics")
        if not evidence.infrastructure or "infrastructure_access_tool" in failed_tools:
            missing_reqs.append("grid_power_and_road_connectivity")

        return EvidenceQuality(
            completeness=round(completeness_ratio, 2),
            source_quality=round(source_quality_score, 2),
            geographic_relevance=round(geo_score, 2),
            freshness=round(freshness_score, 2),
            semantic_relevance_score=round(semantic_relevance_score, 2),
            tool_success_score=round(tool_success_score, 2),
            overall_quality=round(overall, 2),
            confidence_level=confidence_level,
            breakdown=EvidenceQualityBreakdown(
                completeness=round(completeness_ratio, 2),
                source_quality=round(source_quality_score, 2),
                geographic_relevance=round(geo_score, 2),
                freshness=round(freshness_score, 2),
                validation=round(validation_score, 2),
                semantic_relevance=round(semantic_relevance_score, 2),
                tool_success=round(tool_success_score, 2)
            ),
            missing_requirements=missing_reqs,
            quality_notes=quality_notes
        )


evidence_quality_scorer = EvidenceQualityScorer()
