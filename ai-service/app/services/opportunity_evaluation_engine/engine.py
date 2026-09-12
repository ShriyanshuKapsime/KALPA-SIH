"""
Stage 8: Deterministic Opportunity Evaluation Engine.
Evaluates the core question: "Does this business have a market opportunity at this location?"
Combines Demand, Competition Opportunity, Infrastructure, Supply Ecosystem, Market Access,
and Market Capacity with zero LLM calculations, strict fallback handling, and full audit provenance.
"""
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple

from app.schemas.opportunity_evaluation import (
    OpportunityLevel,
    DemandSourceType,
    ConstraintSeverity,
    DemandScoreDetail,
    CompetitionOpportunityDetail,
    InfrastructureOpportunityDetail,
    SupplyOpportunityDetail,
    MarketAccessOpportunityDetail,
    MarketCapacityOpportunityDetail,
    OpportunityComponentScores,
    DemandSourceMetadata,
    OpportunityConstraint,
    OpportunityCalculationRecord,
    OpportunityProvenance,
    Stage8WorkflowState,
    OpportunityEvidenceQuality,
    Stage8NextStageContract,
    Stage8ExecutionMetadata,
    OpportunityResult,
    OpportunityEvaluationResponse
)
from app.services.opportunity_evaluation_engine.constants import (
    OPPORTUNITY_WEIGHTS,
    SUPPLY_WEIGHTS,
    OPPORTUNITY_LEVEL_THRESHOLDS,
    DEMAND_SIGNAL_THRESHOLDS,
    CONSTRAINT_PENALTIES,
    POSITIVE_FACTOR_TEMPLATES,
    NEGATIVE_FACTOR_TEMPLATES
)
from app.core.logging import logger


def _clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, round(float(val), 4)))


class OpportunityEvaluationEngine:
    """
    Deterministic Market Opportunity Evaluation Engine (Stage 8).
    Auditable, benchmark-aware, and reproducible without LLMs.
    """

    def __init__(self):
        self.weights = OPPORTUNITY_WEIGHTS
        self.version = "1.0.0"

    def evaluate(self, payload: Dict[str, Any]) -> OpportunityEvaluationResponse:
        """
        Main entry point for Stage 8 Opportunity Evaluation.
        Accepts Stage 6 output directly or within an envelope, executes the 8-step pipeline,
        and returns an explainable OpportunityEvaluationResponse.
        """
        start_time = time.time()
        logger.info("[STAGE 8 ENGINE] Starting deterministic Opportunity Evaluation")

        # ---------------------------------------------------------------------
        # STEP 1: Input Validation & Normalization
        # ---------------------------------------------------------------------
        normalized = self._normalize_input(payload)
        analysis_id = normalized["analysis_id"]
        session_id = normalized["session_id"]
        biz_context = normalized["business_context"]
        loc_context = normalized["location_context"]
        indicators = normalized["indicators"]
        evidence_quality = normalized["evidence_quality"]
        data_gaps = normalized["data_gaps"]
        step_records: List[OpportunityCalculationRecord] = []

        # ---------------------------------------------------------------------
        # STEP 2: Resolve Demand Signal (Stage 7 ML -> Stage 6 Deterministic -> Fallback)
        # ---------------------------------------------------------------------
        demand_detail, demand_meta, demand_step = self._resolve_demand_signal(
            normalized.get("demand_prediction"),
            indicators.get("demand_evidence", {})
        )
        step_records.append(demand_step)

        # ---------------------------------------------------------------------
        # STEP 3: Component Scoring
        # ---------------------------------------------------------------------
        # 3a. Competition Opportunity
        comp_detail, comp_step = self._score_competition(indicators.get("competition", {}))
        step_records.append(comp_step)

        # 3b. Infrastructure Opportunity
        infra_detail, infra_step = self._score_infrastructure(indicators.get("infrastructure", {}))
        step_records.append(infra_step)

        # 3c. Supply Opportunity
        supply_detail, supply_step = self._score_supply(indicators.get("supply_ecosystem", {}))
        step_records.append(supply_step)

        # 3d. Market Access
        access_detail, access_step = self._score_market_access(indicators.get("market_access", {}))
        step_records.append(access_step)

        # 3e. Market Capacity
        capacity_detail, capacity_step = self._score_market_capacity(indicators.get("market_capacity", {}))
        step_records.append(capacity_step)

        component_scores = OpportunityComponentScores(
            demand=demand_detail,
            competition_opportunity=comp_detail,
            infrastructure=infra_detail,
            supply_ecosystem=supply_detail,
            market_access=access_detail,
            market_capacity=capacity_detail
        )

        # ---------------------------------------------------------------------
        # STEP 4: Critical Market Constraints Evaluation
        # ---------------------------------------------------------------------
        constraints, constraint_adjustments, level_override_target, override_reason = self._evaluate_constraints(
            demand_detail=demand_detail,
            comp_detail=comp_detail,
            infra_detail=infra_detail,
            supply_detail=supply_detail,
            capacity_detail=capacity_detail,
            indicators=indicators
        )

        # ---------------------------------------------------------------------
        # STEP 5: Opportunity Synthesis & Classification
        # ---------------------------------------------------------------------
        raw_opp_score, final_opp_score, opp_level, level_override, synth_step = self._synthesize_opportunity(
            component_scores=component_scores,
            constraint_adjustments=constraint_adjustments,
            level_override_target=level_override_target,
            override_reason=override_reason
        )
        step_records.append(synth_step)

        # ---------------------------------------------------------------------
        # STEP 6: Positive & Negative Factors
        # ---------------------------------------------------------------------
        positive_factors, negative_factors = self._generate_factors(
            component_scores=component_scores,
            indicators=indicators,
            proxy_dependency=evidence_quality.get("proxy_dependency", 0.0)
        )

        # ---------------------------------------------------------------------
        # STEP 7: Confidence Calculation
        # ---------------------------------------------------------------------
        opp_confidence, conf_step = self._calculate_confidence(
            component_scores=component_scores,
            evidence_quality=evidence_quality,
            demand_meta=demand_meta,
            data_gaps=data_gaps
        )
        step_records.append(conf_step)

        # ---------------------------------------------------------------------
        # STEP 8: Assemble Provenance and Response
        # ---------------------------------------------------------------------
        provenance = OpportunityProvenance(
            formula=(
                f"{self.weights['demand']} * demand + {self.weights['competition']} * comp_opp + "
                f"{self.weights['infrastructure']} * infra + {self.weights['supply']} * supply + "
                f"{self.weights['market_access']} * market_access + {self.weights['market_capacity']} * market_capacity"
            ),
            weights=self.weights,
            component_scores={
                "demand": demand_detail.score,
                "competition_opportunity": comp_detail.score,
                "infrastructure": infra_detail.score,
                "supply_ecosystem": supply_detail.score,
                "market_access": access_detail.score,
                "market_capacity": capacity_detail.score
            },
            constraint_adjustments=constraint_adjustments,
            final_score=final_opp_score,
            classification_method="deterministic_thresholds",
            level_override=level_override,
            override_reason=override_reason if level_override else None,
            step_records=step_records
        )

        opportunity_result = OpportunityResult(
            market_opportunity_score=final_opp_score,
            level=opp_level,
            demand_source=demand_meta,
            component_scores=component_scores,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            constraints=constraints,
            confidence=opp_confidence,
            level_override=level_override,
            override_reason=override_reason if level_override else None
        )

        exec_time = round(time.time() - start_time, 4)

        return OpportunityEvaluationResponse(
            schema_version="1.0",
            analysis_id=analysis_id,
            session_id=session_id,
            workflow=Stage8WorkflowState(
                stage=8,
                state="MARKET_OPPORTUNITY_EVALUATED",
                status="complete" if not constraints else "complete_with_constraints"
            ),
            business_context=biz_context,
            location_context=loc_context,
            opportunity_result=opportunity_result,
            evidence_quality=OpportunityEvidenceQuality(
                overall_confidence=opp_confidence,
                proxy_dependency=_clamp(evidence_quality.get("proxy_dependency", 0.0)),
                data_gaps=data_gaps
            ),
            calculation_provenance=provenance,
            next_stage=Stage8NextStageContract(
                stage=None,
                component="FEASIBILITY_ENGINE",
                input_contract="opportunity_result"
            ),
            execution_metadata=Stage8ExecutionMetadata(
                engine="deterministic_opportunity_evaluation_engine",
                engine_version=self.version,
                llm_used=False,
                stage_7_ml_used=demand_meta.stage_7_available,
                demand_fallback_used=demand_meta.fallback_used,
                status="SUCCESS",
                execution_time_seconds=exec_time
            )
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _normalize_input(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes direct Stage 6 output, wrapped request envelopes, or raw dicts."""
        analysis_id = payload.get("analysis_id") or str(uuid.uuid4())
        session_id = payload.get("session_id") or str(uuid.uuid4())

        # Check for market intelligence inside subfield or at root
        market_intel = payload.get("market_intelligence")
        if market_intel and isinstance(market_intel, dict):
            source_dict = market_intel
            biz_context = payload.get("business_context") or source_dict.get("business_context", {})
            loc_context = payload.get("location_context") or source_dict.get("location_context", {})
            demand_pred = payload.get("demand_prediction") or source_dict.get("demand_prediction")
        else:
            source_dict = payload
            biz_context = payload.get("business_context", {})
            loc_context = payload.get("location_context", {})
            demand_pred = payload.get("demand_prediction")

        indicators = source_dict.get("market_indicators", {})
        evidence_quality = source_dict.get("evidence_quality", {})
        data_gaps = source_dict.get("evidence_gaps", [])

        return {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "business_context": biz_context,
            "location_context": loc_context,
            "indicators": indicators,
            "evidence_quality": evidence_quality,
            "data_gaps": data_gaps,
            "demand_prediction": demand_pred
        }

    def _resolve_demand_signal(
        self,
        demand_prediction: Optional[Dict[str, Any]],
        stage6_demand: Dict[str, Any]
    ) -> Tuple[DemandScoreDetail, DemandSourceMetadata, OpportunityCalculationRecord]:
        """
        Resolves demand signal through 3-tier priority abstraction:
        1. Stage 7 ML prediction (if available)
        2. Stage 6 deterministic demand evidence
        3. Neutral fallback with evidence gap
        """
        # CASE A: Stage 7 ML prediction available
        if demand_prediction and isinstance(demand_prediction, dict):
            ml_score = demand_prediction.get("demand_index")
            if ml_score is None:
                ml_score = demand_prediction.get("score")
            if ml_score is not None:
                score = _clamp(ml_score)
                conf = _clamp(demand_prediction.get("confidence", 0.70))
                level = str(demand_prediction.get("level", "MODERATE")).upper()
                detail = DemandScoreDetail(
                    score=score,
                    confidence=conf,
                    source=DemandSourceType.STAGE_7_ML.value,
                    level=level,
                    fallback_used=False
                )
                meta = DemandSourceMetadata(
                    type=DemandSourceType.STAGE_7_ML,
                    stage_7_available=True,
                    fallback_used=False,
                    confidence=conf,
                    details=demand_prediction
                )
                record = OpportunityCalculationRecord(
                    indicator="demand_score",
                    formula="demand_prediction.demand_index (Stage 7 ML Model)",
                    inputs={"demand_prediction": demand_prediction},
                    intermediate_steps=[f"Ingested Stage 7 ML predictive proxy signal with score={score}, level={level}"],
                    output_value=score,
                    confidence=conf
                )
                return detail, meta, record

        # CASE B: Stage 6 Deterministic Demand Evidence (Default MVP Mode)
        if stage6_demand and ("demand_signal_score" in stage6_demand or "demand_signal_strength" in stage6_demand):
            score = _clamp(stage6_demand.get("demand_signal_score", 0.50))
            conf = _clamp(stage6_demand.get("confidence", 0.85))
            raw_strength = stage6_demand.get("demand_signal_strength")
            if raw_strength:
                level = str(raw_strength).upper()
            else:
                if score >= DEMAND_SIGNAL_THRESHOLDS["HIGH"]:
                    level = "HIGH"
                elif score >= DEMAND_SIGNAL_THRESHOLDS["MODERATE"]:
                    level = "MODERATE"
                else:
                    level = "LOW"

            detail = DemandScoreDetail(
                score=score,
                confidence=conf,
                source=DemandSourceType.STAGE_6_DETERMINISTIC_EVIDENCE.value,
                level=level,
                fallback_used=True
            )
            meta = DemandSourceMetadata(
                type=DemandSourceType.STAGE_6_DETERMINISTIC_EVIDENCE,
                stage_7_available=False,
                fallback_used=True,
                confidence=conf,
                details={"stage_6_signal_strength": level, "data_coverage": stage6_demand.get("data_coverage", 1.0)}
            )
            record = OpportunityCalculationRecord(
                indicator="demand_score",
                formula="market_indicators.demand_evidence.demand_signal_score (Stage 6 Deterministic Evidence)",
                inputs={"stage6_demand_signal_score": score, "stage6_confidence": conf},
                intermediate_steps=[
                    "Stage 7 ML not provided. Gracefully falling back to Stage 6 deterministic demand synthesis.",
                    f"Normalized Stage 6 demand score to {score} (level={level}, confidence={conf})"
                ],
                output_value=score,
                confidence=conf
            )
            return detail, meta, record

        # CASE C: Demand Data Missing -> Neutral Fallback
        neutral_score = 0.50
        neutral_conf = 0.30
        detail = DemandScoreDetail(
            score=neutral_score,
            confidence=neutral_conf,
            source=DemandSourceType.UNAVAILABLE.value,
            level="MODERATE",
            fallback_used=True
        )
        meta = DemandSourceMetadata(
            type=DemandSourceType.UNAVAILABLE,
            stage_7_available=False,
            fallback_used=True,
            confidence=neutral_conf,
            details={"status": "UNKNOWN_DATA_GAP", "note": "Zero demand indicators found"}
        )
        record = OpportunityCalculationRecord(
            indicator="demand_score",
            formula="Neutral fallback value (0.50) due to missing demand evidence",
            inputs={"stage6_demand": stage6_demand},
            intermediate_steps=[
                "Demand data unavailable from Stage 6 or Stage 7.",
                "Applied neutral demand score 0.50 with confidence penalty to prevent fabricated demand."
            ],
            output_value=neutral_score,
            confidence=neutral_conf
        )
        return detail, meta, record

    def _score_competition(self, comp: Dict[str, Any]) -> Tuple[CompetitionOpportunityDetail, OpportunityCalculationRecord]:
        """Competition Opportunity Score = 1 - competitive_pressure_score."""
        pressure_score = _clamp(comp.get("competitive_pressure_score", 0.0))
        comp_opp_score = _clamp(1.0 - pressure_score)
        conf = _clamp(comp.get("confidence", 0.85))
        pressure_level = str(comp.get("competitive_pressure", "LOW")).upper()
        direct_count = comp.get("direct", {}).get("count", 0) if isinstance(comp.get("direct"), dict) else 0

        detail = CompetitionOpportunityDetail(
            score=comp_opp_score,
            confidence=conf,
            pressure_score=pressure_score,
            pressure_level=pressure_level,
            direct_competitors=direct_count
        )
        record = OpportunityCalculationRecord(
            indicator="competition_opportunity_score",
            formula="clamp(1.0 - competitive_pressure_score)",
            inputs={"competitive_pressure_score": pressure_score, "pressure_level": pressure_level},
            intermediate_steps=[f"1.0 - {pressure_score} = {comp_opp_score}"],
            output_value=comp_opp_score,
            confidence=conf
        )
        return detail, record

    def _score_infrastructure(self, infra: Dict[str, Any]) -> Tuple[InfrastructureOpportunityDetail, OpportunityCalculationRecord]:
        """Infrastructure Opportunity Score = max(0, readiness_score - critical_gap_penalty)."""
        readiness_score = _clamp(infra.get("readiness_score", 1.0))
        readiness_str = str(infra.get("readiness", "AVAILABLE")).upper()
        critical_gaps = infra.get("critical_gaps", [])
        gap_count = len(critical_gaps) if isinstance(critical_gaps, list) else 0
        gap_penalty = round(min(0.50, gap_count * CONSTRAINT_PENALTIES["CRITICAL_GAP_PENALTY_PER_ITEM"]), 4)

        final_infra_score = _clamp(max(0.0, readiness_score - gap_penalty))
        conf = _clamp(infra.get("confidence", 0.85))

        detail = InfrastructureOpportunityDetail(
            score=final_infra_score,
            confidence=conf,
            readiness=readiness_str,
            readiness_score=readiness_score,
            critical_gaps_count=gap_count,
            gap_penalty=gap_penalty
        )
        record = OpportunityCalculationRecord(
            indicator="infrastructure_score",
            formula="clamp(readiness_score - (critical_gaps_count * 0.10))",
            inputs={"readiness_score": readiness_score, "critical_gaps_count": gap_count, "gap_penalty": gap_penalty},
            intermediate_steps=[f"{readiness_score} - {gap_penalty} = {final_infra_score}"],
            output_value=final_infra_score,
            confidence=conf
        )
        return detail, record

    def _score_supply(self, supply: Dict[str, Any]) -> Tuple[SupplyOpportunityDetail, OpportunityCalculationRecord]:
        """Supply Opportunity Score = 0.60 * (1 - supply_risk_score) + 0.40 * critical_input_coverage_ratio."""
        risk_score = _clamp(supply.get("supply_risk_score", 0.0))
        cov_dict = supply.get("critical_input_coverage", {})
        if isinstance(cov_dict, dict) and "coverage_ratio" in cov_dict:
            coverage_ratio = _clamp(cov_dict.get("coverage_ratio", 1.0))
        elif isinstance(cov_dict, (int, float)):
            coverage_ratio = _clamp(cov_dict)
        else:
            coverage_ratio = 1.0

        w_risk = SUPPLY_WEIGHTS["risk_complement"]
        w_cov = SUPPLY_WEIGHTS["input_coverage"]
        supply_score = _clamp(w_risk * (1.0 - risk_score) + w_cov * coverage_ratio)
        conf = _clamp(supply.get("confidence", 0.80))
        accessibility = str(supply.get("accessibility", "HIGH")).upper()

        detail = SupplyOpportunityDetail(
            score=supply_score,
            confidence=conf,
            risk_score=risk_score,
            input_coverage_ratio=coverage_ratio,
            accessibility=accessibility
        )
        record = OpportunityCalculationRecord(
            indicator="supply_score",
            formula=f"{w_risk} * (1.0 - supply_risk_score) + {w_cov} * critical_input_coverage_ratio",
            inputs={"supply_risk_score": risk_score, "critical_input_coverage_ratio": coverage_ratio},
            intermediate_steps=[
                f"{w_risk} * (1.0 - {risk_score}) = {round(w_risk * (1.0 - risk_score), 4)}",
                f"{w_cov} * {coverage_ratio} = {round(w_cov * coverage_ratio, 4)}",
                f"Sum = {supply_score}"
            ],
            output_value=supply_score,
            confidence=conf
        )
        return detail, record

    def _score_market_access(self, access: Dict[str, Any]) -> Tuple[MarketAccessOpportunityDetail, OpportunityCalculationRecord]:
        """Market Access Score = geographic_accessibility_score."""
        geo_score = _clamp(access.get("geographic_accessibility_score", 0.80))
        conf = _clamp(access.get("confidence", 0.80))
        accessibility = str(access.get("accessibility", "HIGH")).upper()

        detail = MarketAccessOpportunityDetail(
            score=geo_score,
            confidence=conf,
            geographic_accessibility_score=geo_score,
            accessibility=accessibility
        )
        record = OpportunityCalculationRecord(
            indicator="market_access_score",
            formula="geographic_accessibility_score",
            inputs={"geographic_accessibility_score": geo_score},
            intermediate_steps=[f"Direct geographic accessibility score = {geo_score}"],
            output_value=geo_score,
            confidence=conf
        )
        return detail, record

    def _score_market_capacity(self, cap: Dict[str, Any]) -> Tuple[MarketCapacityOpportunityDetail, OpportunityCalculationRecord]:
        """Market Capacity Score = net_capacity_score."""
        net_cap = _clamp(cap.get("net_capacity_score", 0.70))
        conf = _clamp(cap.get("confidence", 0.70))
        status = str(cap.get("status", "AVAILABLE")).upper()
        signal = str(cap.get("capacity_signal", "EXPANSION_CAPACITY")).upper()

        detail = MarketCapacityOpportunityDetail(
            score=net_cap,
            confidence=conf,
            net_capacity_score=net_cap,
            status=status,
            capacity_signal=signal
        )
        record = OpportunityCalculationRecord(
            indicator="market_capacity_score",
            formula="market_indicators.market_capacity.net_capacity_score",
            inputs={"net_capacity_score": net_cap, "status": status},
            intermediate_steps=[f"Direct net market capacity score = {net_cap} (status={status})"],
            output_value=net_cap,
            confidence=conf
        )
        return detail, record

    def _evaluate_constraints(
        self,
        demand_detail: DemandScoreDetail,
        comp_detail: CompetitionOpportunityDetail,
        infra_detail: InfrastructureOpportunityDetail,
        supply_detail: SupplyOpportunityDetail,
        capacity_detail: MarketCapacityOpportunityDetail,
        indicators: Dict[str, Any]
    ) -> Tuple[List[OpportunityConstraint], List[Dict[str, Any]], Optional[OpportunityLevel], Optional[str]]:
        """
        Evaluates critical constraints before final opportunity scoring:
        1. Market Saturation
        2. Critical Infrastructure Failure
        3. Extreme Supply Failure
        4. Severe Competitive Pressure
        5. High Seasonality Volatility
        """
        constraints: List[OpportunityConstraint] = []
        adjustments: List[Dict[str, Any]] = []
        level_override: Optional[OpportunityLevel] = None
        override_reason: Optional[str] = None

        # 1. Market Saturation Constraint
        if capacity_detail.status == "SATURATED" or capacity_detail.score < CONSTRAINT_PENALTIES["MARKET_SATURATION_SCORE_THRESHOLD"]:
            penalty = 0.20
            constraints.append(OpportunityConstraint(
                constraint_id="MARKET_SATURATION",
                severity=ConstraintSeverity.CRITICAL if capacity_detail.status == "SATURATED" else ConstraintSeverity.HIGH,
                component="market_capacity",
                description="Available market capacity is insufficient for additional similar businesses in this catchment.",
                blocking=True,
                score_impact=-penalty
            ))
            adjustments.append({
                "constraint": "MARKET_SATURATION",
                "penalty": penalty,
                "reason": f"Capacity status is {capacity_detail.status} with net capacity score {capacity_detail.score}"
            })
            level_override = OpportunityLevel.LIMITED_OPPORTUNITY
            override_reason = "Critical market saturation caps opportunity level to LIMITED_OPPORTUNITY regardless of demand evidence."

        # 2. Critical Infrastructure Failure Constraint
        if infra_detail.critical_gaps_count >= 2 or (infra_detail.readiness == "UNAVAILABLE" and infra_detail.readiness_score < 0.20):
            penalty = 0.15
            constraints.append(OpportunityConstraint(
                constraint_id="CRITICAL_INFRASTRUCTURE_FAILURE",
                severity=ConstraintSeverity.HIGH,
                component="infrastructure",
                description=f"Multiple unresolved critical infrastructure gaps ({infra_detail.critical_gaps_count}) restrict operational viability.",
                blocking=True,
                score_impact=-penalty
            ))
            adjustments.append({
                "constraint": "CRITICAL_INFRASTRUCTURE_FAILURE",
                "penalty": penalty,
                "reason": f"{infra_detail.critical_gaps_count} critical infrastructure gaps detected"
            })
            if not level_override or level_override == OpportunityLevel.HIGH_OPPORTUNITY:
                level_override = OpportunityLevel.LIMITED_OPPORTUNITY
                override_reason = "Critical infrastructure failure restricts opportunity tier."

        # 3. Extreme Supply Failure Constraint
        if supply_detail.input_coverage_ratio < 0.40 and supply_detail.risk_score > 0.70:
            penalty = CONSTRAINT_PENALTIES["EXTREME_SUPPLY_FAILURE_PENALTY"]
            constraints.append(OpportunityConstraint(
                constraint_id="EXTREME_SUPPLY_FAILURE",
                severity=ConstraintSeverity.HIGH,
                component="supply_ecosystem",
                description="Severe supply chain procurement deficit (< 40% input coverage) combined with high supply risk.",
                blocking=False,
                score_impact=-penalty
            ))
            adjustments.append({
                "constraint": "EXTREME_SUPPLY_FAILURE",
                "penalty": penalty,
                "reason": f"Input coverage {supply_detail.input_coverage_ratio} and supply risk {supply_detail.risk_score}"
            })

        # 4. Severe Competitive Pressure Constraint
        if comp_detail.pressure_score >= 0.80 and capacity_detail.score < 0.50:
            penalty = CONSTRAINT_PENALTIES["SEVERE_COMPETITION_PENALTY"]
            constraints.append(OpportunityConstraint(
                constraint_id="SEVERE_COMPETITIVE_PRESSURE",
                severity=ConstraintSeverity.HIGH,
                component="competition",
                description="Extreme competitor clustering in target catchment with constrained expansion capacity.",
                blocking=False,
                score_impact=-penalty
            ))
            adjustments.append({
                "constraint": "SEVERE_COMPETITIVE_PRESSURE",
                "penalty": penalty,
                "reason": f"Competitive pressure {comp_detail.pressure_score} with capacity score {capacity_detail.score}"
            })

        # 5. Seasonality Risk Constraint
        seasonality = indicators.get("seasonality", {})
        annual_vol = seasonality.get("annual_volatility", 0.0)
        seasonal_risk = str(seasonality.get("seasonal_risk", "LOW")).upper()
        if annual_vol > 0.40 or seasonal_risk == "HIGH":
            constraints.append(OpportunityConstraint(
                constraint_id="HIGH_SEASONALITY_VOLATILITY",
                severity=ConstraintSeverity.MODERATE,
                component="seasonality",
                description="High seasonal demand swings require significant working capital buffers.",
                blocking=False,
                score_impact=0.0
            ))

        return constraints, adjustments, level_override, override_reason

    def _synthesize_opportunity(
        self,
        component_scores: OpportunityComponentScores,
        constraint_adjustments: List[Dict[str, Any]],
        level_override_target: Optional[OpportunityLevel],
        override_reason: Optional[str]
    ) -> Tuple[float, float, OpportunityLevel, bool, OpportunityCalculationRecord]:
        """Calculates weighted baseline opportunity score, applies penalty adjustments, and assigns level."""
        w = self.weights
        c = component_scores

        raw_score = (
            w["demand"] * c.demand.score +
            w["competition"] * c.competition_opportunity.score +
            w["infrastructure"] * c.infrastructure.score +
            w["supply"] * c.supply_ecosystem.score +
            w["market_access"] * c.market_access.score +
            w["market_capacity"] * c.market_capacity.score
        )
        raw_score = round(raw_score, 4)

        # Sum penalty adjustments
        total_penalty = sum(adj.get("penalty", 0.0) for adj in constraint_adjustments)
        adjusted_score = _clamp(raw_score - total_penalty)

        # Map to deterministic level
        if adjusted_score >= OPPORTUNITY_LEVEL_THRESHOLDS["HIGH"]:
            normal_level = OpportunityLevel.HIGH_OPPORTUNITY
        elif adjusted_score >= OPPORTUNITY_LEVEL_THRESHOLDS["MODERATE"]:
            normal_level = OpportunityLevel.MODERATE_OPPORTUNITY
        elif adjusted_score >= OPPORTUNITY_LEVEL_THRESHOLDS["LIMITED"]:
            normal_level = OpportunityLevel.LIMITED_OPPORTUNITY
        else:
            normal_level = OpportunityLevel.LOW_OPPORTUNITY

        # Apply level override if critical constraint blocks high classification
        level_override_applied = False
        final_level = normal_level

        if level_override_target is not None:
            # If normal level is higher than the override cap, cap it
            hierarchy = [
                OpportunityLevel.LOW_OPPORTUNITY,
                OpportunityLevel.LIMITED_OPPORTUNITY,
                OpportunityLevel.MODERATE_OPPORTUNITY,
                OpportunityLevel.HIGH_OPPORTUNITY
            ]
            if hierarchy.index(normal_level) > hierarchy.index(level_override_target):
                final_level = level_override_target
                level_override_applied = True

        record = OpportunityCalculationRecord(
            indicator="market_opportunity_score",
            formula=(
                f"{w['demand']} * demand ({c.demand.score}) + "
                f"{w['competition']} * comp_opp ({c.competition_opportunity.score}) + "
                f"{w['infrastructure']} * infra ({c.infrastructure.score}) + "
                f"{w['supply']} * supply ({c.supply_ecosystem.score}) + "
                f"{w['market_access']} * access ({c.market_access.score}) + "
                f"{w['market_capacity']} * capacity ({c.market_capacity.score})"
            ),
            inputs={
                "weights": w,
                "scores": {
                    "demand": c.demand.score,
                    "competition_opportunity": c.competition_opportunity.score,
                    "infrastructure": c.infrastructure.score,
                    "supply_ecosystem": c.supply_ecosystem.score,
                    "market_access": c.market_access.score,
                    "market_capacity": c.market_capacity.score
                },
                "total_penalty": total_penalty
            },
            intermediate_steps=[
                f"Weighted Component Sum = {raw_score}",
                f"Total Constraint Penalty Adjustments = {total_penalty}",
                f"Final Adjusted Opportunity Score = {adjusted_score}",
                f"Classification Level: {final_level.value} (Level Override: {level_override_applied})"
            ],
            output_value=adjusted_score,
            confidence=0.85
        )

        return raw_score, adjusted_score, final_level, level_override_applied, record

    def _generate_factors(
        self,
        component_scores: OpportunityComponentScores,
        indicators: Dict[str, Any],
        proxy_dependency: float
    ) -> Tuple[List[str], List[str]]:
        """Generates explainable positive and negative factors deterministically (zero LLM)."""
        pos: List[str] = []
        neg: List[str] = []
        c = component_scores

        # Positive factor rules
        if c.demand.score >= 0.70:
            pos.append(POSITIVE_FACTOR_TEMPLATES["STRONG_DEMAND"])
        if c.competition_opportunity.pressure_score <= 0.30:
            pos.append(POSITIVE_FACTOR_TEMPLATES["LOW_COMPETITION"])
        if c.infrastructure.readiness_score >= 0.80 and c.infrastructure.critical_gaps_count == 0:
            pos.append(POSITIVE_FACTOR_TEMPLATES["INFRASTRUCTURE_AVAILABLE"])
        if c.market_capacity.status == "AVAILABLE" or c.market_capacity.score >= 0.70:
            pos.append(POSITIVE_FACTOR_TEMPLATES["CAPACITY_EXPANSION"])
        if c.market_access.score >= 0.70:
            pos.append(POSITIVE_FACTOR_TEMPLATES["HIGH_MARKET_ACCESS"])
        if c.supply_ecosystem.score >= 0.70:
            pos.append(POSITIVE_FACTOR_TEMPLATES["ROBUST_SUPPLY"])

        # Negative factor rules
        if c.supply_ecosystem.risk_score >= 0.40 or c.supply_ecosystem.input_coverage_ratio < 0.80:
            neg.append(POSITIVE_FACTOR_TEMPLATES.get("SUPPLY_FRICTION", NEGATIVE_FACTOR_TEMPLATES["SUPPLY_FRICTION"]))
        seasonality = indicators.get("seasonality", {})
        if seasonality.get("annual_volatility", 0.0) >= 0.25 or str(seasonality.get("seasonal_risk", "LOW")).upper() in ["MODERATE", "HIGH"]:
            neg.append(NEGATIVE_FACTOR_TEMPLATES["HIGH_SEASONALITY"])
        if c.competition_opportunity.pressure_score >= 0.50:
            neg.append(NEGATIVE_FACTOR_TEMPLATES["HIGH_COMPETITION_PRESSURE"])
        if c.infrastructure.critical_gaps_count > 0 or c.infrastructure.readiness_score < 0.60:
            neg.append(NEGATIVE_FACTOR_TEMPLATES["INFRASTRUCTURE_GAPS"])
        if c.market_capacity.status == "SATURATED" or c.market_capacity.score < 0.40:
            neg.append(NEGATIVE_FACTOR_TEMPLATES["MARKET_SATURATION"])
        if proxy_dependency >= 0.40:
            neg.append(NEGATIVE_FACTOR_TEMPLATES["PROXY_HEAVY_EVIDENCE"])

        return pos, neg

    def _calculate_confidence(
        self,
        component_scores: OpportunityComponentScores,
        evidence_quality: Dict[str, Any],
        demand_meta: DemandSourceMetadata,
        data_gaps: List[Any]
    ) -> Tuple[float, OpportunityCalculationRecord]:
        """Calculates opportunity confidence independently from score using upstream evidence confidence."""
        w = self.weights
        c = component_scores

        base_confidence = (
            w["demand"] * c.demand.confidence +
            w["competition"] * c.competition_opportunity.confidence +
            w["infrastructure"] * c.infrastructure.confidence +
            w["supply"] * c.supply_ecosystem.confidence +
            w["market_access"] * c.market_access.confidence +
            w["market_capacity"] * c.market_capacity.confidence
        )
        base_confidence = round(base_confidence, 4)

        proxy_dep = _clamp(evidence_quality.get("proxy_dependency", 0.0))
        proxy_discount = round(proxy_dep * CONSTRAINT_PENALTIES["DATA_CONFIDENCE_DISCOUNT_PROXY"], 4)

        gap_count = len(data_gaps) if isinstance(data_gaps, list) else 0
        gap_discount = round(min(0.20, gap_count * 0.02), 4)

        fallback_discount = 0.15 if demand_meta.type == DemandSourceType.UNAVAILABLE else 0.0

        final_conf = _clamp(base_confidence - proxy_discount - gap_discount - fallback_discount, low=0.10, high=0.99)

        record = OpportunityCalculationRecord(
            indicator="opportunity_confidence",
            formula="clamp(weighted_confidence - proxy_discount - gap_discount - fallback_discount)",
            inputs={
                "base_confidence": base_confidence,
                "proxy_dependency": proxy_dep,
                "proxy_discount": proxy_discount,
                "gap_count": gap_count,
                "gap_discount": gap_discount,
                "fallback_discount": fallback_discount
            },
            intermediate_steps=[
                f"Weighted Upstream Evidence Confidence = {base_confidence}",
                f"Proxy Dependency Discount = {proxy_discount}",
                f"Data Gap Discount = {gap_discount}",
                f"Fallback Discount = {fallback_discount}",
                f"Final Opportunity Confidence = {final_conf}"
            ],
            output_value=final_conf,
            confidence=final_conf
        )

        return final_conf, record


# Global singleton instance
opportunity_evaluation_engine = OpportunityEvaluationEngine()
