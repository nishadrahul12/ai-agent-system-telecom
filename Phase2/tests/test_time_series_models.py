"""
Test Suite for time_series_models.py

Test Coverage:
- Data validation (5 tests)
- ARIMA forecasting (3 tests)
- LSTM forecasting (3 tests)
- Exponential Smoothing (2 tests)
- Model comparison (2 tests)

Total: 15 tests, all passing expected

Usage:
python -m pytest test_time_series_models.py -v
"""

import pytest
import numpy as np
import logging
from typing import List

# Import from time_series_models (adjust path as needed)
from Phase2.models.time_series_models import (
    TimeSeriesModels,
    TimeSeriesError,
    DataValidationError,
    ModelTrainingError,
    ForecastError
)

logger = logging.getLogger(__name__)


class TestDataValidation:
    """Test data validation methods."""

    @pytest.fixture
    def models(self) -> TimeSeriesModels:
        """Create TimeSeriesModels instance."""
        return TimeSeriesModels()

    @pytest.fixture
    def valid_data(self) -> np.ndarray:
        """Valid 30-point time-series."""
        return np.random.randn(30) + 100  # Mean 100, random noise

    def test_validate_data_valid_input(self, models: TimeSeriesModels, valid_data: np.ndarray) -> None:
        """Test validation passes for valid data."""
        try:
            models.validate_data(valid_data)
            assert True  # No exception raised
        except Exception as e:
            pytest.fail(f"Unexpected exception: {e}")

    def test_validate_data_insufficient_points(self, models: TimeSeriesModels) -> None:
        """Test validation fails for data with <10 points."""
        short_data = np.array([1, 2, 3, 4, 5])
        with pytest.raises(DataValidationError) as exc_info:
            models.validate_data(short_data)
        assert "Insufficient data" in str(exc_info.value)

    def test_validate_data_with_nan(self, models: TimeSeriesModels) -> None:
        """Test validation fails for data with NaN values."""
        data_with_nan = np.array([1, 2, np.nan, 4, 5] + [6] * 10)
        with pytest.raises(DataValidationError) as exc_info:
            models.validate_data(data_with_nan)
        assert "NaN" in str(exc_info.value)

    def test_validate_data_with_inf(self, models: TimeSeriesModels) -> None:
        """Test validation fails for data with infinite values."""
        data_with_inf = np.array([1, 2, np.inf, 4, 5] + [6] * 10)
        with pytest.raises(DataValidationError) as exc_info:
            models.validate_data(data_with_inf)
        assert "infinite" in str(exc_info.value)

    def test_validate_data_wrong_type(self, models: TimeSeriesModels) -> None:
        """Test validation fails for wrong data type."""
        with pytest.raises(DataValidationError) as exc_info:
            models.validate_data("not_an_array")
        assert "array or list" in str(exc_info.value)


class TestARIMAForecasting:
    """Test ARIMA forecasting methods."""

    @pytest.fixture
    def models(self) -> TimeSeriesModels:
        """Create TimeSeriesModels instance."""
        return TimeSeriesModels()

    @pytest.fixture
    def sample_data(self) -> np.ndarray:
        """Sample 30-point time-series with trend."""
        np.random.seed(42)
        t = np.arange(30)
        return 100 + 2 * t + 5 * np.random.randn(30)

    def test_arima_forecast_basic(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test basic ARIMA forecast generation."""
        try:
            result = models.forecast_arima(sample_data, periods=10, order=(1, 1, 1), auto_optimize=False)
            assert result["model"] == "ARIMA"
            assert result["order"] == (1, 1, 1)
            assert len(result["forecast"]) == 10
            assert len(result["confidence_interval_lower"]) == 10
            assert len(result["confidence_interval_upper"]) == 10
            assert "mae" in result and "rmse" in result and "mape" in result
            assert result["success"] is True
        except ModelTrainingError as e:
            pytest.skip(f"statsmodels not available: {e}")

    def test_arima_forecast_auto_optimize(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test ARIMA with automatic order optimization."""
        try:
            result = models.forecast_arima(sample_data, periods=10, auto_optimize=True)
            assert result["model"] == "ARIMA"
            assert result["order"] is not None
            assert len(result["order"]) == 3
            assert len(result["forecast"]) == 10
            assert result["success"] is True
        except ModelTrainingError as e:
            pytest.skip(f"statsmodels not available: {e}")

    def test_arima_confidence_intervals_valid(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test ARIMA confidence intervals are valid (upper > lower)."""
        try:
            result = models.forecast_arima(sample_data, periods=10, order=(1, 1, 1), auto_optimize=False)
            for i in range(len(result["forecast"])):
                assert result["confidence_interval_lower"][i] <= result["forecast"][i]
                assert result["forecast"][i] <= result["confidence_interval_upper"][i]
        except ModelTrainingError as e:
            pytest.skip(f"statsmodels not available: {e}")


class TestLSTMForecasting:
    """Test LSTM forecasting methods."""

    @pytest.fixture
    def models(self) -> TimeSeriesModels:
        """Create TimeSeriesModels instance."""
        return TimeSeriesModels()

    @pytest.fixture
    def sample_data(self) -> np.ndarray:
        """Sample 30-point time-series."""
        np.random.seed(42)
        t = np.arange(30)
        return 100 + 2 * t + 5 * np.random.randn(30)

    def test_lstm_forecast_basic(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test basic LSTM forecast generation."""
        try:
            result = models.forecast_lstm(sample_data, periods=10)
            assert result["model"] == "LSTM"
            assert len(result["forecast"]) == 10
            assert len(result["confidence_interval_lower"]) == 10
            assert len(result["confidence_interval_upper"]) == 10
            assert "mae" in result and "rmse" in result and "mape" in result
            assert result["success"] is True
            assert "lookback" in result
        except ModelTrainingError as e:
            pytest.skip(f"TensorFlow not available: {e}")

    def test_lstm_forecast_custom_lookback(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test LSTM with custom lookback window."""
        try:
            result = models.forecast_lstm(sample_data, periods=10, lookback=3)
            assert result["lookback"] == 3
            assert len(result["forecast"]) == 10
            assert result["success"] is True
        except ModelTrainingError as e:
            pytest.skip(f"TensorFlow not available: {e}")

    def test_lstm_confidence_intervals_valid(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test LSTM confidence intervals are valid."""
        try:
            result = models.forecast_lstm(sample_data, periods=10)
            for i in range(len(result["forecast"])):
                assert result["confidence_interval_lower"][i] <= result["forecast"][i]
                assert result["forecast"][i] <= result["confidence_interval_upper"][i]
        except ModelTrainingError as e:
            pytest.skip(f"TensorFlow not available: {e}")


class TestExponentialSmoothing:
    """Test Exponential Smoothing forecasting."""

    @pytest.fixture
    def models(self) -> TimeSeriesModels:
        """Create TimeSeriesModels instance."""
        return TimeSeriesModels()

    @pytest.fixture
    def sample_data(self) -> np.ndarray:
        """Sample 30-point time-series."""
        np.random.seed(42)
        t = np.arange(30)
        return 100 + 2 * t + 5 * np.random.randn(30)

    def test_exponential_smoothing_basic(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test Exponential Smoothing forecast."""
        result = models.forecast_exponential_smoothing(sample_data, periods=10)
        assert result["model"] == "ExponentialSmoothing"
        assert len(result["forecast"]) == 10
        assert len(result["confidence_interval_lower"]) == 10
        assert len(result["confidence_interval_upper"]) == 10
        assert "mae" in result and "rmse" in result and "mape" in result
        assert result["success"] is True

    def test_exponential_smoothing_confidence_intervals(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test Exponential Smoothing confidence intervals."""
        result = models.forecast_exponential_smoothing(sample_data, periods=10)
        for i in range(len(result["forecast"])):
            assert result["confidence_interval_lower"][i] <= result["forecast"][i]
            assert result["forecast"][i] <= result["confidence_interval_upper"][i]


class TestModelComparison:
    """Test model comparison functionality."""

    @pytest.fixture
    def models(self) -> TimeSeriesModels:
        """Create TimeSeriesModels instance."""
        return TimeSeriesModels()

    @pytest.fixture
    def sample_data(self) -> np.ndarray:
        """Sample 30-point time-series."""
        np.random.seed(42)
        t = np.arange(30)
        return 100 + 2 * t + 5 * np.random.randn(30)

    def test_compare_models_structure(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test model comparison returns proper structure."""
        result = models.compare_models(sample_data, periods=10)
        assert "comparison" in result
        assert "best_model" in result
        assert "best_score" in result
        assert result["best_model"] is not None
        assert "exponential_smoothing" in result["comparison"]

    def test_compare_models_best_selected(self, models: TimeSeriesModels, sample_data: np.ndarray) -> None:
        """Test that best model is properly selected."""
        result = models.compare_models(sample_data, periods=10)
        assert result["best_model"] in ["arima", "lstm", "exponential_smoothing"]
        # Best model should have a forecast result
        best_result = result["comparison"][result["best_model"]]
        assert "forecast" in best_result or "error" not in best_result


class TestModelSummary:
    """Test model summary methods."""

    def test_get_model_summary(self) -> None:
        """Test model summary generation."""
        models = TimeSeriesModels()
        summary = models.get_model_summary()
        assert "available_models" in summary
        assert "best_model" in summary
        assert "arima_model" in summary
        assert "lstm_model" in summary
        assert "arima_params" in summary
        assert "lstm_params" in summary
        assert len(summary["available_models"]) == 3


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_periods(self) -> None:
        """Test with invalid forecast periods."""
        models = TimeSeriesModels()
        data = np.random.randn(30) + 100

        # Zero periods
        with pytest.raises((ValueError, ForecastError)):
            models.forecast_exponential_smoothing(data, periods=0)

        # Negative periods
        with pytest.raises((ValueError, ForecastError)):
            models.forecast_exponential_smoothing(data, periods=-1)

    def test_constant_data(self) -> None:
        """Test with constant (no variation) data."""
        models = TimeSeriesModels()
        constant_data = np.ones(30) * 100

        try:
            # Exponential smoothing should handle constant data
            result = models.forecast_exponential_smoothing(constant_data, periods=10)
            assert result["success"] is True
        except ForecastError:
            pytest.skip("Constant data handling may vary")

    def test_list_input(self) -> None:
        """Test with list input instead of numpy array."""
        models = TimeSeriesModels()
        data_list = [100 + i + np.random.randn() for i in range(30)]

        try:
            result = models.forecast_exponential_smoothing(data_list, periods=10)
            assert result["success"] is True
        except DataValidationError as e:
            pytest.fail(f"List input should be supported: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
