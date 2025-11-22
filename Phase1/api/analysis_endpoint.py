"""
Analysis Endpoint for Phase 1.3 API.

Responsibilities:
- Queue analysis tasks with orchestrator
- Track task status and progress
- Manage task lifecycle (pending → processing → completed/failed)
- Return analysis results
- Handle errors and timeouts

Architecture:
- Single responsibility: Analysis task management
- Type-safe: 100% type hints
- Error classification: Use custom exceptions
- Logging: All operations logged
- Testable: Pure functions where possible

Task Lifecycle:
    1. POST /api/correlation/analyze → Queue task
    2. Task queued with ID
    3. GET /api/correlation/status/{task_id} → Check progress
    4. GET /api/correlation/result/{task_id} → Get results (when complete)

Usage:
    from Phase1.api.analysis_endpoint import AnalysisEndpoint
    
    endpoint = AnalysisEndpoint(orchestrator)
    task_id = endpoint.queue_analysis(
        file_id="file_123",
        target_variable="drop_rate"
    )
    
    status = endpoint.get_task_status(task_id)
    result = endpoint.get_task_result(task_id)
"""

import uuid
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from Phase1.config import Config
from Phase1.utils.errors import TaskQueueError, AgentInitializationError

logger = logging.getLogger(__name__)


class TaskMetadata:
    """Metadata for a single analysis task."""

    def __init__(
        self,
        task_id: str,
        file_id: str,
        target_variable: str,
        correlation_method: str = "pearson",
        test_size: float = 0.2
    ) -> None:
        """
        Initialize task metadata.

        Args:
            task_id: Unique task identifier
            file_id: ID of file to analyze
            target_variable: Target variable for analysis
            correlation_method: Correlation method (pearson/spearman)
            test_size: Train/test split ratio
        """
        self.task_id = task_id
        self.file_id = file_id
        self.target_variable = target_variable
        self.correlation_method = correlation_method
        self.test_size = test_size
        self.status = "queued"
        self.progress_percent = 0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.retry_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "task_id": self.task_id,
            "file_id": self.file_id,
            "target_variable": self.target_variable,
            "correlation_method": self.correlation_method,
            "test_size": self.test_size,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }


class AnalysisEndpoint:
    """Manage analysis tasks and orchestrator integration."""

    def __init__(self, orchestrator: Any) -> None:
        """
        Initialize analysis endpoint.

        Args:
            orchestrator: Phase 0 orchestrator instance
        """
        self.orchestrator = orchestrator
        self.tasks: Dict[str, TaskMetadata] = {}
        logger.info("AnalysisEndpoint initialized")

    def queue_analysis(
        self,
        file_id: str,
        target_variable: str,
        correlation_method: str = "pearson",
        test_size: float = 0.2
    ) -> str:
        """
        Queue a new analysis task.

        Args:
            file_id: ID of uploaded file
            target_variable: Target variable for analysis
            correlation_method: Correlation method (pearson/spearman)
            test_size: Train/test split ratio

        Returns:
            Task ID for tracking

        Raises:
            TaskQueueError: If queuing fails
        """
        logger.info(f"Queuing analysis for file: {file_id}, target: {target_variable}")

        try:
            # Generate task ID
            task_id = self._generate_task_id()

            # Create metadata
            metadata = TaskMetadata(
                task_id=task_id,
                file_id=file_id,
                target_variable=target_variable,
                correlation_method=correlation_method,
                test_size=test_size
            )

            # Store metadata
            self.tasks[task_id] = metadata
            logger.debug(f"Task metadata stored: {task_id}")

            # Queue with orchestrator
            payload = {
                "task_id": task_id,
                "file_id": file_id,
                "target_variable": target_variable,
                "correlation_method": correlation_method,
                "test_size": test_size
            }

            result = self.orchestrator.execute_task(
                agent_id=Config.CORRELATION_AGENT_ID,
                payload=payload
            )

            if not result or result.get("status") != "queued":
                error_msg = f"Orchestrator failed to queue task: {result}"
                logger.error(error_msg)
                raise TaskQueueError(error_msg, task_id)

            logger.info(f"Task queued successfully: {task_id}")
            return task_id

        except TaskQueueError:
            raise
        except Exception as e:
            error_msg = f"Failed to queue analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise TaskQueueError(error_msg)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get current status of a task.

        Args:
            task_id: Task identifier

        Returns:
            Status dictionary with progress

        Raises:
            TaskQueueError: If task not found
        """
        logger.debug(f"Getting status for task: {task_id}")

        if task_id not in self.tasks:
            error_msg = f"Task not found: {task_id}"
            logger.warning(error_msg)
            raise TaskQueueError(error_msg, task_id)

        metadata = self.tasks[task_id]

        # Build status response
        status_dict = {
            "task_id": task_id,
            "status": metadata.status,
            "progress_percent": metadata.progress_percent,
            "created_at": metadata.created_at.isoformat(),
            "started_at": metadata.started_at.isoformat() if metadata.started_at else None,
            "message": self._get_status_message(metadata)
        }

        logger.debug(f"Status retrieved: {task_id}, status: {metadata.status}")
        return status_dict

    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results of completed task.

        Args:
            task_id: Task identifier

        Returns:
            Result dictionary if completed, None if still processing

        Raises:
            TaskQueueError: If task failed or not found
        """
        logger.debug(f"Retrieving results for task: {task_id}")

        if task_id not in self.tasks:
            error_msg = f"Task not found: {task_id}"
            logger.warning(error_msg)
            raise TaskQueueError(error_msg, task_id)

        metadata = self.tasks[task_id]

        # Check status
        if metadata.status == "failed":
            error_msg = f"Task failed: {metadata.error_message}"
            logger.warning(error_msg)
            raise TaskQueueError(error_msg, task_id)

        if metadata.status != "completed":
            logger.debug(f"Task not completed yet: {task_id}, status: {metadata.status}")
            return None

        # Include status in result
        result_with_status = {
            "status": "completed",
            "task_id": task_id,
            **(metadata.result or {})
        }

        logger.info(f"Results retrieved for task: {task_id}")
        return result_with_status


    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress_percent: int = 0,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update task status (called by orchestrator/agent).

        Args:
            task_id: Task identifier
            status: New status (queued, processing, completed, failed)
            progress_percent: Progress percentage (0-100)
            result: Result data if completed
            error_message: Error message if failed
        """
        logger.debug(f"Updating task status: {task_id}, status: {status}")

        if task_id not in self.tasks:
            logger.warning(f"Task not found for update: {task_id}")
            return

        metadata = self.tasks[task_id]
        metadata.status = status
        metadata.progress_percent = progress_percent

        if status == "processing" and not metadata.started_at:
            metadata.started_at = datetime.now()
            logger.debug(f"Task started: {task_id}")

        if status == "completed":
            metadata.completed_at = datetime.now()
            metadata.result = result
            logger.info(f"Task completed: {task_id}")

        if status == "failed":
            metadata.completed_at = datetime.now()
            metadata.error_message = error_message
            logger.error(f"Task failed: {task_id}, error: {error_message}")

    def cleanup_old_tasks(self, hours: int = 24) -> int:
        """
        Remove old completed tasks from memory.

        Args:
            hours: Remove tasks older than N hours

        Returns:
            Number of tasks cleaned up
        """
        logger.debug(f"Cleaning up tasks older than {hours} hours")

        cutoff_time = datetime.now() - timedelta(hours=hours)
        tasks_to_delete = []

        for task_id, metadata in self.tasks.items():
            if metadata.completed_at and metadata.completed_at < cutoff_time:
                tasks_to_delete.append(task_id)

        for task_id in tasks_to_delete:
            del self.tasks[task_id]
            logger.debug(f"Cleaned up task: {task_id}")

        logger.info(f"Cleaned up {len(tasks_to_delete)} tasks")
        return len(tasks_to_delete)

    def get_task_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tasks.

        Returns:
            Dictionary with task counts by status
        """
        summary = {
            "total_tasks": len(self.tasks),
            "queued": sum(1 for m in self.tasks.values() if m.status == "queued"),
            "processing": sum(1 for m in self.tasks.values() if m.status == "processing"),
            "completed": sum(1 for m in self.tasks.values() if m.status == "completed"),
            "failed": sum(1 for m in self.tasks.values() if m.status == "failed")
        }
        logger.debug(f"Task summary: {summary}")
        return summary

    def _generate_task_id(self) -> str:
        """Generate unique task identifier."""
        return str(uuid.uuid4())

    def _get_status_message(self, metadata: TaskMetadata) -> str:
        """Get human-readable status message."""
        messages = {
            "queued": "Task queued, waiting to start",
            "processing": f"Processing correlation analysis ({metadata.progress_percent}%)",
            "completed": "Analysis completed successfully",
            "failed": f"Analysis failed: {metadata.error_message}"
        }
        return messages.get(metadata.status, "Unknown status")
