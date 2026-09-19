"""
Stage 12 Feasibility Engine:
Final analytical decision and venture viability synthesis component of KALPA.
Consumes structured outputs from:
- Stage 8: Opportunity Evaluation
- Stage 9: Financial Analysis
- Stage 10: Entrepreneur Profile
- Stage 11: Enterprise Risk Engine

Executes Feature Vector normalization -> ML Model Slot -> Critical Gates -> 4-Pillar Synthesis -> Dynamic SWOT / Pivot Advisor.
"""
from typing import Dict, Any, Optional
import uuid

from app.schemas.feasibility import (
    FeasibilityEvaluationRequest,
    FeasibilityAnalysisResponse
)
from app.services.feasibility_engine.feature_vector import feasibility_feature_vector_builder
from app.services.feasibility_engine.ml_adapter import feasibility_ml_adapter
from app.services.feasibility_engine.critical_gates import critical_gates_evaluator
from app.services.feasibility_engine.synthesis_engine import feasibility_synthesis_engine
from app.services.feasibility_engine.dynamic_swot import dynamic_swot_engine
from app.services.feasibility_engine.pivot_advisor import pivot_advisor_engine
from app.core.logging import logger


class FeasibilityEngine:
    """The master analytical synthesis engine for Stage 12."""

    def __init__(self):
        self.engine_name = "KALPA_FEASIBILITY_SYNTHESIS_ENGINE"
        self.version = "1.0.0"

    def evaluate_feasibility(
        self,
        request: FeasibilityEvaluationRequest,
        raw_market_evidence: Optional[Dict[str, Any]] = None
    ) -> FeasibilityAnalysisResponse:
        """
        Executes full Stage 12 feasibility assessment.
        """
        analysis_id = request.analysis_id or str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        bus_profile = request.business_profile or {}
        loc_profile = request.location_profile or {}

        # Extract names & labels
        bus_name = (
            bus_profile.get("specific_business") or
            bus_profile.get("business_name") or
            bus_profile.get("business_profile", {}).get("specific_business") or
            "Target Micro-Enterprise"
        )
        biz_id = bus_profile.get("business_id") or bus_profile.get("business_profile", {}).get("business_id")

        village = loc_profile.get("village") or bus_profile.get("location_profile", {}).get("village") or "Target Location"
        district = loc_profile.get("district") or bus_profile.get("location_profile", {}).get("district") or "District"
        state = loc_profile.get("state") or bus_profile.get("location_profile", {}).get("state") or "State"
        location_summary = f"{village}, {district}, {state}".strip(", ")

        logger.info(f"[STAGE 12 FEASIBILITY START] analysis_id={analysis_id}, business='{bus_name}', location='{location_summary}'")

        # -------------------------------------------------------------------
        # Step 1: Build Normalized Feasibility Feature Vector
        # -------------------------------------------------------------------
        feature_vector = feasibility_feature_vector_builder.build_feature_vector(
            opportunity_data=request.opportunity_result,
            financial_data=request.financial_analysis,
            entrepreneur_data=request.entrepreneur_readiness,
            risk_data=request.risk_analysis,
            market_data=raw_market_evidence
        )

        # -------------------------------------------------------------------
        # Step 2: Feasibility ML Model Slot Interface
        # -------------------------------------------------------------------
        ml_prediction_result = feasibility_ml_adapter.predict(feature_vector)

        # -------------------------------------------------------------------
        # Step 3: Layer 1 - Critical Gates Evaluation
        # -------------------------------------------------------------------
        critical_gates = critical_gates_evaluator.evaluate_gates(
            feature_vector=feature_vector,
            business_profile=bus_profile,
            risk_data=request.risk_analysis,
            entrepreneur_data=request.entrepreneur_readiness
        )

        # -------------------------------------------------------------------
        # Step 4: Layer 2 - 4-Pillar Deterministic Synthesis
        # -------------------------------------------------------------------
        (
            overall_score,
            decision,
            recommendation,
            confidence_score,
            pillar_scores,
            positive_drivers,
            key_constraints,
            conditions,
            provenance,
            data_completeness
        ) = feasibility_synthesis_engine.synthesize(
            feature_vector=feature_vector,
            critical_gates=critical_gates,
            business_title=bus_name
        )

        # -------------------------------------------------------------------
        # Step 5: Dynamic SWOT Generation (YES / Viable Pathway)
        # -------------------------------------------------------------------
        dynamic_swot = dynamic_swot_engine.generate_swot(
            feature_vector=feature_vector,
            pillar_scores=pillar_scores,
            business_title=bus_name
        )

        # -------------------------------------------------------------------
        # Step 6: Pivot Advisory (NO / Conditional Pathway)
        # -------------------------------------------------------------------
        pivot_recommendations = pivot_advisor_engine.recommend_pivots(
            feature_vector=feature_vector,
            business_profile=bus_profile,
            entrepreneur_data=request.entrepreneur_readiness
        )

        logger.info(
            f"[STAGE 12 FEASIBILITY COMPLETE] score={overall_score:.1f}, decision='{decision}', recommendation='{recommendation}', confidence={confidence_score:.2f}"
        )

        return FeasibilityAnalysisResponse(
            analysis_id=analysis_id,
            session_id=session_id,
            business_id=biz_id,
            business_name=bus_name,
            location_summary=location_summary,
            overall_feasibility_score=overall_score,
            decision=decision,
            recommendation=recommendation,
            confidence_score=confidence_score,
            ml_prediction=ml_prediction_result,
            pillar_scores=pillar_scores,
            critical_gates=critical_gates,
            positive_drivers=positive_drivers,
            key_constraints=key_constraints,
            conditions=conditions,
            dynamic_swot=dynamic_swot,
            pivot_recommendations=pivot_recommendations,
            calculation_provenance=provenance,
            data_completeness=data_completeness,
            workflow_status="FEASIBILITY_COMPLETE"
        )


feasibility_engine = FeasibilityEngine()
