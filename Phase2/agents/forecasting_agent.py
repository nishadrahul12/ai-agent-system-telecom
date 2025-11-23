"""
Forecasting Agent for Time-Series Prediction.

Responsibilities:
- Wrap TimeSeriesModels for orchestrator integration
- Handle data preprocessing and validation
- Manage automatic model selection
- Provide trend analysis
- Generate forecasts with confidence intervals
- Return orchestrator-compatible results

Architecture:
- Single responsibility: Time-series forecasting agent
- Inherits patterns from Phase 1 agents
- Type-safe: 100% type hints
- Logging: All operations logged
- Error handling: Custom exceptions

Features:
- Auto model selection (ARIMA, LSTM, Exponential Smoothing)
- Trend analysis (increasing/decreasing/stable)
- Forecast validation
- Confidence interval estimation
- Orchestrator integration via run() method
"""

import logging
import numpy as np
from typing import Any, Dict, Optional, Tuple, List

from Phase2.models.time_series_models import (
    TimeSeriesModels,
    DataValidationError,
    ModelTrainingError,
    ForecastError
)

logger = logging.getLogger(__name__)


class ForecastingAgent:
    """
    Time-series forecasting agent for telecom KPI prediction.

    Wraps TimeSeriesModels and provides orchestrator interface.
    Automatically selects best forecasting model based on data characteristics.
    Supports ARIMA, LSTM, and Exponential Smoothing models.

    Attributes:
        name (str): Agent identifier
        version (str): Agent version
        models (TimeSeriesModels): Wrapped forecasting models
        last_forecast (Optional[Dict]): Cache of last generated forecast
        last_data (Optional[np.ndarray]): Cache of last processed data
        metadata (Dict): Forecast metadata (trend, confidence, etc.)

    Constants:
        SUPPORTED_PERIODS: Valid forecast periods (7, 14, 30 days)
        MIN_DATA_POINTS: Minimum historical data required
        CONFIDENCE_THRESHOLD: Minimum acceptable MAPE (95%)
    """

    # Configuration constants
    SUPPORTED_PERIODS: List[int] = [7, 14, 30]
    MIN_DATA_POINTS: int = 30
    CONFIDENCE_THRESHOLD: float = 0.95
    TREND_THRESHOLD: float = 0.1

    def __init__(
        self,
        name: str = "forecasting_agent",
        version: str = "0.1.0"
    ) -> None:
        """
        Initialize forecasting agent.

        Args:
            name: Agent identifier
            version: Agent version

        Raises:
            None
        """
        self.name: str = name
        self.version: str = version
        self.models: TimeSeriesModels = TimeSeriesModels()
        self.last_forecast: Optional[Dict[str, Any]] = None
        self.last_data: Optional[np.ndarray] = None
        self.metadata: Dict[str, Any] = {}

        logger.info(f"[{self.name}] Initialized version {self.version}")

    def load_data(self, data: np.ndarray) -> bool:
        """
        Load and validate time-series data.

        Args:
            data: 1D numpy array of historical values

        Returns:
            bool: True if data loaded successfully

        Raises:
            DataValidationError: If data invalid or insufficient
            TypeError: If data not array-like
        """
        try:
            # Convert to numpy array
            data_array = np.asarray(data, dtype=np.float32)

            # Validate shape
            if data_array.ndim != 1:
                raise DataValidationError(
                    f"Expected 1D array, got {data_array.ndim}D",
                    details={"shape": data_array.shape}
                )

            # Validate size
            if len(data_array) < self.MIN_DATA_POINTS:
                raise DataValidationError(
                    f"Insufficient data: {len(data_array)} points (need {self.MIN_DATA_POINTS})",
                    details={"points": len(data_array), "minimum": self.MIN_DATA_POINTS}
                )

            # Validate no NaN/Inf
            if np.any(np.isnan(data_array)) or np.any(np.isinf(data_array)):
                raise DataValidationError(
                    "Data contains NaN or infinite values",
                    details={"nan_count": np.sum(np.isnan(data_array)), "inf_count": np.sum(np.isinf(data_array))}
                )

            # Cache data
            self.last_data = data_array
            logger.info(f"[{self.name}] Loaded {len(data_array)} data points")
            return True

        except DataValidationError:
            raise
        except Exception as e:
            error_msg = f"Data loading failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            raise DataValidationError(error_msg, details={"error": str(e)})

    def forecast(
        self,
        periods: int = 30,
        model: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate forecast using selected model.

        Args:
            periods: Number of periods to forecast
            model: Model name ("auto", "arima", "lstm", "exponential_smoothing")

        Returns:
            Dict with forecast, confidence intervals, metrics

        Raises:
            ValueError: If invalid model or periods
            ForecastError: If forecasting fails
            RuntimeError: If no data loaded
        """
        if self.last_data is None:
            raise RuntimeError("No data loaded. Call load_data() first.")

        if periods not in self.SUPPORTED_PERIODS:
            raise ValueError(
                f"Invalid periods: {periods}. Supported: {self.SUPPORTED_PERIODS}"
            )

        try:
            logger.info(f"[{self.name}] Starting forecast: periods={periods}, model={model}")

            # Select model
            if model == "auto":
                logger.debug(f"[{self.name}] Auto-selecting best model")
                comparison = self.models.compare_models(self.last_data, periods)
                # Extract best model forecast from comparison
                best_model = comparison.get("best_model", "arima")
                method_name = f"forecast_{best_model}"
                forecast_method = getattr(self.models, method_name)
                result = forecast_method(self.last_data, periods)
                selected_model = best_model
            elif model in ["arima", "lstm", "exponential_smoothing"]:
                method_name = f"forecast_{model}"
                forecast_method = getattr(self.models, method_name)
                result = forecast_method(self.last_data, periods)
                selected_model = model
            else:
                raise ValueError(f"Unknown model: {model}")


            # Analyze trend
            trend = self.analyze_trend(self.last_data)


            # Validate forecast
            if "forecast" in result and not self.validate_forecast(np.array(result["forecast"])):
                logger.warning(f"[{self.name}] Forecast validation warning")


            # Cache result
            self.last_forecast = result
            self.metadata = {
                "periods": periods,
                "model": selected_model,
                "trend": trend,
                "mape": result.get("mape", 0),
                "confidence_level": 0.95
            }

            logger.info(
                f"[{self.name}] Forecast complete: model={selected_model}, "
                f"MAPE={result.get('mape', 0):.2f}%"
            )

            return result

        except ForecastError:
            raise
        except Exception as e:
            error_msg = f"Forecasting failed: {str(e)}"
            logger.error(f"[{self.name}] {error_msg}", exc_info=True)
            raise ForecastError(error_msg, details={"error": str(e)})

    def analyze_trend(self, data: np.ndarray) -> Dict[str, Any]:
        """
        Analyze trend direction in time-series data.

        Args:
            data: 1D numpy array

        Returns:
            Dict with trend direction and slope

        Raises:
            ValueError: If invalid data
        """
        try:
            data_array = np.asarray(data, dtype=np.float32)

            if len(data_array) < 2:
                raise ValueError("Need at least 2 points for trend analysis")

            # Calculate slope using linear regression
            x = np.arange(len(data_array))
            coefficients = np.polyfit(x, data_array, 1)
            slope = float(coefficients[0])

            # Determine trend direction
            if slope > self.TREND_THRESHOLD:
                direction = "increasing"
            elif slope < -self.TREND_THRESHOLD:
                direction = "decreasing"
            else:
                direction = "stable"

            # Calculate trend strength (R² value)
            y_pred = np.polyval(coefficients, x)
            ss_res = np.sum((data_array - y_pred) ** 2)
            ss_tot = np.sum((data_array - np.mean(data_array)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            return {
                "direction": direction,
                "slope": slope,
                "strength": float(r_squared)
            }

        except Exception as e:
            logger.warning(f"[{self.name}] Trend analysis failed: {e}")
            return {
                "direction": "unknown",
                "slope": 0.0,
                "strength": 0.0
            }

    def validate_forecast(self, forecast: np.ndarray) -> bool:
        """
        Validate forecast quality and consistency.

        Args:
            forecast: 1D array of forecast values

        Returns:
            bool: True if forecast valid

        Raises:
            None
        """
        try:
            forecast_array = np.asarray(forecast, dtype=np.float32)

            # Check for NaN or Inf
            if np.any(np.isnan(forecast_array)) or np.any(np.isinf(forecast_array)):
                logger.warning(f"[{self.name}] Forecast contains NaN/Inf")
                return False

            # Check for extreme values (>1000% change from last data point)
            if self.last_data is not None and len(self.last_data) > 0:
                last_value = self.last_data[-1]
                if last_value != 0:
                    max_pct_change = np.max(np.abs((forecast_array - last_value) / last_value))
                    if max_pct_change > 10:  # 1000% change
                        logger.warning(f"[{self.name}] Extreme forecast values detected")
                        return False

            return True

        except Exception as e:
            logger.warning(f"[{self.name}] Validation error: {e}")
            return False

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method (orchestrator interface).

        Expected payload keys:
            - data: Historical time-series data (1D array)
            - periods: Forecast periods (optional, default=30)
            - model: Model name (optional, default="auto")

        Returns:
            Dict with status, forecast, trend, metadata

        Raises:
            None (catches all exceptions)
        """
        try:
            logger.info(f"[{self.name}] Starting execution")

            # Extract payload
            data = payload.get("data")
            periods = payload.get("periods", 30)
            model = payload.get("model", "auto")

            if data is None:
                raise ValueError("Missing required key: 'data'")

            # Load data
            self.load_data(data)

            # Forecast
            forecast_result = self.forecast(periods, model)

            # Analyze trend
            trend_analysis = self.analyze_trend(self.last_data)

            # Build response
            return {
                "status": "success",
                "forecast": forecast_result["forecast"],
                "confidence_interval_lower": forecast_result.get("confidence_interval_lower", []),
                "confidence_interval_upper": forecast_result.get("confidence_interval_upper", []),
                "trend": trend_analysis,
                "metrics": {
                    "mae": forecast_result.get("mae", 0),
                    "rmse": forecast_result.get("rmse", 0),
                    "mape": forecast_result.get("mape", 0),
                },
                "metadata": self.metadata
            }

        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "forecast": [],
                "trend": {"direction": "unknown", "slope": 0.0, "strength": 0.0}
            }


# Export
__all__ = ["ForecastingAgent"]
