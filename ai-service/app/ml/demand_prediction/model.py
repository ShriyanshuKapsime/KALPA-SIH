"""
Model architecture scaffolding for Demand Prediction.
"""
from typing import Optional


class DemandPredictionModel:
    """
    Scaffolding for XGBoost / Scikit-Learn regression model predicting local monthly demand units.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None

    def load_model(self):
        """
        Load trained weights if available.
        """
        pass
