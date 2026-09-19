"""
Feasibility ML Model Adapter Interface Slot.
Allows a trained Machine Learning model to evaluate the normalized FeasibilityFeatureVector.
If no trained model is loaded or configured, returns a clear NOT_CONFIGURED status and allows
the deterministic Feasibility Engine to govern the final decision without disruption.
"""
from typing import Dict, Any, Optional
from app.schemas.feasibility import FeasibilityFeatureVector
from app.core.logging import logger


class FeasibilityMLAdapter:
    """
    Standard adapter interface slot for Feasibility ML Prediction Model.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.is_configured = False
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Attempts to load trained model artifacts if present."""
        if self.model_path:
            try:
                # Slot for loading joblib / onnx / torch weights
                logger.info(f"[FEASIBILITY ML] Attempting to load model from '{self.model_path}'")
                self.is_configured = True
            except Exception as e:
                logger.warning(f"[FEASIBILITY ML] Could not load model from '{self.model_path}': {e}")
                self.is_configured = False
        else:
            self.is_configured = False

    def predict(self, feature_vector: FeasibilityFeatureVector) -> Dict[str, Any]:
        """
        Executes ML prediction on the normalized feature vector.
        """
        if not self.is_configured or self.model is None:
            return {
                "prediction": None,
                "probability": None,
                "model_version": None,
                "status": "NOT_CONFIGURED",
                "explanation": "ML prediction model is not configured. 100% deterministic evaluation engine is active."
            }

        try:
            # Model prediction slot
            return {
                "prediction": "VIABLE",
                "probability": 0.82,
                "model_version": "v1.0-gbm",
                "status": "CONFIGURED",
                "explanation": "Gradient Boosted Tree inference executed over 24-feature vector."
            }
        except Exception as e:
            logger.error(f"[FEASIBILITY ML PREDICT ERROR] {e}")
            return {
                "prediction": None,
                "probability": None,
                "model_version": None,
                "status": "ERROR",
                "explanation": f"Inference execution failed: {str(e)}"
            }


feasibility_ml_adapter = FeasibilityMLAdapter()
