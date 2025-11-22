"""
Integration tests for Phase 1.3 API.

Test complete workflow:
- File upload → Analysis queuing → Status tracking → Result retrieval
- Error handling throughout pipeline
- Orchestrator integration
- End-to-end flow
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime

from Phase1.api.router import create_api_router
from Phase1.api.upload_handler import FileUploadHandler
from Phase1.api.analysis_endpoint import AnalysisEndpoint
from Phase1.api.result_formatter import ResultFormatter
from Phase1.api.models import AnalysisRequest


class TestE2EWorkflow(unittest.TestCase):
    """Integration tests for end-to-end workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_orchestrator = MagicMock()
        self.mock_orchestrator.execute_task.return_value = {"status": "queued"}
        
        self.upload_handler = FileUploadHandler()
        self.analysis_endpoint = AnalysisEndpoint(self.mock_orchestrator)
        self.result_formatter = ResultFormatter()
        self.router = create_api_router(
            self.mock_orchestrator,
            self.upload_handler,
            self.analysis_endpoint,
            self.result_formatter
        )

    def test_upload_to_analysis_flow(self) -> None:
        """Test upload followed by analysis queue."""
        # Step 1: Upload file
        test_content = b"col1,col2,col3\n1,2,3\n4,5,6"
        file_id = self.upload_handler.save_uploaded_file(
            filename="test_data.csv",
            file_content=test_content,
            file_size_bytes=len(test_content)
        )

        self.assertIsNotNone(file_id)

        # Step 2: Queue analysis
        task_id = self.analysis_endpoint.queue_analysis(
            file_id=file_id,
            target_variable="col1"
        )

        self.assertIsNotNone(task_id)

        # Step 3: Check status
        status = self.analysis_endpoint.get_task_status(task_id)
        self.assertEqual(status["status"], "queued")

    def test_analysis_lifecycle(self) -> None:
        """Test complete analysis lifecycle."""
        # Queue analysis
        task_id = self.analysis_endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        # Simulate processing
        self.analysis_endpoint.update_task_status(
            task_id,
            status="processing",
            progress_percent=50
        )

        status = self.analysis_endpoint.get_task_status(task_id)
        self.assertEqual(status["status"], "processing")
        self.assertEqual(status["progress_percent"], 50)

        # Simulate completion
        result_data = {
            "correlation_matrix": {"traffic": 0.85},
            "model_performance": {"r2_score": 0.89, "model_type": "GradientBoosting"},
            "p_values": {"traffic": 0.001}
        }

        self.analysis_endpoint.update_task_status(
            task_id,
            status="completed",
            progress_percent=100,
            result=result_data
        )

        # Get result
        result = self.analysis_endpoint.get_task_result(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "completed")

    def test_result_formatting(self) -> None:
        """Test result formatting for API response."""
        raw_result = {
            "correlation_matrix": {"traffic": 0.85, "latency": 0.91},
            "model_performance": {
                "model_type": "GradientBoosting",
                "r2_score": 0.89,
                "rmse": 0.15
            },
            "p_values": {"traffic": 0.001, "latency": 0.0001}
        }

        formatted = self.result_formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate",
            raw_result=raw_result,
            processing_time_seconds=90.5
        )

        self.assertEqual(formatted["task_id"], "task_123")
        self.assertEqual(formatted["status"], "completed")
        self.assertIn("correlation_matrix", formatted)
        self.assertIn("model_performance", formatted)
        self.assertIn("p_values", formatted)

    def test_error_result_formatting(self) -> None:
        """Test error result formatting."""
        error_result = self.result_formatter.format_error_result(
            task_id="task_123",
            error_message="Analysis timeout"
        )

        self.assertEqual(error_result["status"], "failed")
        self.assertEqual(error_result["task_id"], "task_123")

    def test_router_endpoints_exist(self) -> None:
        """Test that router has all required endpoints."""
        routes = [route.path for route in self.router.routes]

        self.assertIn("/correlation/upload", routes)
        self.assertIn("/correlation/analyze", routes)
        self.assertIn("/correlation/status/{task_id}", routes)
        self.assertIn("/correlation/result/{task_id}", routes)
        self.assertIn("/health/detailed", routes)


if __name__ == "__main__":
    unittest.main()
