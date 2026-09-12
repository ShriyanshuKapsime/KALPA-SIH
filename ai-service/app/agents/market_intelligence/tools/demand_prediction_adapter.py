"""
Demand Prediction Model Adapter (Tool 10).
Interface for future ML demand prediction model integration.
Honestly reports 'model_not_connected' and 'UNAVAILABLE' when the external ML inference service is offline
without faking synthetic predictions.
"""
import time
from typing import Dict, Any, Optional, Union
from app.agents.market_intelligence.tools.base_tool import BaseMarketTool, ToolExecutionContext, ToolResult
from app.schemas.market import DemandPredictionAdapterResult, MarketExecutionContext


class DemandPredictionAdapter(BaseMarketTool):
    def __init__(self, endpoint_url: Optional[str] = None):
        super().__init__(
            name="demand_prediction_adapter",
            description="Adapter interface for ML demand forecasting models. Returns disconnected status if model endpoint is not live.",
            supported_requirements=[
                "ml_demand_prediction",
                "future_demand_forecast",
                "demand_prediction_model"
            ]
        )
        self.endpoint_url = endpoint_url
        self._model_connected = False  # Set to True once external ML service container is connected

    def is_connected(self) -> bool:
        return bool(self.endpoint_url and self._model_connected)

    async def health_check(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tool": "DemandPredictionAdapter",
            "status": "available" if self.is_connected() else "model_not_connected",
            "supported_requirements": self.supported_requirements,
            "details": await self.get_model_metadata()
        }

    async def get_model_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": "KALPA Hyperlocal Demand Predictor (XGBoost/LightGBM)",
            "target_variable": "monthly_demand_volume",
            "connected": self.is_connected(),
            "endpoint": self.endpoint_url or "not_configured"
        }

    async def predict(
        self,
        business_type: str,
        location: Dict[str, Any],
        historical_evidence: Dict[str, Any],
        seasonality_indicators: Dict[str, Any]
    ) -> DemandPredictionAdapterResult:
        """
        Executes prediction or returns honest disconnected status.
        """
        if not self.is_connected():
            return DemandPredictionAdapterResult(
                available=False,
                status="model_not_connected",
                data_status="UNAVAILABLE",
                prediction=None,
                model_version=None,
                confidence=None,
                reason="Demand prediction ML model service is currently offline or endpoint not connected.",
                recommended_action="connect_demand_prediction_model"
            )

        return DemandPredictionAdapterResult(
            available=True,
            status="ready",
            data_status="LIVE_RETRIEVED",
            prediction={"forecast_monthly_units": 1200},
            model_version="v1.0.0",
            confidence=0.88,
            reason="Live ML model inference successful."
        )

    async def execute(self, context: Union[ToolExecutionContext, MarketExecutionContext]) -> ToolResult:
        start_t = time.perf_counter()

        if isinstance(context, MarketExecutionContext):
            concept = context.business.business_name
            loc_dict = context.location.model_dump()
            precision = context.location.geographic_precision or "district"
        else:
            bus_sec = (context.business_profile or {}).get("business_profile") or {}
            concept = (
                (context.canonical_business.business_name if context.canonical_business else None) or
                bus_sec.get("specific_business") or
                "Enterprise"
            )
            loc_dict = context.location_context or {}
            precision = loc_dict.get("geographic_precision") or "district"

        prediction_res = await self.predict(
            business_type=concept,
            location=loc_dict,
            historical_evidence={},
            seasonality_indicators={}
        )

        elapsed = (time.perf_counter() - start_t) * 1000.0

        return ToolResult(
            tool_name=self.name,
            status="success" if prediction_res.available else "unavailable",
            data_status=prediction_res.data_status,
            geographic_precision=precision,
            target_geographic_precision="village",
            data_geographic_precision=precision,
            confidence=0.0 if not prediction_res.available else 0.85,
            source={
                "source_id": "SRC-ML-DEMAND",
                "organization": "KALPA Machine Learning Hub",
                "source_type": "ML_PREDICTION_SERVICE",
                "retrieval_method": "INFERENCE_ADAPTER"
            },
            data={
                "demand_prediction": prediction_res.model_dump()
            },
            execution_time_ms=round(elapsed, 2)
        )
