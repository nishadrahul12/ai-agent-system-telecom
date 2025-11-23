"""
Test Suite for ForecastingAgent.

Comprehensive testing covering:
- Agent initialization and setup
- Data loading and validation
- Forecasting (all models)
- Trend analysis
- Forecast validation
- Orchestrator interface

Test Structure:
- 4 test classes
- 12 test methods
- Fixtures for sample data
- Full error case coverage
"""

import pytest
import numpy as np
from typing import Dict, Any

from Phase2.agents.forecasting_agent import ForecastingAgent
from Phase2.models.time_series_models import DataValidationError, ForecastError


# ============================================================================
# FIXTURES - Sample Data
# ============================================================================

@pytest.fixture
def sample_data() -> np.ndarray:
    """Generate sample time-series data."""
    np.random.seed(42)
    trend = np.linspace(100, 150, 50)  # Upward trend
    noise = np.random.randn(50) * 3
    return trend + noise


@pytest.fixture
def short_data() -> np.ndarray:
    """Generate data too short for forecasting."""
    return np.array([100.0, 101.0, 102.0, 103.0])


@pytest.fixture
def agent() -> ForecastingAgent:
    """Create agent instance."""
    return ForecastingAgent(name="test_agent", version="0.1.0")


# ============================================================================
# TestInitialization - Agent Setup
# ============================================================================

class TestInitialization:
    """Test agent initialization and setup."""

    def test_agent_initialization(self):
        """Test agent initializes with correct attributes."""
        agent = ForecastingAgent(name="test_agent", version="1.0.0")

        assert agent.name == "test_agent"
        assert agent.version == "1.0.0"
        assert agent.last_forecast is None
        assert agent.last_data is None
        assert isinstance(agent.metadata, dict)
        assert len(agent.metadata) == 0

    def test_models_instance_created(self, agent):
        """Test TimeSeriesModels instance is created."""
        assert agent.models is not None
        assert hasattr(agent.models, "forecast_arima")
        assert hasattr(agent.models, "forecast_lstm")
        assert hasattr(agent.models, "forecast_exponential_smoothing")
        assert hasattr(agent.models, "compare_models")


# ============================================================================
# TestDataLoading - Load and Validate Data
# ============================================================================

class TestDataLoading:
    """Test data loading and validation."""

    def test_load_valid_data(self, agent, sample_data):
        """Test loading valid time-series data."""
        result = agent.load_data(sample_data)

        assert result is True
        assert agent.last_data is not None
        assert len(agent.last_data) == len(sample_data)
        assert np.allclose(agent.last_data, sample_data)

    def test_load_invalid_data_insufficient_points(self, agent, short_data):
        """Test loading data with insufficient points raises error."""
        with pytest.raises(DataValidationError):
            agent.load_data(short_data)

    def test_load_invalid_data_with_nan(self, agent):
        """Test loading data with NaN values raises error."""
        data_with_nan = np.array([100.0, np.nan, 102.0] + [103.0] * 50)
        with pytest.raises(DataValidationError):
            agent.load_data(data_with_nan)

    def test_load_invalid_data_with_inf(self, agent):
        """Test loading data with infinite values raises error."""
        data_with_inf = np.array([100.0, np.inf, 102.0] + [103.0] * 50)
        with pytest.raises(DataValidationError):
            agent.load_data(data_with_inf)


# ============================================================================
# TestForecasting - Forecast Generation
# ============================================================================

class TestForecasting:
    """Test forecasting with different models."""

    def test_forecast_auto_model_selection(self, agent, sample_data):
        """Test forecasting with automatic model selection."""
        agent.load_data(sample_data)
        result = agent.forecast(periods=30, model="auto")

        assert "status" not in result or result.get("status") != "error"
        assert "forecast" in result
        assert len(result["forecast"]) == 30
        assert isinstance(result["forecast"], list)
        assert all(isinstance(v, (int, float, np.number)) for v in result["forecast"])

    def test_forecast_arima_model(self, agent, sample_data):
        """Test forecasting with ARIMA model."""
        agent.load_data(sample_data)
        result = agent.forecast(periods=14, model="arima")

        assert "forecast" in result
        assert len(result["forecast"]) == 14
        assert "mape" in result
        assert result["mape"] >= 0

    def test_forecast_lstm_model(self, agent, sample_data):
        """Test forecasting with LSTM model."""
        agent.load_data(sample_data)
        result = agent.forecast(periods=7, model="lstm")

        assert "forecast" in result
        assert len(result["forecast"]) == 7
        assert "mape" in result
        assert result["mape"] >= 0

    def test_forecast_exponential_smoothing_model(self, agent, sample_data):
        """Test forecasting with Exponential Smoothing model."""
        agent.load_data(sample_data)
        result = agent.forecast(periods=30, model="exponential_smoothing")

        assert "forecast" in result
        assert len(result["forecast"]) == 30
        assert "mape" in result
        assert result["mape"] >= 0

    def test_forecast_invalid_periods(self, agent, sample_data):
        """Test forecasting with invalid periods raises error."""
        agent.load_data(sample_data)
        with pytest.raises(ValueError):
            agent.forecast(periods=100, model="arima")

    def test_forecast_without_data(self, agent):
        """Test forecasting without loading data raises error."""
        with pytest.raises(RuntimeError):
            agent.forecast(periods=30, model="auto")


# ============================================================================
# TestTrendAnalysis - Trend Detection
# ============================================================================

class TestTrendAnalysis:
    """Test trend analysis."""

    def test_analyze_trend_increasing(self):
        """Test trend analysis detects increasing trend."""
        data = np.array([100 + i * 2 for i in range(50)])  # Clear upward trend
        agent = ForecastingAgent()

        trend = agent.analyze_trend(data)

        assert "direction" in trend
        assert "slope" in trend
        assert "strength" in trend
        assert trend["direction"] == "increasing"
        assert trend["slope"] > 0
        assert trend["strength"] >= 0

    def test_analyze_trend_decreasing(self):
        """Test trend analysis detects decreasing trend."""
        data = np.array([100 - i * 2 for i in range(50)])  # Clear downward trend
        agent = ForecastingAgent()

        trend = agent.analyze_trend(data)

        assert trend["direction"] == "decreasing"
        assert trend["slope"] < 0

    def test_analyze_trend_stable(self):
        """Test trend analysis detects stable trend."""
        data = np.array([100.0] * 50)  # Constant values
        agent = ForecastingAgent()

        trend = agent.analyze_trend(data)

        assert trend["direction"] == "stable"
        assert abs(trend["slope"]) < 0.1


# ============================================================================
# TestValidation - Forecast Validation
# ============================================================================

class TestValidation:
    """Test forecast validation."""

    def test_validate_forecast_valid(self, agent):
        """Test validation passes for valid forecast."""
        forecast = np.array([101.0, 102.0, 103.0, 104.0, 105.0])
        result = agent.validate_forecast(forecast)

        assert result is True

    def test_validate_forecast_with_nan(self, agent):
        """Test validation fails for forecast with NaN."""
        forecast = np.array([101.0, np.nan, 103.0, 104.0, 105.0])
        result = agent.validate_forecast(forecast)

        assert result is False

    def test_validate_forecast_with_inf(self, agent):
        """Test validation fails for forecast with infinity."""
        forecast = np.array([101.0, 102.0, np.inf, 104.0, 105.0])
        result = agent.validate_forecast(forecast)

        assert result is False


# ============================================================================
# TestOrchestrator - Orchestrator Interface
# ============================================================================

class TestOrchestrator:
    """Test orchestrator interface."""

    def test_run_orchestrator_interface(self, sample_data):
        """Test run() method follows orchestrator interface."""
        agent = ForecastingAgent(name="test_agent")
        payload = {
            "data": sample_data,
            "periods": 30,
            "model": "auto"
        }

        result = agent.run(payload)

        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "success"
        assert "forecast" in result
        assert "trend" in result
        assert "metrics" in result
        assert "metadata" in result
        assert len(result["forecast"]) == 30
        assert result["trend"]["direction"] in ["increasing", "decreasing", "stable"]

    def test_run_missing_data(self):
        """Test run() with missing data returns error."""
        agent = ForecastingAgent()
        payload = {
            "periods": 30,
            "model": "auto"
        }

        result = agent.run(payload)

        assert result["status"] == "error"
        assert "message" in result

    def test_run_with_default_parameters(self, sample_data):
        """Test run() with default parameters."""
        agent = ForecastingAgent()
        payload = {"data": sample_data}

        result = agent.run(payload)

        assert result["status"] == "success"
        assert len(result["forecast"]) == 30  # Default periods

    def test_run_error_handling(self):
        """Test run() handles errors gracefully."""
        agent = ForecastingAgent()
        payload = {
            "data": np.array([1.0, 2.0, 3.0]),  # Too short
            "periods": 30
        }

        result = agent.run(payload)

        assert result["status"] == "error"
        assert "message" in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_workflow(self, sample_data):
        """Test complete workflow from load to forecast."""
        agent = ForecastingAgent()

        # Load data
        assert agent.load_data(sample_data) is True

        # Forecast with auto model
        forecast = agent.forecast(periods=30, model="auto")
        assert len(forecast["forecast"]) == 30

        # Analyze trend
        trend = agent.analyze_trend(sample_data)
        assert trend["direction"] in ["increasing", "decreasing", "stable"]

        # Validate
        is_valid = agent.validate_forecast(np.array(forecast["forecast"]))
        assert isinstance(is_valid, bool)

    def test_multiple_forecasts_same_agent(self, sample_data):
        """Test generating multiple forecasts with same agent."""
        agent = ForecastingAgent()
        agent.load_data(sample_data)

        # Forecast 1
        result1 = agent.forecast(periods=7, model="arima")
        assert len(result1["forecast"]) == 7

        # Forecast 2 (different model)
        result2 = agent.forecast(periods=14, model="exponential_smoothing")
        assert len(result2["forecast"]) == 14

        # Both should succeed
        assert "forecast" in result1
        assert "forecast" in result2


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
