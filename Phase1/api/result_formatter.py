"""
Result Formatter for Phase 1.3 API.

Responsibilities:
- Format raw agent results into API responses
- Validate result data completeness
- Normalize numerical precision
- Handle missing or partial results
- Error handling for malformed data

Architecture:
- Single responsibility: Result standardization
- Type-safe: 100% type hints
- Error classification: Use custom exceptions
- Logging: All operations logged
- Testable: Pure functions where possible

Usage:
    from Phase1.api.result_formatter import ResultFormatter
    
    formatter = ResultFormatter()
    api_response = formatter.format_analysis_result(
        task_id="task_123",
        raw_result={...}
    )
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from Phase1.utils.errors import ResultNormalizationError

logger = logging.getLogger(__name__)


class ResultFormatter:
    """Format analysis results for API responses."""

    def __init__(self, precision: int = 4) -> None:
        """
        Initialize result formatter.

        Args:
            precision: Decimal precision for floats
        """
        self.precision = precision
        logger.debug(f"ResultFormatter initialized with precision: {precision}")

    def format_analysis_result(
        self,
        task_id: str,
        file_id: str,
        target_variable: str,
        raw_result: Dict[str, Any],
        processing_time_seconds: float
    ) -> Dict[str, Any]:
        """
        Format raw analysis result for API response.

        Args:
            task_id: Unique task identifier
            file_id: Original file ID
            target_variable: Target variable analyzed
            raw_result: Raw result from agent
            processing_time_seconds: Processing duration

        Returns:
            Formatted result suitable for API response

        Raises:
            ResultNormalizationError: If formatting fails
        """
        logger.info(f"Formatting result for task: {task_id}")

        try:
            # Validate raw result
            self._validate_raw_result(raw_result)

            # Extract and format components
            correlation_matrix = self._format_correlation_matrix(
                raw_result.get("correlation_matrix", {})
            )

            model_performance = self._format_model_performance(
                raw_result.get("model_performance", {})
            )

            p_values = self._format_p_values(
                raw_result.get("p_values", {})
            )

            # Build response
            formatted_result = {
                "task_id": task_id,
                "status": "completed",
                "file_id": file_id,
                "target_variable": target_variable,
                "correlation_matrix": correlation_matrix,
                "model_performance": model_performance,
                "p_values": p_values,
                "completed_at": datetime.now().isoformat(),
                "processing_time_seconds": round(processing_time_seconds, 2)
            }

            logger.info(f"Result formatted successfully: {task_id}")
            return formatted_result

        except ResultNormalizationError:
            raise
        except Exception as e:
            error_msg = f"Failed to format result: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ResultNormalizationError(error_msg, field="raw_result")

    def format_error_result(
        self,
        task_id: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Format error result for API response.

        Args:
            task_id: Task identifier
            error_message: Error description

        Returns:
            Error response dictionary
        """
        logger.warning(f"Formatting error result for task: {task_id}")

        return {
            "task_id": task_id,
            "status": "failed",
            "error": "ANALYSIS_FAILED",
            "message": error_message,
            "completed_at": datetime.now().isoformat()
        }

    def _validate_raw_result(self, raw_result: Dict[str, Any]) -> None:
        """
        Validate raw result has required fields.

        Args:
            raw_result: Raw result from agent

        Raises:
            ResultNormalizationError: If validation fails
        """
        logger.debug("Validating raw result structure")

        if not isinstance(raw_result, dict):
            raise ResultNormalizationError(
                "Result must be dictionary",
                field="result_type"
            )

        required_fields = [
            "correlation_matrix",
            "model_performance",
            "p_values"
        ]

        missing_fields = [f for f in required_fields if f not in raw_result]
        if missing_fields:
            raise ResultNormalizationError(
                f"Missing required fields: {missing_fields}",
                field="required_fields",
                details={"missing": missing_fields}
            )

        logger.debug("Raw result validation passed")

    def _format_correlation_matrix(
        self,
        correlation_matrix: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Format correlation matrix with precision.

        Args:
            correlation_matrix: Raw correlation data

        Returns:
            Formatted correlation dictionary

        Raises:
            ResultNormalizationError: If formatting fails
        """
        logger.debug("Formatting correlation matrix")

        if not isinstance(correlation_matrix, dict):
            raise ResultNormalizationError(
                "Correlation matrix must be dictionary",
                field="correlation_matrix"
            )

        formatted = {}
        for variable, correlation in correlation_matrix.items():
            try:
                correlation_value = float(correlation)

                # Validate correlation is in [-1, 1]
                if not (-1.0 <= correlation_value <= 1.0):
                    logger.warning(
                        f"Correlation out of range: {variable}={correlation_value}"
                    )
                    # Clamp to valid range
                    correlation_value = max(-1.0, min(1.0, correlation_value))

                formatted[str(variable)] = round(correlation_value, self.precision)

            except (ValueError, TypeError) as e:
                raise ResultNormalizationError(
                    f"Invalid correlation value for {variable}: {correlation}",
                    field="correlation_matrix",
                    details={"variable": variable, "error": str(e)}
                )

        logger.debug(f"Formatted {len(formatted)} correlations")
        return formatted

    def _format_model_performance(
        self,
        model_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format model performance metrics.

        Args:
            model_performance: Raw performance data

        Returns:
            Formatted performance dictionary
        """
        logger.debug("Formatting model performance")

        if not isinstance(model_performance, dict):
            raise ResultNormalizationError(
                "Model performance must be dictionary",
                field="model_performance"
            )

        formatted = {
            "model_type": str(model_performance.get("model_type", "Unknown")),
        }

        # Format numeric metrics
        numeric_fields = ["r2_score", "rmse", "mae", "mse"]
        for field in numeric_fields:
            if field in model_performance:
                try:
                    value = float(model_performance[field])
                    formatted[field] = round(value, self.precision)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not format {field}: {e}")

        logger.debug("Model performance formatted")
        return formatted

    def _format_p_values(
        self,
        p_values: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Format statistical p-values.

        Args:
            p_values: Raw p-value data

        Returns:
            Formatted p-values dictionary

        Raises:
            ResultNormalizationError: If formatting fails
        """
        logger.debug("Formatting p-values")

        if not isinstance(p_values, dict):
            raise ResultNormalizationError(
                "P-values must be dictionary",
                field="p_values"
            )

        formatted = {}
        for variable, p_value in p_values.items():
            try:
                p_val = float(p_value)

                # Validate p-value is in [0, 1]
                if not (0.0 <= p_val <= 1.0):
                    logger.warning(
                        f"P-value out of range: {variable}={p_val}"
                    )
                    # Clamp to valid range
                    p_val = max(0.0, min(1.0, p_val))

                formatted[str(variable)] = round(p_val, self.precision)

            except (ValueError, TypeError) as e:
                raise ResultNormalizationError(
                    f"Invalid p-value for {variable}: {p_value}",
                    field="p_values",
                    details={"variable": variable, "error": str(e)}
                )

        logger.debug(f"Formatted {len(formatted)} p-values")
        return formatted

    def get_format_summary(self) -> Dict[str, Any]:
        """
        Get formatter configuration summary.

        Returns:
            Summary of formatter settings
        """
        return {
            "precision": self.precision,
            "correlation_range": [-1.0, 1.0],
            "p_value_range": [0.0, 1.0]
        }
