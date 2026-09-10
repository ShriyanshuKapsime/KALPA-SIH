"""
Inference pipeline for Feasibility Prediction model.
"""
from typing import Dict, Any, Tuple
from app.ml.feasibility_prediction.features import FeasibilityFeatureExtractor
from app.ml.feasibility_prediction.model import FeasibilityPredictionModel


class FeasibilityInferencePipeline:
    def __init__(self):
        self.feature_extractor = FeasibilityFeatureExtractor()
        self.model = FeasibilityPredictionModel()

    def predict(self, raw_input: Dict[str, Any]) -> Tuple[float, str]:
        """
        Run inference over input metrics. Returns (viability_score, status_category).
        """
        features_df = self.feature_extractor.extract_features(raw_input)
        return (0.0, "pending_evaluation")
