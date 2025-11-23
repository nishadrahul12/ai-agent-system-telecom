"""
Orchestrator Adapter for ForecastingAgent Integration.

Provides seamless integration between Phase 1 Orchestrator and Phase 2 ForecastingAgent.
Handles payload transformation, result mapping, and error management.

Responsibilities:
- Transform orchestrator format → agent format
- Execute ForecastingAgent
- Transform results → orchestrator format
- Map errors appropriately
- Maintain orchestrator compatibility

Architecture:
- Single adapter class
- Minimal overhead
- Full error handling
- Type-safe operations
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from Phase2.agents.forecasting_agent import ForecastingAgent
from Phase2.models.time_series_models import DataValidationError, ForecastError

logger = logging.getLogger(__name__)


class OrchestratorAdapter:
    """
    Adapter connecting Phase 1 Orchestrator with Phase 2 ForecastingAgent.

    Transforms between orchestrator and agent message formats.
    Handles all integration concerns: payload mapping, result formatting, error handling.

    Attributes:
        agent (ForecastingAgent): Wrapped forecasting agent
        name (str): Adapter identifier
        version (str): Adapter version
        task_id (Optional[str]): Current task ID (for tracing)
        last_result (Optional[Dict]): Cache of last result
    """

    def __init__(self, name: str = "forecasting_adapter", version: str = "1.0.0") -> None:
        """
        Initialize orchestrator adapter.

        Args:
            name: Adapter identifier
            version: Adapter version
        """
        self.name = name
        self.version = version
        self.agent = ForecastingAgent()
        self.task_id: Optional[str] = None
        self.last_result: Optional[Dict[str, Any]] = None

        logger.info(f"[{self.name}] Initialized version {self.version}")

    def execute(self, orchestrator_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute forecasting via orchestrator interface.

        Expected orchestrator_payload:
            - task_id: Task identifier (for tracing)
            - data: Historical time-series data
            - periods: Forecast periods (7, 14, or 30)
            - model: Model name (optional, "auto" default)

        Returns:
            Orchestrator-format result with status, forecast, trend, metrics

        Raises:
            None (all errors caught and formatted)
        """
        try:
            # Extract task metadata
            self.task_id = orchestrator_payload.get("task_id", "unknown")
            logger.info(f"[{self.name}] Task {self.task_id}: Starting execution")

            # Transform payload
            agent_payload = self._transform_payload_to_agent(orchestrator_payload)

            # Execute agent
            agent_result = self.agent.run(agent_payload)

            # Transform result
            orchestrator_result = self._transform_result_to_orchestrator(agent_result)

            # Cache result
            self.last_result = orchestrator_result

            logger.info(f"[{self.name}] Task {self.task_id}: Execution complete")
            return orchestrator_result

        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            logger.error(f"[{self.name}] Task {self.task_id}: {error_msg}", exc_info=True)
            return self._format_error_result(error_msg, str(e))

    def _transform_payload_to_agent(self, orch_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform orchestrator payload to agent format.

        Maps orchestrator keys to agent keys and validates required fields.

        Args:
            orch_payload: Orchestrator format payload

        Returns:
            Agent format payload

        Raises:
            ValueError: If required fields missing
        """
        try:
            # Validate required fields
            if "data" not in orch_payload:
                raise ValueError("Missing required field: 'data'")

            # Extract and transform
            agent_payload = {
                "data": orch_payload["data"],
                "periods": orch_payload.get("periods", 30),
                "model": orch_payload.get("model", "auto")
            }

            logger.debug(f"[{self.name}] Payload transformed: periods={agent_payload['periods']}, model={agent_payload['model']}")
            return agent_payload

        except ValueError as e:
            logger.error(f"[{self.name}] Payload transformation failed: {e}")
            return self._format_error_result(f"Payload transformation failed: {str(e)}", str(e))

    def _transform_result_to_orchestrator(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent result to orchestrator format.

        Maps agent result structure to orchestrator result structure.
        Adds metadata and status information.

        Args:
            agent_result: Agent format result

        Returns:
            Orchestrator format result
        """
        try:
            # Build orchestrator result
            orch_result = {
                "task_id": self.task_id,
                "status": agent_result.get("status", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
                "adapter_version": self.version,
                "result": {
                    "forecast": agent_result.get("forecast", []),
                    "confidence_intervals": {
                        "lower": agent_result.get("confidence_interval_lower", []),
                        "upper": agent_result.get("confidence_interval_upper", [])
                    },
                    "trend": agent_result.get("trend", {
                        "direction": "unknown",
                        "slope": 0.0,
                        "strength": 0.0
                    }),
                    "metrics": agent_result.get("metrics", {
                        "mae": 0,
                        "rmse": 0,
                        "mape": 0
                    }),
                    "model_metadata": agent_result.get("metadata", {})
                }
            }

            if agent_result.get("status") == "error":
                orch_result["error"] = agent_result.get("message", "Unknown error")

            logger.debug(f"[{self.name}] Result transformed: status={orch_result['status']}")
            return orch_result

        except Exception as e:
            logger.error(f"[{self.name}] Result transformation failed: {e}")
            return self._format_error_result(f"Result transformation failed: {e}", str(e))

    def _format_error_result(self, error_msg: str, details: str) -> Dict[str, Any]:
        """
        Format error as orchestrator result.

        Args:
            error_msg: User-friendly error message
            details: Technical error details

        Returns:
            Orchestrator format error result
        """
        return {
            "task_id": self.task_id,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "adapter_version": self.version,
            "error": error_msg,
            "details": details,
            "result": {
                "forecast": [],
                "confidence_intervals": {"lower": [], "upper": []},
                "trend": {"direction": "unknown", "slope": 0.0, "strength": 0.0},
                "metrics": {"mae": 0, "rmse": 0, "mape": 0},
                "model_metadata": {}
            }
        }


    def get_last_result(self) -> Optional[Dict[str, Any]]:
        """Get last cached result."""
        return self.last_result

    def reset(self) -> None:
        """Reset adapter state."""
        self.task_id = None
        self.last_result = None
        logger.debug(f"[{self.name}] State reset")


# Export
__all__ = ["OrchestratorAdapter"]
