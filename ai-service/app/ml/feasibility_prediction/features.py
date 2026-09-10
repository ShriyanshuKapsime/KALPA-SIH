"""
Feature extraction definitions for Feasibility Prediction ML Model.
"""
from typing import Dict, Any
import pandas as pd


class FeasibilityFeatureExtractor:
    """
    Transforms enterprise inputs, financial metrics, and spatial indicators into composite viability vectors.
    """
    def __init__(self):
        self.feature_names = [
            "debt_service_coverage_ratio",
            "break_even_point_percentage",
            "promoter_equity_ratio",
            "market_saturation_index",
            "entrepreneur_experience_years"
        ]

    def extract_features(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        row = {f: raw_data.get(f, 0.0) for f in self.feature_names}
        return pd.DataFrame([row])
