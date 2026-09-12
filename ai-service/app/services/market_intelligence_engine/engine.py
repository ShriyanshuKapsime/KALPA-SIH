"""
Stage 6: Market Intelligence Engine Core Coordinator.
Transforms raw verified Stage 5 market evidence into structured market indicators,
transparent benchmark comparisons, explainable calculation provenance,
and standardized 'market_features' for Stage 7 Demand Prediction ML Model.
STRICTLY DETERMINISTIC — NO ARBITRARY LLM SCORING.
"""
import time
import uuid
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel

from app.services.market_intelligence_engine.schemas import (
    Stage5Input,
    Stage6Output,
    Stage6WorkflowState,
    MarketIndicators,
    MarketFeatures,
    BenchmarkAnalysis,
    BenchmarkComparison,
    CalculationProvenance,
    EvidenceGap,
    EvidenceQuality,
    NextStageContract,
    ExecutionMetadata,
    DataStatus
)
from app.services.market_intelligence_engine.benchmark_service import benchmark_service
from app.services.market_intelligence_engine.data_cleaning import data_cleaning_service
from app.services.market_intelligence_engine.geospatial_analysis import geospatial_service
from app.services.market_intelligence_engine.competition_analysis import competition_service
from app.services.market_intelligence_engine.demand_evidence_analysis import demand_evidence_service
from app.services.market_intelligence_engine.infrastructure_analysis import infrastructure_service
from app.services.market_intelligence_engine.supply_ecosystem_analysis import supply_ecosystem_service
from app.services.market_intelligence_engine.market_access_analysis import market_access_service
from app.services.market_intelligence_engine.seasonality_analysis import seasonality_service
from app.services.market_intelligence_engine.market_capacity_analysis import market_capacity_service
from app.services.market_intelligence_engine.feature_builder import feature_builder_service
from app.services.market_intelligence_engine.confidence_service import confidence_service
from app.core.logging import logger


class MarketIntelligenceEngine:
    def __init__(self):
        self.engine_name = "deterministic_market_intelligence_engine"
        self.version = "1.0.0"

    def analyze(self, stage5_input: Union[Stage5Input, Dict[str, Any]]) -> Stage6Output:
        """
        Executes end-to-end deterministic Stage 6 market intelligence analysis.
        """
        start_time = time.time()
        logger.info("[STAGE 6 ENGINE] Starting deterministic market intelligence analysis")

        # 1. Normalize Input Structure
        if isinstance(stage5_input, BaseModel):
            raw_data = stage5_input.model_dump()
        else:
            raw_data = dict(stage5_input)

        # Unpack nested evidence_profile if present (from API wrapper)
        if "evidence_profile" in raw_data and isinstance(raw_data["evidence_profile"], dict):
            profile_data = raw_data["evidence_profile"]
            analysis_id = raw_data.get("analysis_id") or profile_data.get("analysis_id") or str(uuid.uuid4())
            session_id = raw_data.get("session_id") or profile_data.get("session_id") or str(uuid.uuid4())
        else:
            profile_data = raw_data
            analysis_id = raw_data.get("analysis_id") or str(uuid.uuid4())
            session_id = raw_data.get("session_id") or str(uuid.uuid4())

        business_context = profile_data.get("business_context") or {}
        location_context = profile_data.get("location_context") or {}
        market_evidence = profile_data.get("market_evidence") or {}
        evidence_quality_in = profile_data.get("evidence_quality") or {}

        # 2. Resolve Business Identifier & Benchmarks
        concept = (
            business_context.get("business_id") or
            business_context.get("specific_business") or
            business_context.get("category") or
            business_context.get("business_concept") or
            "poultry_farm"
        )
        benchmarks = benchmark_service.get_benchmarks_for_business(concept)
        logger.info(f"[STAGE 6 ENGINE] Resolved benchmark profile: '{benchmarks.get('business_node_id')}' ({benchmarks.get('business_title')})")

        # 3. Clean and Validate Raw Evidence
        raw_demographics = market_evidence.get("demographics") or []
        cleaned_demographics = data_cleaning_service.clean_demographics(raw_demographics)

        raw_competitors = market_evidence.get("competitors") or {}
        cleaned_competitors = data_cleaning_service.clean_competitors(raw_competitors)

        raw_demand_indicators = market_evidence.get("demand_indicators") or []
        cleaned_demand_indicators = data_cleaning_service.clean_demand_indicators(raw_demand_indicators)

        raw_supply = market_evidence.get("supply_access") or []
        cleaned_supply = data_cleaning_service.clean_supply_access(raw_supply)

        raw_infra = market_evidence.get("infrastructure") or []
        expected_infra = benchmarks.get("infrastructure_requirements", [])
        cleaned_infra, infra_data_status = data_cleaning_service.clean_infrastructure(raw_infra, expected_infra)

        raw_seasonality = market_evidence.get("seasonality_evidence") or []

        # 4. Execute Analysis Modules Deterministically
        # Module 3: Geospatial Analysis
        geospatial_res = geospatial_service.analyze_geospatial_context(
            location_context=location_context,
            competitors=cleaned_competitors,
            supply_hubs=cleaned_supply,
            benchmarks=benchmarks
        )

        # Module 4: Competition Analysis
        demo_map = {d.metric: d.value for d in cleaned_demographics}
        competition_res = competition_service.analyze_competition(
            competitors=cleaned_competitors,
            demographics=demo_map,
            benchmarks=benchmarks
        )

        # Module 5: Demand Evidence Analysis
        demand_res = demand_evidence_service.analyze_demand_evidence(
            demographics=cleaned_demographics,
            demand_indicators=cleaned_demand_indicators,
            benchmarks=benchmarks
        )

        # Module 6: Infrastructure Analysis
        infrastructure_res = infrastructure_service.analyze_infrastructure(
            cleaned_requirements=cleaned_infra,
            data_status=infra_data_status,
            benchmarks=benchmarks
        )

        # Module 7: Supply Ecosystem Analysis
        supply_res = supply_ecosystem_service.analyze_supply_ecosystem(
            supply_hubs=cleaned_supply,
            benchmarks=benchmarks
        )

        # Module 8: Market Access Analysis
        substitutes_list = cleaned_competitors.get("substitute", [])
        market_access_res = market_access_service.analyze_market_access(
            demographics=cleaned_demographics,
            supply_hubs=cleaned_supply,
            substitutes=substitutes_list,
            benchmarks=benchmarks
        )

        # Module 9: Seasonality Analysis
        seasonality_res = seasonality_service.analyze_seasonality(
            raw_seasonality=raw_seasonality,
            benchmarks=benchmarks
        )

        # Module 10: Market Capacity Analysis
        market_capacity_res = market_capacity_service.analyze_market_capacity(
            demand_analysis=demand_res,
            competition_analysis=competition_res,
            supply_analysis=supply_res,
            benchmarks=benchmarks
        )

        # 5. Assemble Market Indicators
        market_indicators = MarketIndicators(
            geospatial_analysis=geospatial_res,
            competition=competition_res,
            demand_evidence=demand_res,
            infrastructure=infrastructure_res,
            supply_ecosystem=supply_res,
            market_access=market_access_res,
            seasonality=seasonality_res,
            market_capacity=market_capacity_res
        )

        # 6. Benchmark Comparisons & Traceability
        comparisons: List[BenchmarkComparison] = []
        benchmarks_used: List[str] = [
            benchmarks.get("provenance", {}).get("source_id", "NABARD_BENCHMARKS"),
            "CENSUS_2011_SOCIOECONOMIC",
            "MSME_UDYAM_CENSUS"
        ]

        # Population comparison
        pop_actual = demo_map.get("total_population")
        pop_bm = benchmarks.get("catchment", {}).get("target_population_min")
        if pop_actual is not None and pop_bm is not None:
            comparisons.append(
                benchmark_service.compare_metric(
                    benchmark_id="BM-DEMO-001",
                    benchmark_name="Minimum Catchment Population",
                    actual_value=pop_actual,
                    benchmark_value=pop_bm,
                    unit="persons",
                    higher_is_better=True,
                    source=benchmarks.get("provenance", {}).get("document_name")
                )
            )

        # Competition density comparison
        comp_actual = competition_res.competition_density_per_10k
        comp_bm = benchmarks.get("competition", {}).get("saturation_threshold_units_per_10k_pop")
        if comp_actual is not None and comp_bm is not None:
            comparisons.append(
                benchmark_service.compare_metric(
                    benchmark_id="BM-COMP-002",
                    benchmark_name="Competition Saturation Threshold (per 10k Pop)",
                    actual_value=comp_actual,
                    benchmark_value=comp_bm,
                    unit="units_per_10k",
                    higher_is_better=False,
                    source=benchmarks.get("provenance", {}).get("document_name")
                )
            )

        # Supply proximity comparison
        if supply_res.nearest_hub_distance_km is not None:
            supply_bm_dist = benchmarks.get("supply_access", {}).get("ideal_distance_km", 15.0)
            comparisons.append(
                benchmark_service.compare_metric(
                    benchmark_id="BM-SUPPLY-003",
                    benchmark_name="Ideal Supply Hub Distance",
                    actual_value=supply_res.nearest_hub_distance_km,
                    benchmark_value=supply_bm_dist,
                    unit="km",
                    higher_is_better=False,
                    source="AGMARKNET_MANDI_DIRECTORY"
                )
            )

        benchmark_analysis = BenchmarkAnalysis(
            benchmarks_used=benchmarks_used,
            comparisons=comparisons
        )

        # 7. Calculation Provenance Records
        calculation_provenance: List[CalculationProvenance] = [
            CalculationProvenance(
                indicator="competitive_pressure",
                value=competition_res.competitive_pressure.value,
                calculation_method="weighted_proximity_decay_density",
                formula="pressure_score = (1.0 * w_direct + 0.5 * w_adj + 0.25 * w_sub) / expected_saturation_units",
                inputs=[f"direct_count={competition_res.direct.count}", f"adjacent_count={competition_res.adjacent.count}", f"substitute_count={competition_res.substitute.count}"],
                benchmarks_used=[f"saturation_threshold={competition_res.saturation_threshold}"],
                evidence_refs=["competitor_discovery_tool_udyam"],
                assumptions=["Competitor clusters weighted with proximity decay factor"],
                confidence=competition_res.confidence
            ),
            CalculationProvenance(
                indicator="market_capacity_status",
                value=market_capacity_res.status.value,
                calculation_method="net_market_capacity_synthesis",
                formula="net_capacity_score = demand_score - (0.60 * comp_pressure_score) - (0.15 * supply_risk)",
                inputs=[f"demand_score={demand_res.demand_signal_score}", f"comp_score={competition_res.competitive_pressure_score}", f"supply_risk={supply_res.supply_risk_score}"],
                benchmarks_used=["target_population_min", "saturation_threshold_units_per_10k_pop"],
                evidence_refs=["census_pca_2011", "udyam_clusters", "agmarknet_mandi"],
                assumptions=["Net capacity is bounded by localized purchasing power and competitive density"],
                confidence=market_capacity_res.confidence
            ),
            CalculationProvenance(
                indicator="annual_seasonal_volatility",
                value=seasonality_res.annual_volatility,
                calculation_method="standard_deviation_over_mean",
                formula="volatility = std_dev(monthly_multipliers) / mean(monthly_multipliers)",
                inputs=[f"months={len(seasonality_res.monthly_multipliers)}"],
                benchmarks_used=["seasonality_factors_nabard"],
                evidence_refs=["seasonality_tool_nabard_series"],
                assumptions=["12-month calendar cyclical demand distribution"],
                confidence=seasonality_res.confidence
            )
        ]

        # 8. Build Features for Stage 7 ML Model
        market_features = feature_builder_service.build_market_features(
            business_context=business_context,
            location_context=location_context,
            demographics=cleaned_demographics,
            indicators=market_indicators,
            benchmarks=benchmarks
        )

        # 9. Evidence Quality & Confidence Propagation
        evidence_quality = confidence_service.calculate_evidence_quality(
            indicators=market_indicators,
            demographics=cleaned_demographics,
            infrastructure_reqs=cleaned_infra,
            stage5_quality=evidence_quality_in
        )

        # 10. Final Workflow State
        has_gaps = len(evidence_quality.data_gaps) > 0 or infrastructure_res.readiness == "UNKNOWN_DATA_GAP"
        workflow_state = Stage6WorkflowState(
            stage=6,
            state="MARKET_INTELLIGENCE_ANALYZED",
            status="complete_with_gaps" if has_gaps else "complete"
        )

        exec_time = round(time.time() - start_time, 3)
        logger.info(f"[STAGE 6 ENGINE] Completed analysis in {exec_time}s with status '{workflow_state.status}' (overall confidence: {evidence_quality.overall_confidence})")

        return Stage6Output(
            schema_version="1.0",
            analysis_id=analysis_id,
            session_id=session_id,
            workflow=workflow_state,
            business_context=business_context,
            location_context=location_context,
            market_indicators=market_indicators,
            market_features=market_features,
            benchmark_analysis=benchmark_analysis,
            evidence_quality=evidence_quality,
            calculation_provenance=calculation_provenance,
            evidence_gaps=evidence_quality.data_gaps,
            next_stage=NextStageContract(
                stage=7,
                component="DEMAND_PREDICTION_ML_MODEL",
                input_contract="market_features"
            ),
            execution_metadata=ExecutionMetadata(
                engine=self.engine_name,
                engine_version=self.version,
                llm_used=False,
                status="SUCCESS",
                execution_time_seconds=exec_time
            )
        )


market_intelligence_engine = MarketIntelligenceEngine()
