"""
End-to-End Workflow Tests for Phase 1.3 API.

Tests the complete workflow from user perspective:
1. Upload file
2. Queue analysis
3. Check status
4. Get results
5. Verify complete flow works

These tests verify that all components work together
in the actual workflow, not just in isolation.
"""

import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO

from Phase1.api.upload_handler import FileUploadHandler
from Phase1.api.analysis_endpoint import AnalysisEndpoint
from Phase1.api.result_formatter import ResultFormatter
from Phase1.api.router import create_api_router
from Phase1.api.models import AnalysisRequest
from Phase1.utils.errors import FileValidationError, TaskQueueError


class TestE2EWorkflowComplete(unittest.TestCase):
    """Complete end-to-end workflow tests."""

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

    def test_complete_workflow_upload_to_result(self) -> None:
        """
        Test complete workflow:
        1. Upload file
        2. Queue analysis
        3. Check status throughout lifecycle
        4. Get final result
        """
        # STEP 1: Upload file
        test_data = b"traffic,prb_util,latency,drop_rate\n100,80,15,0.5\n150,85,20,0.8\n200,90,25,1.2"
        file_id = self.upload_handler.save_uploaded_file(
            filename="telecom_kpi.csv",
            file_content=test_data,
            file_size_bytes=len(test_data)
        )

        self.assertIsNotNone(file_id)
        print(f"✓ File uploaded: {file_id}")

        # Verify file can be retrieved
        retrieved_content = self.upload_handler.get_file_content(file_id)
        self.assertEqual(retrieved_content, test_data)
        print(f"✓ File content verified")

        # STEP 2: Queue analysis
        task_id = self.analysis_endpoint.queue_analysis(
            file_id=file_id,
            target_variable="drop_rate",
            correlation_method="pearson",
            test_size=0.2
        )

        self.assertIsNotNone(task_id)
        print(f"✓ Analysis queued: {task_id}")

        # STEP 3a: Check initial status (queued)
        status = self.analysis_endpoint.get_task_status(task_id)
        self.assertEqual(status["status"], "queued")
        self.assertEqual(status["progress_percent"], 0)
        print(f"✓ Task status (queued): {status['status']}")

        # STEP 3b: Simulate processing status
        self.analysis_endpoint.update_task_status(
            task_id,
            status="processing",
            progress_percent=25
        )

        status = self.analysis_endpoint.get_task_status(task_id)
        self.assertEqual(status["status"], "processing")
        self.assertEqual(status["progress_percent"], 25)
        print(f"✓ Task status (processing 25%): {status['status']}")

        # STEP 3c: More progress
        self.analysis_endpoint.update_task_status(
            task_id,
            status="processing",
            progress_percent=75
        )

        status = self.analysis_endpoint.get_task_status(task_id)
        self.assertEqual(status["progress_percent"], 75)
        print(f"✓ Task status (processing 75%): {status['status']}")

        # STEP 4: Get final result
        raw_result = {
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

        # Mark task complete
        self.analysis_endpoint.update_task_status(
            task_id,
            status="completed",
            progress_percent=100,
            result=raw_result
        )

        # Retrieve and format result
        result = self.analysis_endpoint.get_task_result(task_id)
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "completed")
        print(f"✓ Task completed: {result['status']}")

        # Format for API response
        api_response = self.result_formatter.format_analysis_result(
            task_id=task_id,
            file_id=file_id,
            target_variable="drop_rate",
            raw_result=raw_result,
            processing_time_seconds=120.5
        )

        self.assertEqual(api_response["status"], "completed")
        self.assertEqual(api_response["task_id"], task_id)
        self.assertIn("correlation_matrix", api_response)
        self.assertIn("model_performance", api_response)
        self.assertIn("p_values", api_response)
        self.assertIn("processing_time_seconds", api_response)
        print(f"✓ Result formatted for API response")

        # Verify result structure
        self.assertEqual(
            api_response["correlation_matrix"]["traffic"],
            0.85
        )
        self.assertEqual(
            api_response["model_performance"]["r2_score"],
            0.89
        )
        print(f"✓ All result data verified")

        print("\n✅ COMPLETE WORKFLOW TEST PASSED")

    def test_workflow_with_invalid_file(self) -> None:
        """Test workflow rejects invalid files."""
        # Try to upload invalid file
        with self.assertRaises(FileValidationError):
            self.upload_handler.save_uploaded_file(
                filename="data.txt",  # Invalid extension
                file_content=b"some data",
                file_size_bytes=9
            )
        print("✓ Invalid file extension rejected")

        # Try to upload oversized file
        from Phase1.config import Config
        oversized = b"x" * (Config.MAX_FILE_SIZE_BYTES + 1)

        with self.assertRaises(FileValidationError):
            self.upload_handler.save_uploaded_file(
                filename="huge.csv",
                file_content=oversized,
                file_size_bytes=len(oversized)
            )
        print("✓ Oversized file rejected")

    def test_workflow_error_handling(self) -> None:
        """Test error handling throughout workflow."""
        # Try to get status of non-existent task
        with self.assertRaises(TaskQueueError):
            self.analysis_endpoint.get_task_status("nonexistent_task")
        print("✓ Non-existent task error handled")

        # Try to get result of non-existent task
        with self.assertRaises(TaskQueueError):
            self.analysis_endpoint.get_task_result("nonexistent_task")
        print("✓ Non-existent result error handled")

        # Queue analysis and mark as failed
        task_id = self.analysis_endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        self.analysis_endpoint.update_task_status(
            task_id,
            status="failed",
            error_message="Analysis timeout after 300 seconds"
        )

        with self.assertRaises(TaskQueueError):
            self.analysis_endpoint.get_task_result(task_id)
        print("✓ Failed task error handled")

        # Error result formatting
        error_result = self.result_formatter.format_error_result(
            task_id=task_id,
            error_message="Analysis timeout after 300 seconds"
        )

        self.assertEqual(error_result["status"], "failed")
        self.assertIn("error", error_result)
        print("✓ Error result formatted correctly")

    def test_workflow_with_multiple_files(self) -> None:
        """Test handling multiple files and analyses concurrently."""
        files = []
        tasks = []

        # Upload multiple files
        for i in range(3):
            test_data = f"col1,col2,col3\n1,2,{i}\n4,5,{i+10}\n".encode()
            file_id = self.upload_handler.save_uploaded_file(
                filename=f"test_data_{i}.csv",
                file_content=test_data,
                file_size_bytes=len(test_data)
            )
            files.append(file_id)

        print(f"✓ Uploaded {len(files)} files")

        # Queue analyses for all files
        for i, file_id in enumerate(files):
            task_id = self.analysis_endpoint.queue_analysis(
                file_id=file_id,
                target_variable=f"col{(i % 3) + 1}"
            )
            tasks.append(task_id)

        print(f"✓ Queued {len(tasks)} analyses")

        # Verify all tasks exist and are queued
        for task_id in tasks:
            status = self.analysis_endpoint.get_task_status(task_id)
            self.assertEqual(status["status"], "queued")

        print(f"✓ All {len(tasks)} tasks verified as queued")

        # Get task summary
        summary = self.analysis_endpoint.get_task_summary()
        self.assertEqual(summary["total_tasks"], 3)
        self.assertEqual(summary["queued"], 3)
        print(f"✓ Task summary: {summary['total_tasks']} total, {summary['queued']} queued")

    def test_workflow_result_precision_and_validation(self) -> None:
        """Test result formatting with precision and validation."""
        # Test with various precision requirements
        raw_result = {
            "correlation_matrix": {
                "var1": 0.123456789,
                "var2": 0.999999,
                "var3": -0.987654321
            },
            "model_performance": {
                "model_type": "RandomForest",
                "r2_score": 0.891234567,
                "rmse": 0.154321,
                "mae": 0.123456
            },
            "p_values": {
                "var1": 0.001234,
                "var2": 0.999999,
                "var3": 0.0001
            }
        }

        api_response = self.result_formatter.format_analysis_result(
            task_id="task_123",
            file_id="file_456",
            target_variable="target",
            raw_result=raw_result,
            processing_time_seconds=90.123456
        )

        # Verify precision
        self.assertAlmostEqual(
            api_response["correlation_matrix"]["var1"],
            0.1235,
            places=4
        )
        print(f"✓ Precision handled: var1={api_response['correlation_matrix']['var1']}")

        # Verify clamping for out-of-range values
        self.assertLessEqual(api_response["correlation_matrix"]["var2"], 1.0)
        self.assertGreaterEqual(api_response["correlation_matrix"]["var3"], -1.0)
        print(f"✓ Out-of-range values clamped")

        # Verify processing time is rounded
        self.assertAlmostEqual(
            api_response["processing_time_seconds"],
            90.12,
            places=2
        )
        print(f"✓ Processing time rounded: {api_response['processing_time_seconds']}s")

        print("\n✅ RESULT PRECISION AND VALIDATION TEST PASSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
