"""
Seasonality Analysis Layer for Stage 6 Market Intelligence Engine.
Evaluates 12-month demand fluctuations, identifies peak/lean cycles,
and computes deterministic annual seasonal volatility and business risk.
"""
import math
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    SeasonalRiskLevel,
    SeasonalityAnalysisResult
)


class SeasonalityAnalysisService:
    def analyze_seasonality(
        self,
        raw_seasonality: Optional[List[Dict[str, Any]]],
        benchmarks: Dict[str, Any]
    ) -> SeasonalityAnalysisResult:
        """
        Executes deterministic seasonality analysis.
        """
        bm_factors = benchmarks.get("seasonality", {})
        notes = benchmarks.get("seasonality_notes", "Stable baseline demand across annual cycle")

        # Standard months
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        monthly_multipliers: Dict[str, float] = {}

        # 1. Merge Stage 5 evidence with benchmark baselines
        evidence_map: Dict[str, float] = {}
        if raw_seasonality:
            for item in raw_seasonality:
                m = str(item.get("month", "")).strip().lower()[:3]
                mult = item.get("multiplier") or item.get("value")
                if m in months and mult is not None:
                    try:
                        evidence_map[m] = float(mult)
                    except (ValueError, TypeError):
                        pass

        for m in months:
            if m in evidence_map:
                monthly_multipliers[m] = round(evidence_map[m], 3)
            elif m in bm_factors:
                monthly_multipliers[m] = round(float(bm_factors[m]), 3)
            else:
                monthly_multipliers[m] = 1.0

        # 2. Identify Peaks, Leans & Extremes
        values = list(monthly_multipliers.values())
        peak_val = max(values)
        lean_val = min(values)

        peak_months = [m for m, val in monthly_multipliers.items() if val >= 1.10]
        lean_months = [m for m, val in monthly_multipliers.items() if val <= 0.90]

        # 3. Compute Annual Volatility
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance)
        volatility = round(std_dev / max(0.01, mean_val), 3)

        # 4. Classify Seasonal Risk
        if volatility <= 0.12:
            seasonal_risk = SeasonalRiskLevel.LOW
        elif volatility <= 0.25:
            seasonal_risk = SeasonalRiskLevel.MODERATE
        else:
            seasonal_risk = SeasonalRiskLevel.HIGH

        return SeasonalityAnalysisResult(
            peak_months=peak_months,
            lean_months=lean_months,
            peak_multiplier=round(peak_val, 2),
            lean_multiplier=round(lean_val, 2),
            monthly_multipliers=monthly_multipliers,
            annual_volatility=volatility,
            seasonal_risk=seasonal_risk,
            seasonal_notes=notes,
            confidence=0.92
        )


seasonality_service = SeasonalityAnalysisService()
