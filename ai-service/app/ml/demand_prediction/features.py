"""
Feature extraction definitions for Demand Prediction ML Model.
"""
from typing import Dict, Any, List
import pandas as pd


class DemandFeatureExtractor:
    """
    Transforms raw geographic, demographic, and historical sector signals into feature vectors.
    """
    def __init__(self):
        self.feature_names = [
            "catchment_population",
            "per_capita_income_proxy",
            "competitor_density",
            "infrastructure_score",
            "seasonal_index"
        ]

    def extract_features(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert dictionary of attributes to feature DataFrame.
        """
        row = {f: raw_data.get(f, 0.0) for f in self.feature_names}
        return pd.DataFrame([row])
