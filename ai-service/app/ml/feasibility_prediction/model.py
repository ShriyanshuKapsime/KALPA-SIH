"""
Model architecture scaffolding for Feasibility Prediction.
"""
from typing import Optional


class FeasibilityPredictionModel:
    """
    Scaffolding for XGBoost / Random Forest classifier/regressor evaluating viability score & survival risk.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None

    def load_model(self):
        pass
