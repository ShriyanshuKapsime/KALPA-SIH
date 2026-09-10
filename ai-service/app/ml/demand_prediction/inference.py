"""
Inference pipeline for Demand Prediction model.
"""
from typing import Dict, Any
from app.ml.demand_prediction.features import DemandFeatureExtractor
from app.ml.demand_prediction.model import DemandPredictionModel


class DemandInferencePipeline:
    def __init__(self):
        self.feature_extractor = DemandFeatureExtractor()
        self.model = DemandPredictionModel()

    def predict(self, raw_input: Dict[str, Any]) -> float:
        """
        Run inference over input attributes.
        """
        features_df = self.feature_extractor.extract_features(raw_input)
        return 0.0
