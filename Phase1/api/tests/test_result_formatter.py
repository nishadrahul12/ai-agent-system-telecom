"""
Unit tests for ResultFormatter.

Test coverage:
- Result formatting
- Validation
- Precision handling
- Edge cases
- Error handling
"""

import unittest
from Phase1.api.result_formatter import ResultFormatter
from Phase1.utils.errors import ResultNormalizationError


class TestResultFormatter(unittest.TestCase):
    """Test suite for ResultFormatter."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.formatter = ResultFormatter(precision=4)
        self.valid_raw_result = {
            "correlation_matrix": {
                "traffic": 0.85,
                "prb_util": 0.72,
                "latency": 0.91
            },
            "model_performance": {
                "model_type": "GradientBoosting",
                "r2_score": 0.89,
                "rmse": 0.15,
                "mae": 0.12
            },
            "p_values": {
                "traffic": 0.001,
                "prb_util": 0.05,
                "latency": 0.0001
            }
        }

    def test_format_valid_result(self) -> None:
        """Test formatting valid result."""
        result = self.formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate",
            raw_result=self.valid_raw_result,
            processing_time_seconds=90.5
        )

        self.assertEqual(result["task_id"], "task_123")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["file_id"], "file_456")
        self.assertIn("correlation_matrix", result)
        self.assertIn("model_performance", result)
        self.assertIn("p_values", result)

    def test_format_result_precision(self) -> None:
        """Test precision handling."""
        result = self.formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate",
            raw_result=self.valid_raw_result,
            processing_time_seconds=90.5
        )

        # Check precision
        traffic_corr = result["correlation_matrix"]["traffic"]
        self.assertEqual(len(str(traffic_corr).split(".")[-1]), 2)  # 4 decimals max

    def test_format_error_result(self) -> None:
        """Test error result formatting."""
        error_result = self.formatter.format_error_result(
            task_id="task_123",
            error_message="Analysis failed due to invalid data"
        )

        self.assertEqual(error_result["status"], "failed")
        self.assertEqual(error_result["task_id"], "task_123")
        self.assertIn("error", error_result)

    def test_validate_missing_fields(self) -> None:
        """Test validation fails for missing fields."""
        invalid_result = {
            "correlation_matrix": {}
            # Missing model_performance and p_values
        }

        with self.assertRaises(ResultNormalizationError):
            self.formatter.format_analysis_result(
                task_id="task_123",
                file_id="file_456",
                target_variable="drop_rate",
                raw_result=invalid_result,
                processing_time_seconds=90.5
            )

    def test_format_correlation_out_of_range(self) -> None:
        """Test handling of out-of-range correlation."""
        raw_result = self.valid_raw_result.copy()
        raw_result["correlation_matrix"]["invalid"] = 1.5  # Out of range

        result = self.formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate",
            raw_result=raw_result,
            processing_time_seconds=90.5
        )

        # Should be clamped to 1.0
        self.assertEqual(result["correlation_matrix"]["invalid"], 1.0)

    def test_format_p_value_out_of_range(self) -> None:
        """Test handling of out-of-range p-value."""
        raw_result = self.valid_raw_result.copy()
        raw_result["p_values"]["invalid"] = 1.5  # Out of range

        result = self.formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate",
            raw_result=raw_result,
            processing_time_seconds=90.5
        )

        # Should be clamped to 1.0
        self.assertEqual(result["p_values"]["invalid"], 1.0)

    def test_format_invalid_correlation_type(self) -> None:
        """Test error handling for invalid correlation type."""
        raw_result = self.valid_raw_result.copy()
        raw_result["correlation_matrix"]["invalid"] = "not_a_number"

        with self.assertRaises(ResultNormalizationError):
            self.formatter.format_analysis_result(
                task_id="task_123",
                file_id="file_456",
                target_variable="drop_rate",
                raw_result=raw_result,
                processing_time_seconds=90.5
            )

    def test_format_result_with_processing_time(self) -> None:
        """Test processing time is included and formatted."""
        result = self.formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate",
            raw_result=self.valid_raw_result,
            processing_time_seconds=90.12345
        )

        self.assertAlmostEqual(result["processing_time_seconds"], 90.12, places=2)

    def test_formatter_summary(self) -> None:
        """Test formatter configuration summary."""
        summary = self.formatter.get_format_summary()

        self.assertEqual(summary["precision"], 4)
        self.assertEqual(summary["correlation_range"], [-1.0, 1.0])
        self.assertEqual(summary["p_value_range"], [0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
