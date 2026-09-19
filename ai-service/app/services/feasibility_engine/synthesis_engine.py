"""
Feasibility Synthesis Engine (Layer 2 Explainable Synthesis).
Combines the 4 Core Analytical Pillars:
1. Market Opportunity (25%)
2. Financial Viability (35%)
3. Entrepreneur Readiness (20%)
4. Business Risk Resilience (20%)

Enforces Critical Gate decisions and computes the final explainable decision.
"""
from typing import Dict, Any, List, Tuple
from app.schemas.feasibility import (
    FeasibilityFeatureVector,
    CriticalGateResult,
    PillarScore
)


class FeasibilitySynthesisEngine:
    """Computes deterministic 4-pillar synthesis and authoritative decision."""

    # Centralized Pillar Weights
    WEIGHT_MARKET = 0.25
    WEIGHT_FINANCE = 0.35
    WEIGHT_ENTREPRENEUR = 0.20
    WEIGHT_RISK_RESILIENCE = 0.20

    def synthesize(
        self,
        feature_vector: FeasibilityFeatureVector,
        critical_gates: List[CriticalGateResult],
        business_title: str = "Micro-Enterprise"
    ) -> Tuple[float, str, str, float, Dict[str, PillarScore], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes explainable 4-pillar synthesis.
        Returns:
            (overall_score, decision, recommendation, confidence, pillar_scores,
             positive_drivers, key_constraints, conditions, calculation_provenance, data_completeness)
        """
        provenance: List[Dict[str, Any]] = []

        # -------------------------------------------------------------------
        # 1. Market Opportunity Pillar (25%)
        # -------------------------------------------------------------------
        mkt_is_gap = feature_vector.market_opportunity_score.value is None or feature_vector.market_opportunity_score.status == "DATA_GAP"
        if mkt_is_gap:
            mkt_val = 0.0
            mkt_conf = 0.0
            mkt_contrib = 0.0
            mkt_status = "DATA_GAP"
            mkt_expl = "Stage 8 Opportunity Evaluation outputs not available (DATA_GAP)."
            mkt_calc = "Stage 8 Market Opportunity data missing → 0.0 pts (DATA_GAP)"
        else:
            mkt_val = float(feature_vector.market_opportunity_score.value)
            mkt_conf = feature_vector.market_opportunity_score.confidence
            mkt_contrib = mkt_val * self.WEIGHT_MARKET
            mkt_status = "STRONG" if mkt_val >= 75.0 else ("ADEQUATE" if mkt_val >= 50.0 else "CAUTION")
            mkt_expl = f"Stage 8 Opportunity Index scored {mkt_val:.1f}/100 based on local demand density and catchment accessibility."
            mkt_calc = f"Composite Opportunity Score ({mkt_val:.1f}/100) × {int(self.WEIGHT_MARKET*100)}% Weight = {mkt_contrib:.2f} pts"

        pillar_market = PillarScore(
            pillar="MARKET_OPPORTUNITY",
            title="Market Opportunity & Demand Potential",
            score=round(mkt_val, 1) if not mkt_is_gap else 0.0,
            weight=self.WEIGHT_MARKET,
            weighted_contribution=round(mkt_contrib, 2),
            source_stage="STAGE_8_OPPORTUNITY" if not mkt_is_gap else "DATA_GAP",
            status=mkt_status,
            confidence=mkt_conf,
            explanation=mkt_expl,
            key_inputs={
                "opportunity_score": mkt_val if not mkt_is_gap else None,
                "demand_index": feature_vector.demand_index.value,
                "competition_pressure": feature_vector.competition_pressure.value,
                "market_accessibility": feature_vector.market_accessibility.value
            },
            formula=f"{mkt_val:.1f} × {self.WEIGHT_MARKET:.2f} = {mkt_contrib:.2f} pts" if not mkt_is_gap else "DATA_GAP"
        )
        provenance.append({
            "dimension": "MARKET_OPPORTUNITY",
            "score": round(mkt_val, 1) if not mkt_is_gap else None,
            "weight": self.WEIGHT_MARKET,
            "weighted_contribution": round(mkt_contrib, 2),
            "status": mkt_status,
            "source": "Stage 8 Opportunity Evaluation" if not mkt_is_gap else "DATA_GAP",
            "calculation": mkt_calc
        })

        # -------------------------------------------------------------------
        # 2. Financial Viability Pillar (35%)
        # -------------------------------------------------------------------
        fin_is_gap = feature_vector.financial_viability_score.value is None or feature_vector.financial_viability_score.status == "DATA_GAP"
        dscr_val = float(feature_vector.dscr.value) if feature_vector.dscr.value is not None else None
        bep_val = float(feature_vector.break_even_percentage.value) if feature_vector.break_even_percentage.value is not None else None

        if fin_is_gap:
            fin_val = 0.0
            fin_conf = 0.0
            fin_contrib = 0.0
            fin_status = "DATA_GAP"
            fin_expl = "Stage 9 Financial Analysis outputs not available (DATA_GAP)."
            fin_calc = "Stage 9 Financial Viability model missing → 0.0 pts (DATA_GAP)"
        else:
            fin_val = float(feature_vector.financial_viability_score.value)
            fin_conf = feature_vector.financial_viability_score.confidence
            fin_contrib = fin_val * self.WEIGHT_FINANCE
            fin_status = "STRONG" if fin_val >= 75.0 else ("ADEQUATE" if fin_val >= 50.0 else "RESTRICT")
            dscr_str = f"{dscr_val:.2f}x" if dscr_val is not None else "N/A"
            bep_str = f"{bep_val:.1f}%" if bep_val is not None else "N/A"
            fin_expl = f"Stage 9 Financial Analysis indicates DSCR of {dscr_str} and Break-Even Point of {bep_str}."
            fin_calc = f"Financial Synthesis Score ({fin_val:.1f}/100) based on DSCR {dscr_str} & BEP {bep_str} × {int(self.WEIGHT_FINANCE*100)}% Weight = {fin_contrib:.2f} pts"

        pillar_finance = PillarScore(
            pillar="FINANCIAL_VIABILITY",
            title="Financial Viability & Repayment Buffer",
            score=round(fin_val, 1) if not fin_is_gap else 0.0,
            weight=self.WEIGHT_FINANCE,
            weighted_contribution=round(fin_contrib, 2),
            source_stage="STAGE_9_FINANCIAL" if not fin_is_gap else "DATA_GAP",
            status=fin_status,
            confidence=fin_conf,
            explanation=fin_expl,
            key_inputs={
                "financial_score": fin_val if not fin_is_gap else None,
                "dscr": dscr_val,
                "break_even_percentage": bep_val,
                "total_project_cost": feature_vector.project_cost.value,
                "loan_amount": feature_vector.loan_amount.value,
                "monthly_emi": feature_vector.emi.value
            },
            formula=f"{fin_val:.1f} × {self.WEIGHT_FINANCE:.2f} = {fin_contrib:.2f} pts" if not fin_is_gap else "DATA_GAP"
        )
        provenance.append({
            "dimension": "FINANCIAL_VIABILITY",
            "score": round(fin_val, 1) if not fin_is_gap else None,
            "weight": self.WEIGHT_FINANCE,
            "weighted_contribution": round(fin_contrib, 2),
            "status": fin_status,
            "source": "Stage 9 Financial Analysis" if not fin_is_gap else "DATA_GAP",
            "calculation": fin_calc
        })

        # -------------------------------------------------------------------
        # 3. Entrepreneur Readiness Pillar (20%)
        # -------------------------------------------------------------------
        ent_is_gap = feature_vector.entrepreneur_readiness_score.value is None or feature_vector.entrepreneur_readiness_score.status == "DATA_GAP"
        if ent_is_gap:
            ent_val = 0.0
            ent_conf = 0.0
            ent_contrib = 0.0
            ent_status = "DATA_GAP"
            ent_expl = "Stage 10 Entrepreneur Profile readiness not available (DATA_GAP)."
            ent_calc = "Stage 10 Readiness evaluation missing → 0.0 pts (DATA_GAP)"
        else:
            ent_val = float(feature_vector.entrepreneur_readiness_score.value)
            ent_conf = feature_vector.entrepreneur_readiness_score.confidence
            ent_contrib = ent_val * self.WEIGHT_ENTREPRENEUR
            ent_status = "STRONG" if ent_val >= 75.0 else ("ADEQUATE" if ent_val >= 50.0 else "CAUTION")
            ent_expl = f"Stage 10 Profile scored {ent_val:.1f}/100 evaluating skills, operating experience, statutory training, and resources."
            ent_calc = f"Composite Readiness Score ({ent_val:.1f}/100) × {int(self.WEIGHT_ENTREPRENEUR*100)}% Weight = {ent_contrib:.2f} pts"

        pillar_entrepreneur = PillarScore(
            pillar="ENTREPRENEUR_READINESS",
            title="Entrepreneur Competency & Operational Readiness",
            score=round(ent_val, 1) if not ent_is_gap else 0.0,
            weight=self.WEIGHT_ENTREPRENEUR,
            weighted_contribution=round(ent_contrib, 2),
            source_stage="STAGE_10_ENTREPRENEUR" if not ent_is_gap else "DATA_GAP",
            status=ent_status,
            confidence=ent_conf,
            explanation=ent_expl,
            key_inputs={
                "readiness_score": ent_val if not ent_is_gap else None,
                "skills_score": feature_vector.skills_score.value,
                "experience_score": feature_vector.experience_score.value,
                "training_score": feature_vector.training_score.value,
                "resources_score": feature_vector.resources_score.value
            },
            formula=f"{ent_val:.1f} × {self.WEIGHT_ENTREPRENEUR:.2f} = {ent_contrib:.2f} pts" if not ent_is_gap else "DATA_GAP"
        )
        provenance.append({
            "dimension": "ENTREPRENEUR_READINESS",
            "score": round(ent_val, 1) if not ent_is_gap else None,
            "weight": self.WEIGHT_ENTREPRENEUR,
            "weighted_contribution": round(ent_contrib, 2),
            "status": ent_status,
            "source": "Stage 10 Entrepreneur Profile Engine" if not ent_is_gap else "DATA_GAP",
            "calculation": ent_calc
        })

        # -------------------------------------------------------------------
        # 4. Business Risk Resilience Pillar (20%)
        # -------------------------------------------------------------------
        rsk_is_gap = feature_vector.overall_risk_score.value is None or feature_vector.overall_risk_score.status == "DATA_GAP"
        if rsk_is_gap:
            risk_score = None
            resilience_val = 0.0
            risk_conf = 0.0
            rsk_contrib = 0.0
            rsk_status = "DATA_GAP"
            rsk_expl = "Stage 11 Enterprise Risk Engine outputs not available (DATA_GAP)."
            rsk_calc = "Stage 11 Risk model missing → 0.0 pts (DATA_GAP)"
        else:
            risk_score = float(feature_vector.overall_risk_score.value)
            risk_conf = feature_vector.overall_risk_score.confidence
            resilience_val = max(0.0, min(100.0, (1.0 - risk_score) * 100.0))
            rsk_contrib = resilience_val * self.WEIGHT_RISK_RESILIENCE
            rsk_status = "STRONG" if resilience_val >= 70.0 else ("ADEQUATE" if resilience_val >= 45.0 else "CAUTION")
            rsk_expl = f"Stage 11 Risk Engine evaluated 7 vectors yielding overall risk of {risk_score:.2f} (Resilience: {resilience_val:.1f}/100)."
            rsk_calc = f"Risk Inversion: (1.0 - Risk Score {risk_score:.2f}) × 100 = {resilience_val:.1f} × {int(self.WEIGHT_RISK_RESILIENCE*100)}% Weight = {rsk_contrib:.2f} pts"

        pillar_risk = PillarScore(
            pillar="RISK_RESILIENCE",
            title="Multi-Vector Risk Resilience",
            score=round(resilience_val, 1) if not rsk_is_gap else 0.0,
            weight=self.WEIGHT_RISK_RESILIENCE,
            weighted_contribution=round(rsk_contrib, 2),
            source_stage="STAGE_11_RISK" if not rsk_is_gap else "DATA_GAP",
            status=rsk_status,
            confidence=risk_conf,
            explanation=rsk_expl,
            key_inputs={
                "overall_risk_score": risk_score,
                "resilience_score": resilience_val if not rsk_is_gap else None,
                "overall_severity": feature_vector.overall_risk_severity.value,
                "financial_risk": feature_vector.financial_risk.value,
                "market_risk": feature_vector.market_risk.value,
                "operational_risk": feature_vector.operational_risk.value
            },
            formula=f"(1.0 - {risk_score:.2f}) × 100 × {self.WEIGHT_RISK_RESILIENCE:.2f} = {rsk_contrib:.2f} pts" if not rsk_is_gap else "DATA_GAP"
        )
        provenance.append({
            "dimension": "RISK_RESILIENCE",
            "score": round(resilience_val, 1) if not rsk_is_gap else None,
            "weight": self.WEIGHT_RISK_RESILIENCE,
            "weighted_contribution": round(rsk_contrib, 2),
            "status": rsk_status,
            "source": "Stage 11 Enterprise Risk Engine" if not rsk_is_gap else "DATA_GAP",
            "calculation": rsk_calc
        })

        # Calculate composite synthesis score
        composite_score = mkt_contrib + fin_contrib + ent_contrib + rsk_contrib
        composite_score = round(max(0.0, min(100.0, composite_score)), 1)

        # Average confidence across available pillars
        active_confs = [c for c in [mkt_conf, fin_conf, ent_conf, risk_conf] if c > 0]
        overall_confidence = round(sum(active_confs) / len(active_confs), 2) if active_confs else 0.0

        # -------------------------------------------------------------------
        # 5. Critical Gate Impact & Final Decision Determination
        # -------------------------------------------------------------------
        has_restrict_gate = any(g.status == "RESTRICT" for g in critical_gates)
        has_caution_gate = any(g.status == "CAUTION" for g in critical_gates)
        restrict_reasons = [g.explanation for g in critical_gates if g.status == "RESTRICT"]

        # Check data completeness: if any core pillar is a DATA_GAP, do NOT issue a unvalidated YES
        has_data_gap = mkt_is_gap or fin_is_gap or ent_is_gap or rsk_is_gap
        raw_stages = feature_vector.raw_vector_summary.get("stages_hydrated", {})
        if sum(raw_stages.values()) < 3 or overall_confidence < 0.50 or has_data_gap:
            is_data_insufficient = True
        else:
            is_data_insufficient = False

        if is_data_insufficient:
            decision = "DATA_INSUFFICIENT"
            recommendation = "NEEDS_VALIDATION"
        elif has_restrict_gate:
            decision = "NOT_FEASIBLE"
            recommendation = "NO"
            composite_score = min(composite_score, 38.0)
        elif composite_score >= 75.0 and not has_caution_gate:
            decision = "VIABLE"
            recommendation = "YES"
        elif composite_score >= 55.0 or has_caution_gate:
            decision = "VIABLE_WITH_CAUTION"
            recommendation = "YES"
        elif composite_score >= 40.0:
            decision = "CONDITIONALLY_VIABLE"
            recommendation = "CONDITIONAL"
        else:
            decision = "NOT_FEASIBLE"
            recommendation = "NO"

        provenance.append({
            "dimension": "FINAL_SYNTHESIS_DECISION",
            "score": composite_score if not is_data_insufficient else None,
            "decision": decision,
            "recommendation": recommendation,
            "source": "KALPA Stage 12 Synthesis Matrix",
            "calculation": f"Sum(Pillars) = {mkt_contrib:.1f} + {fin_contrib:.1f} + {ent_contrib:.1f} + {rsk_contrib:.1f} = {composite_score:.1f}/100. Gates: {'RESTRICTED' if has_restrict_gate else ('CAUTION' if has_caution_gate else 'CLEARED')}. Completeness: {'INCOMPLETE' if is_data_insufficient else 'VALIDATED'}."
        })

        # -------------------------------------------------------------------
        # 6. Positive Drivers, Key Constraints & Conditions
        # -------------------------------------------------------------------
        positive_drivers: List[Dict[str, Any]] = []
        key_constraints: List[Dict[str, Any]] = []
        conditions: List[Dict[str, Any]] = []

        # Positive drivers
        if mkt_val >= 65.0:
            positive_drivers.append({
                "factor": "Strong Market Demand & Opportunity",
                "evidence": f"Stage 8 Opportunity Score of {mkt_val:.0f}/100 indicates robust local demand density.",
                "source": "STAGE_8_OPPORTUNITY"
            })
        if dscr_val >= 1.35:
            positive_drivers.append({
                "factor": "Healthy Debt Service Coverage",
                "evidence": f"Projected DSCR of {dscr_val:.2f}x exceeds statutory 1.35x benchmark.",
                "source": "STAGE_9_FINANCIAL"
            })
        if ent_val >= 65.0:
            positive_drivers.append({
                "factor": "Relevant Operating Experience & Capability",
                "evidence": f"Founder readiness evaluated at {ent_val:.0f}/100 with demonstrated domain capability.",
                "source": "STAGE_10_ENTREPRENEUR"
            })
        if resilience_val >= 65.0:
            positive_drivers.append({
                "factor": "Low Multi-Vector Risk Exposure",
                "evidence": f"Enterprise risk severity is {feature_vector.overall_risk_severity.value} ({risk_score:.2f}).",
                "source": "STAGE_11_RISK"
            })

        # Key constraints
        if dscr_val < 1.35:
            key_constraints.append({
                "constraint": "Narrow Debt Repayment Buffer",
                "severity": "CRITICAL" if dscr_val < 1.15 else "HIGH",
                "explanation": f"DSCR of {dscr_val:.2f}x requires disciplined monthly cash flow management.",
                "required_action": "Maintain 3 months of EMI cash reserves and consider higher promoter margin."
            })
        if float(feature_vector.competition_risk.value or 0) >= 0.50:
            key_constraints.append({
                "constraint": "Local Competitor Cluster Pressure",
                "severity": "MEDIUM",
                "explanation": "Multiple direct competitors operate within the immediate trade radius.",
                "required_action": "Differentiate product mix, offer value-added customer service, or optimize pricing."
            })
        if float(feature_vector.training_score.value or 0) < 60.0:
            key_constraints.append({
                "constraint": "Domain Statutory / Skill Training Gap",
                "severity": "MEDIUM",
                "explanation": "Formal domain certification or business bookkeeping training is missing.",
                "required_action": "Complete recommended RSETI / PMKVY / FoSTaC training module before operational launch."
            })
        if has_restrict_gate:
            for r in restrict_reasons:
                key_constraints.append({
                    "constraint": "Critical Hard Constraint Violation",
                    "severity": "CRITICAL",
                    "explanation": r,
                    "required_action": "Address foundational constraint or explore Pivot Advisor alternative business options."
                })

        # Conditions
        conditions.append({
            "condition_id": "COND_01",
            "title": "Maintain Minimum Working Capital Reserve",
            "requirement": "Retain at least 15% of project cost as contingency liquidity prior to commercial kickoff.",
            "status": "MANDATORY"
        })
        if float(feature_vector.training_score.value or 0) < 70.0:
            conditions.append({
                "condition_id": "COND_02",
                "title": "Complete Statutory Domain Training",
                "requirement": "Enroll in verified institutional support program prior to loan disbursement.",
                "status": "MANDATORY"
            })
        if float(feature_vector.seasonal_risk.value or 0) >= 0.40:
            conditions.append({
                "condition_id": "COND_03",
                "title": "Seasonal Volatility Buffer",
                "requirement": "Establish off-season product bundling or alternative inventory line to hedge against lean months.",
                "status": "RECOMMENDED"
            })

        pillar_scores_dict = {
            "market_opportunity": pillar_market,
            "financial_viability": pillar_finance,
            "entrepreneur_readiness": pillar_entrepreneur,
            "risk_resilience": pillar_risk
        }

        missing_upstream = [f"STAGE_{k.replace('stage', '')}" for k, v in raw_stages.items() if not v]
        data_completeness = {
            "stages_evaluated": raw_stages,
            "missing_upstream": missing_upstream,
            "missing": missing_upstream,
            "complete": len(missing_upstream) == 0,
            "evidence_quality_score": feature_vector.evidence_quality_score,
            "data_gaps_count": sum(1 for p in [pillar_market, pillar_finance, pillar_entrepreneur, pillar_risk] if p.status == "DATA_GAP"),
            "is_authoritative": not is_data_insufficient
        }


        return (
            composite_score,
            decision,
            recommendation,
            overall_confidence,
            pillar_scores_dict,
            positive_drivers,
            key_constraints,
            conditions,
            provenance,
            data_completeness
        )


feasibility_synthesis_engine = FeasibilitySynthesisEngine()
