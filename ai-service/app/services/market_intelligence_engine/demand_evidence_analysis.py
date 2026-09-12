"""
Demand Evidence Analysis Layer for Stage 6 Market Intelligence Engine.
Analyzes consumption expenditure proxies, demographic scale, purchasing power proxies,
and agricultural/commercial demand signals against business-specific benchmarks.
"""
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    DemandSignalStrength,
    DemandEvidenceAnalysisResult,
    CleanedDemographicMetric,
    CleanedDemandIndicator
)


class DemandEvidenceAnalysisService:
    def analyze_demand_evidence(
        self,
        demographics: List[CleanedDemographicMetric],
        demand_indicators: List[CleanedDemandIndicator],
        benchmarks: Dict[str, Any]
    ) -> DemandEvidenceAnalysisResult:
        """
        Executes deterministic demand evidence synthesis.
        """
        catchment_bm = benchmarks.get("catchment", {})
        target_pop_min = float(catchment_bm.get("target_population_min", 10000))
        target_hh_min = float(catchment_bm.get("target_household_count_min", 2000))

        # 1. Extract Demographic Values
        demo_dict: Dict[str, Any] = {}
        for d in demographics:
            demo_dict[d.metric] = d.value

        pop_val = demo_dict.get("total_population") or 0
        hh_val = demo_dict.get("total_households") or 0
        density_val = demo_dict.get("population_density") or 0
        rural_pct = demo_dict.get("rural_percentage") or 50.0

        # Population Scale Score
        pop_ratio = (pop_val / target_pop_min) if target_pop_min > 0 else 1.0
        pop_score = min(1.0, max(0.1, pop_ratio))

        # Household Scale Score
        hh_ratio = (hh_val / target_hh_min) if target_hh_min > 0 else 1.0
        hh_score = min(1.0, max(0.1, hh_ratio))

        # 2. Extract Demand Indicators
        consumption_signals = []
        demographic_signals = []
        economic_signals = []
        consumption_val = None

        for ind in demand_indicators:
            name_lower = ind.indicator_name.lower()
            val = ind.normalized_value or ind.raw_value

            sig_entry = {
                "indicator_name": ind.indicator_name,
                "value": val,
                "unit": ind.unit,
                "data_status": ind.data_status.value,
                "proxy": ind.proxy,
                "business_relevance": ind.business_relevance
            }

            if "consumption" in name_lower or "expenditure" in name_lower or "protein" in name_lower or "surplus" in name_lower:
                consumption_signals.append(sig_entry)
                if consumption_val is None and ind.normalized_value is not None:
                    consumption_val = ind.normalized_value
            elif "population" in name_lower or "household" in name_lower or "density" in name_lower or "demographic" in name_lower:
                demographic_signals.append(sig_entry)
            else:
                economic_signals.append(sig_entry)

        # 3. Consumption Proxy Normalization
        # Standard rural/semi-urban monthly consumption expenditure benchmark baseline = 3000 INR
        consumption_baseline = 3000.0
        if consumption_val is not None and consumption_val > 0:
            cons_score = min(1.0, max(0.2, consumption_val / (consumption_baseline * 1.5)))
        else:
            cons_score = 0.65  # Baseline default proxy

        # Composite Demand Signal Score
        # 40% Population Scale + 30% Household Scale + 30% Consumption / Economic signals
        composite_demand_score = round(
            0.40 * pop_score +
            0.30 * hh_score +
            0.30 * cons_score,
            3
        )

        # Demand Signal Strength Classification
        if composite_demand_score >= 0.75:
            strength = DemandSignalStrength.STRONG
        elif composite_demand_score >= 0.50:
            strength = DemandSignalStrength.MODERATE
        elif composite_demand_score >= 0.30:
            strength = DemandSignalStrength.EMERGING
        else:
            strength = DemandSignalStrength.WEAK

        # Structured Feature Objects for Stage 7 ML
        pop_feature = {
            "total_population": pop_val,
            "target_population_min": target_pop_min,
            "population_scale_ratio": round(pop_ratio, 2),
            "pop_scale_score": round(pop_score, 2)
        }

        hh_feature = {
            "total_households": hh_val,
            "target_household_count_min": target_hh_min,
            "household_scale_ratio": round(hh_ratio, 2),
            "hh_scale_score": round(hh_score, 2)
        }

        cons_feature = {
            "raw_value": consumption_val or consumption_baseline,
            "unit": "INR_monthly_expenditure_proxy",
            "data_status": "PROXY" if consumption_val is None else "ACTUAL",
            "normalized_score": round(cons_score, 2),
            "benchmark_baseline": consumption_baseline
        }

        purchasing_power_feature = {
            "rural_percentage": rural_pct,
            "population_density": density_val,
            "purchasing_power_tier": "TIER_3_RURAL_GROWTH" if rural_pct > 50 else "SEMI_URBAN_GROWTH",
            "estimated_index": round(cons_score * 100, 1)
        }

        seasonal_demand_feature = {
            "demand_multiplier_range": [0.75, 1.30],
            "primary_driver": benchmarks.get("demand_drivers", ["Local household consumption"])[0] if benchmarks.get("demand_drivers") else "Local staple demand"
        }

        coverage = round(
            (len(demographics) + len(demand_indicators)) / (6.0 + 3.0),
            2
        )
        coverage = min(1.0, max(0.3, coverage))

        return DemandEvidenceAnalysisResult(
            population_feature=pop_feature,
            household_feature=hh_feature,
            consumption_proxy=cons_feature,
            purchasing_power_proxy=purchasing_power_feature,
            seasonal_demand=seasonal_demand_feature,
            consumption_signals=consumption_signals,
            demographic_signals=demographic_signals,
            economic_signals=economic_signals,
            demand_signal_strength=strength,
            demand_signal_score=composite_demand_score,
            data_coverage=coverage,
            confidence=0.85
        )


demand_evidence_service = DemandEvidenceAnalysisService()
