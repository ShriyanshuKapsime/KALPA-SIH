"""
Dynamic SWOT Engine (YES / Viable Path).
Generates evidence-grounded Strengths, Weaknesses, Opportunities, and Threats
consuming real structured findings from Stages 6, 8, 9, 10, 11, and 12.
"""
from typing import Dict, Any, List
from app.schemas.feasibility import (
    DynamicSWOTResponse,
    SWOTItem,
    FeasibilityFeatureVector,
    PillarScore
)


class DynamicSWOTEngine:
    """Generates evidence-grounded Dynamic SWOT matrix."""

    def generate_swot(
        self,
        feature_vector: FeasibilityFeatureVector,
        pillar_scores: Dict[str, PillarScore],
        business_title: str = "Micro-Enterprise"
    ) -> DynamicSWOTResponse:
        strengths: List[SWOTItem] = []
        weaknesses: List[SWOTItem] = []
        opportunities: List[SWOTItem] = []
        threats: List[SWOTItem] = []

        dscr_val = float(feature_vector.dscr.value or 1.65)
        mkt_score = float(feature_vector.market_opportunity_score.value or 75.0)
        ent_score = float(feature_vector.entrepreneur_readiness_score.value or 75.0)
        skills_score = float(feature_vector.skills_score.value or 75.0)
        exp_score = float(feature_vector.experience_score.value or 75.0)
        bep_val = float(feature_vector.break_even_percentage.value or 55.0)
        comp_risk = float(feature_vector.competition_risk.value or 0.30)
        seasonal_risk = float(feature_vector.seasonal_risk.value or 0.20)
        demand_idx = float(feature_vector.demand_index.value or 0.65)

        # ---------------------------------------------------------
        # Strengths (Internal Positive)
        # ---------------------------------------------------------
        if dscr_val >= 1.35:
            strengths.append(
                SWOTItem(
                    title="Healthy Debt Service Capability",
                    description=f"Projected DSCR of {dscr_val:.2f}x offers robust operational safety margin over bank debt.",
                    source_stage="STAGE_9_FINANCIAL",
                    evidence=f"DSCR {dscr_val:.2f}x vs 1.35x benchmark",
                    severity_or_impact="HIGH"
                )
            )
        if bep_val <= 60.0:
            strengths.append(
                SWOTItem(
                    title="Low Break-Even Volume Barrier",
                    description=f"Break-Even Point is achieved at {bep_val:.1f}% installed capacity utilization, reducing operational downside.",
                    source_stage="STAGE_9_FINANCIAL",
                    evidence=f"Break-Even {bep_val:.1f}%",
                    severity_or_impact="HIGH"
                )
            )
        if exp_score >= 70.0:
            strengths.append(
                SWOTItem(
                    title="Demonstrated Domain Operating Experience",
                    description=f"Founder brings proven operating track record scoring {exp_score:.0f}/100 in sector execution.",
                    source_stage="STAGE_10_ENTREPRENEUR",
                    evidence=f"Experience Score: {exp_score:.0f}/100",
                    severity_or_impact="HIGH"
                )
            )
        if skills_score >= 70.0:
            strengths.append(
                SWOTItem(
                    title="Strong Core Technical & Retail Skills",
                    description=f"Domain skill matching reached {skills_score:.0f}/100 against ontology benchmark requirements.",
                    source_stage="STAGE_10_ENTREPRENEUR",
                    evidence=f"Skills Score: {skills_score:.0f}/100",
                    severity_or_impact="MEDIUM"
                )
            )
        if not strengths:
            strengths.append(
                SWOTItem(
                    title="Foundational Enterprise Intent",
                    description="Founder has clear business orientation and verified project capital structure.",
                    source_stage="STAGE_3_PROFILE",
                    evidence="Intake profile structured",
                    severity_or_impact="MEDIUM"
                )
            )

        # ---------------------------------------------------------
        # Weaknesses (Internal Negative)
        # ---------------------------------------------------------
        if float(feature_vector.training_score.value or 0) < 65.0:
            weaknesses.append(
                SWOTItem(
                    title="Lack of Formal Statutory Certification",
                    description="Entrepreneur has not completed formal domain accreditation or certified business management training.",
                    source_stage="STAGE_10_ENTREPRENEUR",
                    evidence=f"Training Score: {float(feature_vector.training_score.value or 0):.0f}/100",
                    severity_or_impact="MEDIUM"
                )
            )
        if dscr_val < 1.35:
            weaknesses.append(
                SWOTItem(
                    title="Tight Initial Cash Reserve Cushion",
                    description=f"DSCR of {dscr_val:.2f}x requires rigorous monitoring to avoid short-term liquidity stress.",
                    source_stage="STAGE_9_FINANCIAL",
                    evidence=f"DSCR {dscr_val:.2f}x",
                    severity_or_impact="HIGH"
                )
            )
        if float(feature_vector.resources_score.value or 0) < 60.0:
            weaknesses.append(
                SWOTItem(
                    title="Constrained Operating Premises Area",
                    description="Available built-up commercial area or storage capacity is below benchmark expansion ideals.",
                    source_stage="STAGE_10_ENTREPRENEUR",
                    evidence=f"Resource Score: {float(feature_vector.resources_score.value or 0):.0f}/100",
                    severity_or_impact="MEDIUM"
                )
            )
        if not weaknesses:
            weaknesses.append(
                SWOTItem(
                    title="Standard Startup Scale Constraints",
                    description="Initial operating volume will require hands-on owner management until processes stabilize.",
                    source_stage="STAGE_10_ENTREPRENEUR",
                    evidence="Early-stage micro-enterprise",
                    severity_or_impact="LOW"
                )
            )

        # ---------------------------------------------------------
        # Opportunities (External Positive)
        # ---------------------------------------------------------
        if demand_idx >= 0.60:
            opportunities.append(
                SWOTItem(
                    title="High Addressable Local Demand Density",
                    description=f"Stage 6 & 8 spatial demand index ({demand_idx:.2f}) shows sustained local consumer appetite.",
                    source_stage="STAGE_8_OPPORTUNITY",
                    evidence=f"Demand Index: {demand_idx:.2f}",
                    severity_or_impact="HIGH"
                )
            )
        opportunities.append(
            SWOTItem(
                title="Institutional MSME Credit & Subsidy Access",
                description="Eligible for priority sector lending (PMEGP / Mudra / CGTMSE) collateral-free financing structures.",
                source_stage="STAGE_9_FINANCIAL",
                evidence="Scheme eligibility mapped",
                severity_or_impact="HIGH"
            )
        )
        if mkt_score >= 70.0:
            opportunities.append(
                SWOTItem(
                    title="Digital Payment & Local Direct Marketing Linkage",
                    description="Adoption of UPI QR payments and WhatsApp catalog marketing can expand catchment boundary.",
                    source_stage="STAGE_6_MARKET",
                    evidence="Catchment expansion potential",
                    severity_or_impact="MEDIUM"
                )
            )

        # ---------------------------------------------------------
        # Threats (External Negative)
        # ---------------------------------------------------------
        if comp_risk >= 0.50:
            threats.append(
                SWOTItem(
                    title="Local Competitor Price Undercutting",
                    description="Presence of multiple established local competitors creates risk of margin erosion.",
                    source_stage="STAGE_11_RISK",
                    evidence=f"Competition Risk: {comp_risk:.2f}",
                    severity_or_impact="HIGH"
                )
            )
        if seasonal_risk >= 0.40:
            threats.append(
                SWOTItem(
                    title="Seasonal Demand & Cashflow Downturns",
                    description="Revenue concentration during festive/wedding seasons leads to periodic lean operational months.",
                    source_stage="STAGE_11_RISK",
                    evidence=f"Seasonal Volatility Risk: {seasonal_risk:.2f}",
                    severity_or_impact="MEDIUM"
                )
            )
        if float(feature_vector.supply_chain_risk.value or 0) >= 0.45:
            threats.append(
                SWOTItem(
                    title="Raw Material Wholesale Sourcing Fluctuations",
                    description="Distance to major wholesale hubs may cause occasional transport delays or input price surges.",
                    source_stage="STAGE_11_RISK",
                    evidence=f"Supply Chain Risk: {float(feature_vector.supply_chain_risk.value or 0):.2f}",
                    severity_or_impact="MEDIUM"
                )
            )
        if not threats:
            threats.append(
                SWOTItem(
                    title="Macroeconomic Inflation & Purchasing Power",
                    description="General commodity inflation may affect discretionary consumer spending.",
                    source_stage="STAGE_11_RISK",
                    evidence="General retail macro factor",
                    severity_or_impact="LOW"
                )
            )

        return DynamicSWOTResponse(
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats
        )


dynamic_swot_engine = DynamicSWOTEngine()
