"""
Unit tests for AnalysisEndpoint.

Test coverage:
- Task queuing
- Status tracking
- Result retrieval
- Task cleanup
- Error handling
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from Phase1.api.analysis_endpoint import AnalysisEndpoint, TaskMetadata
from Phase1.utils.errors import TaskQueueError


class TestTaskMetadata(unittest.TestCase):
    """Test suite for TaskMetadata."""

    def test_metadata_creation(self) -> None:
        """Test task metadata initialization."""
        metadata = TaskMetadata(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate"
        )

        self.assertEqual(metadata.task_id, "task_123")
        self.assertEqual(metadata.file_id, "file_456")
        self.assertEqual(metadata.status, "queued")
        self.assertEqual(metadata.progress_percent, 0)

    def test_metadata_to_dict(self) -> None:
        """Test metadata serialization."""
        metadata = TaskMetadata(
            task_id="task_123",
            file_id="file_456",
            target_variable="drop_rate"
        )

        metadata_dict = metadata.to_dict()
        self.assertEqual(metadata_dict["task_id"], "task_123")
        self.assertEqual(metadata_dict["status"], "queued")
        self.assertIn("created_at", metadata_dict)


class TestAnalysisEndpoint(unittest.TestCase):
    """Test suite for AnalysisEndpoint."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_orchestrator = MagicMock()
        self.mock_orchestrator.execute_task.return_value = {"status": "queued"}
        self.endpoint = AnalysisEndpoint(self.mock_orchestrator)

    def test_queue_analysis_success(self) -> None:
        """Test successful task queuing."""
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.endpoint.tasks)

    def test_queue_analysis_orchestrator_called(self) -> None:
        """Test orchestrator is called correctly."""
        self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        self.mock_orchestrator.execute_task.assert_called_once()

    def test_queue_analysis_orchestrator_fails(self) -> None:
        """Test error handling when orchestrator fails."""
        self.mock_orchestrator.execute_task.return_value = {"status": "error"}

        with self.assertRaises(TaskQueueError):
            self.endpoint.queue_analysis(
                file_id="file_123",
                target_variable="drop_rate"
            )

    def test_get_task_status_success(self) -> None:
        """Test retrieving task status."""
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        status = self.endpoint.get_task_status(task_id)
        self.assertEqual(status["task_id"], task_id)
        self.assertEqual(status["status"], "queued")

    def test_get_task_status_not_found(self) -> None:
        """Test error when task not found."""
        with self.assertRaises(TaskQueueError):
            self.endpoint.get_task_status("nonexistent_task")

    def test_update_task_status(self) -> None:
        """Test updating task status."""
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        self.endpoint.update_task_status(
            task_id,
            status="processing",
            progress_percent=50
        )

        status = self.endpoint.get_task_status(task_id)
        self.assertEqual(status["status"], "processing")
        self.assertEqual(status["progress_percent"], 50)

    def test_get_task_result_not_completed(self) -> None:
        """Test result retrieval for incomplete task."""
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        result = self.endpoint.get_task_result(task_id)
        self.assertIsNone(result)

    def test_get_task_result_completed(self) -> None:
        """Test result retrieval for completed task."""
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        result_data = {
            "correlation_matrix": {"traffic": 0.85},
            "model_performance": {"r2_score": 0.89}
        }

        self.endpoint.update_task_status(
            task_id,
            status="completed",
            result=result_data
        )

        result = self.endpoint.get_task_result(task_id)
        
        # Verify result contains original data plus status and task_id
        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["task_id"], task_id)
        self.assertEqual(result["correlation_matrix"], result_data["correlation_matrix"])
        self.assertEqual(result["model_performance"], result_data["model_performance"])


    def test_get_task_result_failed(self) -> None:
        """Test error when retrieving failed task result."""
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        self.endpoint.update_task_status(
            task_id,
            status="failed",
            error_message="Analysis failed"
        )

        with self.assertRaises(TaskQueueError):
            self.endpoint.get_task_result(task_id)

    def test_cleanup_old_tasks(self) -> None:
        """Test cleanup of old completed tasks."""
        # Create and complete a task
        task_id = self.endpoint.queue_analysis(
            file_id="file_123",
            target_variable="drop_rate"
        )

        self.endpoint.update_task_status(task_id, status="completed")

        # Manually set completed time to 25 hours ago
        self.endpoint.tasks[task_id].completed_at = (
            datetime.now() - timedelta(hours=25)
        )

        # Clean up tasks older than 24 hours
        cleaned = self.endpoint.cleanup_old_tasks(hours=24)
        self.assertEqual(cleaned, 1)
        self.assertNotIn(task_id, self.endpoint.tasks)

    def test_get_task_summary(self) -> None:
        """Test task summary statistics."""
        # Queue multiple tasks with different statuses
        task1 = self.endpoint.queue_analysis(
            file_id="file_1",
            target_variable="drop_rate"
        )
        task2 = self.endpoint.queue_analysis(
            file_id="file_2",
            target_variable="latency"
        )

        self.endpoint.update_task_status(task1, status="processing")
        self.endpoint.update_task_status(task2, status="completed")

        summary = self.endpoint.get_task_summary()
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["processing"], 1)
        self.assertEqual(summary["completed"], 1)


if __name__ == "__main__":
    unittest.main()
