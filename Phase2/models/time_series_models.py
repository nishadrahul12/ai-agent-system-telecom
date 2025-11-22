"""
Time-Series Models for Phase 2 Forecasting.

Responsibilities:
- ARIMA model implementation with parameter optimization
- LSTM model implementation (3-layer neural network)
- Automatic model selection based on accuracy
- Accuracy metrics calculation (MAE, RMSE, MAPE)
- Time-series data preprocessing and validation

Architecture:
- Single responsibility: Time-series forecasting models
- Type-safe: 100% type hints
- Error classification: Use custom exceptions
- Logging: All operations logged
- Testable: Pure functions where possible

Supported Models:
1. ARIMA (AutoRegressive Integrated Moving Average)
   - Best for: Univariate time-series with trend/seasonality
   - Parameters: (p, d, q)
   - Auto-optimization: Uses AIC criterion

2. LSTM (Long Short-Term Memory)
   - Best for: Non-linear patterns, longer sequences
   - Architecture: Input → LSTM(64) → LSTM(32) → Dense(1)
   - Epochs: 50, Batch size: 8

3. Exponential Smoothing (Fallback)
   - Best for: Simple, stable trends
   - Method: Simple exponential smoothing

Usage:
from Phase2.models.time_series_models import TimeSeriesModels

models = TimeSeriesModels()
forecast_arima = models.forecast_arima(data, periods=30)
forecast_lstm = models.forecast_lstm(data, periods=30)
"""

import logging
import warnings
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import tensorflow as tf

logger = logging.getLogger(__name__)

# Custom exceptions for forecasting
class TimeSeriesError(Exception):
    """Base exception for time-series operations."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}

class ModelTrainingError(TimeSeriesError):
    """Exception raised when model training fails."""
    pass

class DataValidationError(TimeSeriesError):
    """Exception raised when data validation fails."""
    pass

class ForecastError(TimeSeriesError):
    """Exception raised when forecast generation fails."""
    pass

class TimeSeriesModels:
    """Encapsulates time-series forecasting models (ARIMA, LSTM, Exponential Smoothing)."""

    # ARIMA parameter search space
    ARIMA_P_RANGE = range(0, 4)  # AR order
    ARIMA_D_RANGE = range(0, 3)  # Differencing order
    ARIMA_Q_RANGE = range(0, 4)  # MA order

    # LSTM hyperparameters (tuned for CPU)
    LSTM_UNITS_LAYER1 = 64
    LSTM_UNITS_LAYER2 = 32
    LSTM_EPOCHS = 50
    LSTM_BATCH_SIZE = 8
    LSTM_LOOKBACK = 5  # Use previous 5 timesteps

    # Accuracy metric thresholds
    MAPE_THRESHOLD = 20.0  # 20% acceptable
    RMSE_THRESHOLD = 1000.0  # Depends on data scale

    def __init__(self, random_state: int = 42) -> None:
        """
        Initialize time-series models container.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.arima_model: Optional[Any] = None
        self.lstm_model: Optional[Any] = None
        self.best_model: Optional[str] = None
        self.best_params: Dict[str, Any] = {}
        self.scaler: Optional[Any] = None
        logger.info("TimeSeriesModels initialized")

    def validate_data(self, data: np.ndarray) -> None:
        """
        Validate time-series data before modeling.

        Args:
            data: 1D array of time-series values

        Raises:
            DataValidationError: If data validation fails
        """
        logger.debug("Validating time-series data")

        if not isinstance(data, (np.ndarray, list)):
            raise DataValidationError(
                "Data must be numpy array or list",
                details={"type": type(data).__name__}
            )

        data_array = np.array(data)

        if len(data_array) < 10:
            raise DataValidationError(
                f"Insufficient data: {len(data_array)} points (minimum 10 required)",
                details={"provided": len(data_array), "minimum": 10}
            )

        if np.any(np.isnan(data_array)):
            raise DataValidationError(
                "Data contains NaN values",
                details={"nan_count": np.sum(np.isnan(data_array))}
            )

        if np.any(np.isinf(data_array)):
            raise DataValidationError(
                "Data contains infinite values",
                details={"inf_count": np.sum(np.isinf(data_array))}
            )

        logger.debug(f"Data validation passed: {len(data_array)} points")

    def forecast_arima(
        self,
        data: np.ndarray,
        periods: int = 30,
        order: Optional[Tuple[int, int, int]] = None,
        auto_optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Generate ARIMA forecast.

        Args:
            data: Historical time-series data (1D array)
            periods: Number of periods to forecast
            order: ARIMA (p, d, q) order. If None, auto-select.
            auto_optimize: Whether to search for best order

        Returns:
            Dict with forecast, confidence intervals, and metrics

        Raises:
            DataValidationError: If data invalid
            ModelTrainingError: If model training fails
            ForecastError: If forecast generation fails
        """

        # FIX 3: Validate periods
        if periods <= 0:
            raise ValueError(f"periods must be > 0, got {periods}")
        
        logger.info(f"Starting ARIMA forecast: {len(data)} historical points, {periods} forecast periods")

        try:
            # Validate data
            self.validate_data(data)

            # Import statsmodels
            try:
                from statsmodels.tsa.arima.model import ARIMA
                from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
            except ImportError:
                raise ModelTrainingError(
                    "statsmodels not installed. Run: pip install statsmodels>=0.13.0",
                    details={"required_package": "statsmodels"}
                )

            data_array = np.array(data)

            # Find best order if not specified
            if order is None and auto_optimize:
                logger.info("Auto-optimizing ARIMA parameters")
                order = self._find_best_arima_order(data_array)
                logger.info(f"Selected ARIMA order: {order}")
            elif order is None:
                order = (1, 1, 1)  # Default order
                logger.info(f"Using default ARIMA order: {order}")

            # Train ARIMA model
            logger.debug(f"Training ARIMA with order {order}")
            model = ARIMA(data_array, order=order)
            self.arima_model = model.fit()

            # Generate forecast
            logger.debug(f"Generating {periods}-period forecast")
            forecast_result = self.arima_model.get_forecast(steps=periods)
            forecast_mean = forecast_result.predicted_mean
            forecast_ci = forecast_result.conf_int()

            # Handle both numpy and pandas Series
            if hasattr(forecast_mean, 'values'):
                forecast_mean_values = forecast_mean.values
            else:
                forecast_mean_values = np.asarray(forecast_mean)
    
            if hasattr(forecast_ci, 'values'):
                forecast_ci_values = forecast_ci.values
            else:
                forecast_ci_values = np.asarray(forecast_ci)


            # Calculate accuracy metrics on training set (in-sample)
            in_sample_pred = self.arima_model.fittedvalues
            mae = np.mean(np.abs(data_array - in_sample_pred))
            rmse = np.sqrt(np.mean((data_array - in_sample_pred) ** 2))
            mape = np.mean(np.abs((data_array - in_sample_pred) / (np.abs(data_array) + 1e-8))) * 100

            result = {
                "model": "ARIMA",
                "order": order,
                "forecast": forecast_mean_values.tolist() if hasattr(forecast_mean_values, 'tolist') else list(forecast_mean_values),
                "confidence_interval_lower": forecast_ci_values[:, 0].tolist() if hasattr(forecast_ci_values, 'tolist') else list(forecast_ci_values[:, 0]),
                "confidence_interval_upper": forecast_ci_values[:, 1].tolist() if hasattr(forecast_ci_values, 'tolist') else list(forecast_ci_values[:, 1]),

                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "success": True
            }

            logger.info(f"ARIMA forecast generated: MAE={mae:.4f}, RMSE={rmse:.4f}, MAPE={mape:.2f}%")
            return result

        except ModelTrainingError:
            raise
        except Exception as e:
            error_msg = f"ARIMA forecasting failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ForecastError(error_msg, details={"error": str(e)})

    def forecast_lstm(
        self,
        data: np.ndarray,
        periods: int = 30,
        lookback: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate LSTM forecast.

        Args:
            data: Historical time-series data (1D array)
            periods: Number of periods to forecast
            lookback: Number of previous steps to use

        Returns:
            Dict with forecast, confidence intervals, and metrics

        Raises:
            DataValidationError: If data invalid
            ModelTrainingError: If model training fails
            ForecastError: If forecast generation fails
        """
        # FIX 3: Validate periods
        if periods <= 0:
            raise ValueError(f"periods must be > 0, got {periods}")

        logger.info(f"Starting LSTM forecast: {len(data)} historical points, {periods} forecast periods")

        try:
            # Validate data
            self.validate_data(data)

            # Import TensorFlow
            try:
                from tensorflow import keras
                from tensorflow.keras import layers
                from sklearn.preprocessing import MinMaxScaler
            except ImportError:
                raise ModelTrainingError(
                    "TensorFlow not installed. Run: pip install tensorflow>=2.10.0",
                    details={"required_package": "tensorflow"}
                )

            data_array = np.array(data, dtype=np.float32).reshape(-1, 1)
            lookback = lookback or self.LSTM_LOOKBACK

            # Normalize data
            logger.debug("Normalizing data for LSTM")
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data_array)
            self.scaler = scaler

            # Create sequences
            logger.debug(f"Creating sequences with lookback={lookback}")
            X, y = self._create_sequences(scaled_data, lookback)

            if len(X) < 10:
                raise DataValidationError(
                    f"Insufficient sequences after preprocessing: {len(X)} (need at least 10)",
                    details={"sequences": len(X), "lookback": lookback}
                )

            # Build LSTM model
            logger.debug("Building LSTM model")
            tf.keras.backend.clear_session()
            model = keras.Sequential([
                layers.LSTM(self.LSTM_UNITS_LAYER1, activation='relu', return_sequences=True, input_shape=(lookback, 1)),
                layers.LSTM(self.LSTM_UNITS_LAYER2, activation='relu'),
                layers.Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])

            # Train model
            logger.info(f"Training LSTM for {self.LSTM_EPOCHS} epochs")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                history = model.fit(
                    X, y,
                    epochs=self.LSTM_EPOCHS,
                    batch_size=self.LSTM_BATCH_SIZE,
                    verbose=0
                )

            self.lstm_model = model

            # Calculate training metrics
            train_pred = model.predict(X, verbose=0)
            train_mae = np.mean(np.abs(y - train_pred))
            train_rmse = np.sqrt(np.mean((y - train_pred) ** 2))

            # Denormalize predictions for MAPE calculation
            train_pred_denorm = scaler.inverse_transform(train_pred)
            # Reshape y to 2D if needed for scaler
            y_2d = y.reshape(-1, 1) if y.ndim == 1 else y
            y_denorm = scaler.inverse_transform(y_2d)
            train_mape = np.mean(np.abs((y_denorm - train_pred_denorm) / (np.abs(y_denorm) + 1e-8))) * 100


            # Generate forecast
            logger.debug(f"Generating {periods}-period forecast")
            last_sequence = scaled_data[-lookback:].reshape(1, lookback, 1)
            forecast = []

            for _ in range(periods):
                next_pred = model.predict(last_sequence, verbose=0)[0, 0]
                forecast.append(next_pred)
                last_sequence = np.append(last_sequence[:, 1:, :], [[[next_pred]]], axis=1)

            # Denormalize forecast
            forecast_array = np.array(forecast).reshape(-1, 1)
            forecast_denorm = scaler.inverse_transform(forecast_array).flatten()

            # Simple confidence intervals (±10% of forecast)
            ci_lower = (forecast_denorm * 0.9).tolist()
            ci_upper = (forecast_denorm * 1.1).tolist()

            result = {
                "model": "LSTM",
                "lookback": lookback,
                "forecast": forecast_denorm.tolist(),
                "confidence_interval_lower": ci_lower,
                "confidence_interval_upper": ci_upper,
                "mae": float(train_mae),
                "rmse": float(train_rmse),
                "mape": float(train_mape),
                "success": True
            }

            logger.info(f"LSTM forecast generated: MAE={train_mae:.4f}, RMSE={train_rmse:.4f}, MAPE={train_mape:.2f}%")
            return result

        except ModelTrainingError:
            raise
        except Exception as e:
            error_msg = f"LSTM forecasting failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ForecastError(error_msg, details={"error": str(e)})

    def forecast_exponential_smoothing(
        self,
        data: np.ndarray,
        periods: int = 30,
        smoothing_level: float = 0.2
    ) -> Dict[str, Any]:
        
        # FIX 3: Validate periods
        if periods <= 0:
            raise ValueError(f"periods must be > 0, got {periods}")
        """
        Generate Exponential Smoothing forecast (fallback model).

        Args:
            data: Historical time-series data (1D array)
            periods: Number of periods to forecast
            smoothing_level: Smoothing coefficient (0-1)

        Returns:
            Dict with forecast, confidence intervals, and metrics

        Raises:
            DataValidationError: If data invalid
            ForecastError: If forecast generation fails
        """
        logger.info(f"Starting Exponential Smoothing forecast: {len(data)} points, {periods} periods")

        try:
            self.validate_data(data)
            data_array = np.array(data)
            import pandas as pd
            data_array = pd.Series(data_array)

            # Simple exponential smoothing
            logger.debug(f"Applying exponential smoothing (alpha={smoothing_level})")
            smoothed = [data_array[0]]

            for i in range(1, len(data_array)):
                smoothed.append(
                    smoothing_level * data_array[i] + (1 - smoothing_level) * smoothed[i - 1]
                )

            # Forecast using last smoothed value
            last_value = smoothed[-1]
            trend = np.mean(np.diff(data_array[-10:]))  # Trend from last 10 values

            forecast = [last_value + trend * (i + 1) for i in range(periods)]

            # Calculate training metrics
            mae = np.mean(np.abs(data_array - np.array(smoothed)))
            rmse = np.sqrt(np.mean((data_array - np.array(smoothed)) ** 2))
            mape = np.mean(np.abs((data_array - np.array(smoothed)) / (np.abs(data_array) + 1e-8))) * 100

            # Simple confidence intervals
            std_error = np.std(np.array(smoothed) - data_array)
            ci_lower = [f - 1.96 * std_error for f in forecast]
            ci_upper = [f + 1.96 * std_error for f in forecast]

            result = {
                "model": "ExponentialSmoothing",
                "smoothing_level": smoothing_level,
                "forecast": forecast,
                "confidence_interval_lower": ci_lower,
                "confidence_interval_upper": ci_upper,
                "mae": float(mae),
                "rmse": float(rmse),
                "mape": float(mape),
                "success": True
            }

            logger.info(f"Exponential Smoothing forecast generated: MAE={mae:.4f}, RMSE={rmse:.4f}, MAPE={mape:.2f}%")
            return result

        except Exception as e:
            error_msg = f"Exponential Smoothing forecasting failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ForecastError(error_msg, details={"error": str(e)})

    def compare_models(
        self,
        data: np.ndarray,
        periods: int = 30
    ) -> Dict[str, Any]:
        """
        Train and compare all available models.

        Args:
            data: Historical time-series data
            periods: Number of periods to forecast

        Returns:
            Dict with results from all models and best model recommendation

        Raises:
            DataValidationError: If data invalid
        """
        logger.info("Starting model comparison")
        self.validate_data(data)

        results = {
            "comparison": {},
            "best_model": None,
            "best_score": -np.inf,
            "metrics": {}
        }

        # Try ARIMA
        try:
            logger.debug("Testing ARIMA model")
            arima_result = self.forecast_arima(data, periods)
            results["comparison"]["arima"] = arima_result
            arima_score = -arima_result["mape"]  # Negative MAPE (lower is better)
            logger.info(f"ARIMA MAPE: {arima_result['mape']:.2f}%")

            if arima_score > results["best_score"]:
                results["best_score"] = arima_score
                results["best_model"] = "arima"
                self.best_model = "arima"
        except Exception as e:
            logger.warning(f"ARIMA failed: {e}")
            results["comparison"]["arima"] = {"error": str(e)}

        # Try LSTM
        try:
            logger.debug("Testing LSTM model")
            lstm_result = self.forecast_lstm(data, periods)
            results["comparison"]["lstm"] = lstm_result
            lstm_score = -lstm_result["mape"]
            logger.info(f"LSTM MAPE: {lstm_result['mape']:.2f}%")

            if lstm_score > results["best_score"]:
                results["best_score"] = lstm_score
                results["best_model"] = "lstm"
                self.best_model = "lstm"
        except Exception as e:
            logger.warning(f"LSTM failed: {e}")
            results["comparison"]["lstm"] = {"error": str(e)}

        # Try Exponential Smoothing (always works)
        try:
            logger.debug("Testing Exponential Smoothing model")
            es_result = self.forecast_exponential_smoothing(data, periods)
            results["comparison"]["exponential_smoothing"] = es_result
            es_score = -es_result["mape"]
            logger.info(f"Exponential Smoothing MAPE: {es_result['mape']:.2f}%")

            if es_score > results["best_score"]:
                results["best_score"] = es_score
                results["best_model"] = "exponential_smoothing"
                self.best_model = "exponential_smoothing"
        except Exception as e:
            logger.warning(f"Exponential Smoothing failed: {e}")
            results["comparison"]["exponential_smoothing"] = {"error": str(e)}

        if results["best_model"] is None:
            raise ForecastError(
                "All models failed",
                details={"errors": results["comparison"]}
            )

        logger.info(f"Best model selected: {results['best_model']} (MAPE: {-results['best_score']:.2f}%)")
        return results

    def _find_best_arima_order(self, data: np.ndarray) -> Tuple[int, int, int]:
        """
        Find best ARIMA (p, d, q) order using AIC criterion.

        Args:
            data: Time-series data

        Returns:
            Best (p, d, q) order
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
        except ImportError:
            logger.warning("statsmodels not available, using default ARIMA order")
            return (1, 1, 1)

        best_order = (1, 1, 1)
        best_aic = np.inf

        logger.debug("Searching ARIMA parameter space")
        search_count = 0

        for p in self.ARIMA_P_RANGE:
            for d in self.ARIMA_D_RANGE:
                for q in self.ARIMA_Q_RANGE:
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        fitted_model = model.fit()
                        aic = fitted_model.aic

                        if aic < best_aic:
                            best_aic = aic
                            best_order = (p, d, q)

                        search_count += 1
                    except Exception as e:
                        logger.debug(f"Order ({p}, {d}, {q}) failed: {e}")
                        continue

        logger.debug(f"Searched {search_count} ARIMA combinations, best order: {best_order}")
        return best_order

    def _create_sequences(
        self,
        data: np.ndarray,
        lookback: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training.

        Args:
            data: Scaled time-series data
            lookback: Number of previous steps to use

        Returns:
            Tuple of (X, y) for LSTM input/output
        """
        X, y = [], []

        for i in range(lookback, len(data)):
            X.append(data[i - lookback:i, 0])
            y.append(data[i, 0])

        return np.array(X).reshape(-1, lookback, 1), np.array(y)

    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get summary of available models and current state.

        Returns:
            Summary dictionary
        """
        return {
            "available_models": ["arima", "lstm", "exponential_smoothing"],
            "best_model": self.best_model,
            "arima_model": "trained" if self.arima_model else "not_trained",
            "lstm_model": "trained" if self.lstm_model else "not_trained",
            "arima_params": {
                "p_range": list(self.ARIMA_P_RANGE),
                "d_range": list(self.ARIMA_D_RANGE),
                "q_range": list(self.ARIMA_Q_RANGE)
            },
            "lstm_params": {
                "units_layer1": self.LSTM_UNITS_LAYER1,
                "units_layer2": self.LSTM_UNITS_LAYER2,
                "epochs": self.LSTM_EPOCHS,
                "batch_size": self.LSTM_BATCH_SIZE,
                "lookback": self.LSTM_LOOKBACK
            }
        }
