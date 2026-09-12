"""
Supply Ecosystem Analysis Layer for Stage 6 Market Intelligence Engine.
Assesses raw material sourcing, wholesale market proximity, distance suitability,
and critical input coverage against NABARD and business supply benchmarks.
"""
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    SupplyRiskLevel,
    SupplyEcosystemAnalysisResult,
    CleanedSupplyHub
)


class SupplyEcosystemAnalysisService:
    def analyze_supply_ecosystem(
        self,
        supply_hubs: List[CleanedSupplyHub],
        benchmarks: Dict[str, Any]
    ) -> SupplyEcosystemAnalysisResult:
        """
        Executes deterministic supply ecosystem and critical input coverage analysis.
        """
        supply_bm = benchmarks.get("supply_access", {})
        ideal_km = float(supply_bm.get("ideal_distance_km", 15.0))
        acceptable_km = float(supply_bm.get("acceptable_distance_km", 50.0))
        expected_inputs = supply_bm.get("critical_inputs", [
            "Raw materials / primary inputs",
            "Energy & operating supplies",
            "Transport / packaging logistics"
        ])

        if not supply_hubs:
            return SupplyEcosystemAnalysisResult(
                accessibility="UNKNOWN",
                hub_count=0,
                nearest_hub_distance_km=None,
                critical_input_coverage={"covered": [], "missing_evidence": expected_inputs},
                distance_assessment="UNKNOWN_NO_HUBS",
                supply_risk=SupplyRiskLevel.ELEVATED_DUE_TO_DATA_GAP,
                supply_risk_score=0.70,
                hubs=[],
                confidence=0.40
            )

        nearest_dist = min(h.distance_km for h in supply_hubs)
        hub_count = len(supply_hubs)

        # Distance Assessment
        if nearest_dist <= ideal_km:
            dist_assessment = "IDEAL_PROXIMITY"
        elif nearest_dist <= acceptable_km:
            dist_assessment = "ACCEPTABLE_DISTANCE"
        else:
            dist_assessment = "DISTANT_SUPPLY_CHAIN"

        # Critical Input Coverage Matching
        all_available_commodities = set()
        for h in supply_hubs:
            for c in h.commodities_available:
                all_available_commodities.add(c.lower())

        covered_inputs = []
        missing_inputs = []

        for exp in expected_inputs:
            exp_lower = exp.lower()
            # Match keywords
            matched = any(
                comm in exp_lower or exp_lower in comm or
                any(token in comm for token in exp_lower.split() if len(token) > 3)
                for comm in all_available_commodities
            )
            if matched:
                covered_inputs.append(exp)
            else:
                # If wholesale market/mandi exists, partial coverage is supported
                if any("mandi" in h.hub_type.lower() or "market" in h.hub_type.lower() for h in supply_hubs):
                    covered_inputs.append(f"{exp} (via Wholesale APMC/Trade Hub)")
                else:
                    missing_inputs.append(exp)

        coverage_ratio = len(covered_inputs) / max(1, len(expected_inputs))

        # Overall Accessibility & Risk
        high_accessible_count = sum(1 for h in supply_hubs if h.accessibility_rating == "high")
        if high_accessible_count > 0 and nearest_dist <= acceptable_km:
            overall_accessibility = "HIGH"
        elif nearest_dist <= acceptable_km:
            overall_accessibility = "MODERATE"
        else:
            overall_accessibility = "RESTRICTED"

        if coverage_ratio >= 0.70 and nearest_dist <= acceptable_km:
            supply_risk = SupplyRiskLevel.LOW
            supply_risk_score = 0.20
        elif coverage_ratio >= 0.40 or nearest_dist <= acceptable_km:
            supply_risk = SupplyRiskLevel.MODERATE
            supply_risk_score = 0.45
        else:
            supply_risk = SupplyRiskLevel.HIGH
            supply_risk_score = 0.75

        return SupplyEcosystemAnalysisResult(
            accessibility=overall_accessibility,
            hub_count=hub_count,
            nearest_hub_distance_km=round(nearest_dist, 2),
            critical_input_coverage={
                "covered": covered_inputs,
                "missing_evidence": missing_inputs,
                "coverage_ratio": round(coverage_ratio, 2)
            },
            distance_assessment=dist_assessment,
            supply_risk=supply_risk,
            supply_risk_score=supply_risk_score,
            hubs=supply_hubs,
            confidence=0.82
        )


supply_ecosystem_service = SupplyEcosystemAnalysisService()
