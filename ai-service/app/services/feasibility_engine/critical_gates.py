"""
Critical Gates Evaluator (Layer 1 Hard Constraints).
Evaluates non-negotiable viability criteria before weighted synthesis:
1. Financial Capacity (DSCR & Debt Serviceability)
2. Critical Infrastructure (3-Phase Power & Premises Suitability)
3. Market Capacity & Saturation (Demand Density vs Competitor Saturation)
4. Statutory & Regulatory Compliance (Mandatory Certifications & Licensure)
"""
from typing import List, Dict, Any, Optional
from app.schemas.feasibility import CriticalGateResult, FeasibilityFeatureVector


class CriticalGatesEvaluator:
    """Evaluates hard constraints and critical failure gates."""

    def evaluate_gates(
        self,
        feature_vector: FeasibilityFeatureVector,
        business_profile: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        entrepreneur_data: Optional[Dict[str, Any]] = None
    ) -> List[CriticalGateResult]:
        gates: List[CriticalGateResult] = []
        bus = business_profile or {}
        rsk = risk_data or {}
        ent = entrepreneur_data or {}

        # -------------------------------------------------------------------
        # 1. Financial Capacity Gate
        # -------------------------------------------------------------------
        dscr_val = float(feature_vector.dscr.value) if feature_vector.dscr.value is not None else 1.65
        bep_val = float(feature_vector.break_even_percentage.value) if feature_vector.break_even_percentage.value is not None else 55.0

        if dscr_val < 1.15:
            fin_status = "RESTRICT"
            fin_expl = (
                f"Projected DSCR of {dscr_val:.2f}x is below the statutory bankability threshold of 1.15x. "
                "The venture cannot reliably service planned debt obligations without structural capital restructuring."
            )
        elif dscr_val < 1.35 or bep_val > 75.0:
            fin_status = "CAUTION"
            fin_expl = (
                f"DSCR of {dscr_val:.2f}x (Benchmark: 1.35x) and Break-even of {bep_val:.1f}% provide a narrow "
                "operating safety margin against seasonal revenue dips."
            )
        else:
            fin_status = "PASS"
            fin_expl = (
                f"DSCR of {dscr_val:.2f}x exceeds the 1.35x benchmark. Break-even capacity utilization of {bep_val:.1f}% "
                "ensures robust operational margin."
            )

        gates.append(
            CriticalGateResult(
                gate_id="FINANCIAL_CAPACITY",
                name="Debt Service & Financial Capacity",
                status=fin_status,
                evidence=f"DSCR: {dscr_val:.2f}x, Break-Even: {bep_val:.1f}%",
                threshold="DSCR >= 1.15x (Min), >= 1.35x (Target), Break-Even <= 70%",
                actual_value=f"DSCR {dscr_val:.2f}x, BEP {bep_val:.1f}%",
                explanation=fin_expl,
                source_stage="STAGE_9_FINANCIAL"
            )
        )

        # -------------------------------------------------------------------
        # 2. Critical Infrastructure Gate
        # -------------------------------------------------------------------
        infra_risk_score = float(feature_vector.infrastructure_risk.value) if feature_vector.infrastructure_risk.value is not None else 0.20
        res_score = float(feature_vector.resources_score.value) if feature_vector.resources_score.value is not None else 75.0

        # Check for 3-phase power mismatch from Stage 11 or Stage 10
        mismatch_3phase = False
        cat_infra = rsk.get("category_risks", {}).get("INFRASTRUCTURE", {})
        if infra_risk_score >= 0.80 or "3-phase" in str(cat_infra.get("drivers", "")).lower() or "power" in str(cat_infra.get("drivers", "")).lower():
            mismatch_3phase = True

        if mismatch_3phase:
            infra_status = "RESTRICT"
            infra_expl = (
                "Critical power infrastructure mismatch: The business domain requires a 3-Phase commercial power connection "
                "for machinery/processing, but the operating site lacks verified 3-phase grid capacity."
            )
        elif res_score < 40.0 or infra_risk_score >= 0.50:
            infra_status = "CAUTION"
            infra_expl = (
                f"Infrastructure readiness score of {res_score:.0f}/100 indicates premises floor area or utility access "
                "is constrained and requires operational adjustments."
            )
        else:
            infra_status = "PASS"
            infra_expl = "Premises floor area, grid connectivity, and site accessibility satisfy business domain technical standards."

        gates.append(
            CriticalGateResult(
                gate_id="CRITICAL_INFRASTRUCTURE",
                name="Site Utilities & Power Infrastructure",
                status=infra_status,
                evidence=f"Infrastructure Risk: {infra_risk_score:.2f}, Resource Score: {res_score:.0f}/100",
                threshold="Compatible power rating (Single/3-Phase) & adequate floor area",
                actual_value="3-Phase Mismatch" if mismatch_3phase else f"Risk: {infra_risk_score:.2f}",
                explanation=infra_expl,
                source_stage="STAGE_11_RISK & STAGE_10_ENTREPRENEUR"
            )
        )

        # -------------------------------------------------------------------
        # 3. Market Capacity & Saturation Gate
        # -------------------------------------------------------------------
        mkt_opp_score = float(feature_vector.market_opportunity_score.value) if feature_vector.market_opportunity_score.value is not None else 70.0
        demand_idx = float(feature_vector.demand_index.value) if feature_vector.demand_index.value is not None else 0.60
        comp_risk = float(feature_vector.competition_risk.value) if feature_vector.competition_risk.value is not None else 0.35

        if demand_idx < 0.30 and comp_risk >= 0.70:
            mkt_status = "RESTRICT"
            mkt_expl = (
                "Severe market saturation: Addressable local demand is low while competitor clustering density is critical. "
                "High risk of price erosion and inadequate customer footfall."
            )
        elif mkt_opp_score < 50.0 or comp_risk >= 0.60 or demand_idx < 0.40:
            mkt_status = "CAUTION"
            mkt_expl = (
                f"Market opportunity score ({mkt_opp_score:.0f}/100) and competition pressure ({comp_risk:.2f}) require "
                "a clear customer acquisition strategy and differentiated product mix."
            )
        else:
            mkt_status = "PASS"
            mkt_expl = (
                f"Sufficient addressable demand density ({demand_idx:.2f}) and manageable competitive pressure ({comp_risk:.2f}) "
                f"support healthy sales velocity."
            )

        gates.append(
            CriticalGateResult(
                gate_id="MARKET_CAPACITY",
                name="Addressable Market & Demand Capacity",
                status=mkt_status,
                evidence=f"Market Opportunity: {mkt_opp_score:.0f}/100, Demand Index: {demand_idx:.2f}, Comp Risk: {comp_risk:.2f}",
                threshold="Opportunity Score >= 50/100, Demand Index >= 0.40",
                actual_value=f"Opportunity {mkt_opp_score:.0f}/100, Demand {demand_idx:.2f}",
                explanation=mkt_expl,
                source_stage="STAGE_8_OPPORTUNITY & STAGE_6_MARKET"
            )
        )

        # -------------------------------------------------------------------
        # 4. Statutory & Regulatory Compliance Gate
        # -------------------------------------------------------------------
        train_score = float(feature_vector.training_score.value) if feature_vector.training_score.value is not None else 75.0
        skills_score = float(feature_vector.skills_score.value) if feature_vector.skills_score.value is not None else 75.0

        # Check if mandatory compliance training gap was identified in stage 10
        gaps = ent.get("gaps", [])
        has_mandatory_training_gap = any(
            g.get("dimension") == "training" and g.get("severity") == "HIGH" for g in gaps if isinstance(g, dict)
        )

        if has_mandatory_training_gap and train_score < 30.0:
            stat_status = "CAUTION"
            stat_expl = (
                "Statutory domain training / certification (e.g. FSSAI FoSTaC, Trade Registration) is required before commercial "
                "commencement, but entrepreneur has not yet completed formal enrollment."
            )
        elif train_score < 50.0 or skills_score < 35.0:
            stat_status = "CAUTION"
            stat_expl = (
                f"Operational capability score ({skills_score:.0f}/100) indicates foundational training is recommended "
                "to ensure statutory operating compliance."
            )
        else:
            stat_status = "PASS"
            stat_expl = "Statutory compliance path is clear and entrepreneur holds requisite foundational experience/willingness."

        gates.append(
            CriticalGateResult(
                gate_id="STATUTORY_COMPLIANCE",
                name="Statutory Licensure & Domain Certifications",
                status=stat_status,
                evidence=f"Training Score: {train_score:.0f}/100, Skills Score: {skills_score:.0f}/100",
                threshold="Requisite statutory compliance pathway & certifications confirmed",
                actual_value=f"Training {train_score:.0f}/100",
                explanation=stat_expl,
                source_stage="STAGE_10_ENTREPRENEUR"
            )
        )

        return gates


critical_gates_evaluator = CriticalGatesEvaluator()
