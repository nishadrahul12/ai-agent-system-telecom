"""
Task Manager: FIFO queue-based task execution engine.

Manages task lifecycle with serialized (non-parallel) execution:
    - Queue tasks (with unique IDs)
    - Execute tasks one-at-a-time (FIFO)
    - Track task status (pending → running → completed/error)
    - Persist task state to database

Architecture:
    - In-memory queue for immediate execution
    - Database persistence for recovery
    - Status tracking throughout lifecycle
    - Error handling and retry logic

Usage:
    manager = TaskManager(db_manager)
    task_id = manager.queue_task(agent_id="agent_001", payload={...})
    result = manager.get_task_result(task_id)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 120  # seconds
MAX_RETRIES = 3


class TaskManager:
    """
    Manages task queue and serialized execution.
    
    Attributes:
        _queue (list): In-memory task queue
        _results (dict): Task results cache
        _db_manager: Database connection for persistence
    """
    
    def __init__(self, db_manager: Optional[any] = None) -> None:
        """
        Initialize task manager.
        
        Args:
            db_manager (Optional[any]): Database manager for persistence
        """
        self._queue: list = []
        self._results: Dict[str, Dict[str, Any]] = {}
        self._db_manager = db_manager
        logger.info("TaskManager initialized")
    
    def queue_task(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        priority: int = 0,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> str:
        """
        Add a task to the execution queue.
        
        Args:
            agent_id (str): Target agent identifier
            payload (Dict[str, Any]): Task input data
            priority (int): Task priority (higher = sooner). Defaults to 0
            timeout (int): Execution timeout in seconds. Defaults to 120
            
        Returns:
            str: Unique task ID
            
        Raises:
            ValueError: If agent_id or payload invalid
            
        Example:
            >>> task_id = manager.queue_task(
            ...     agent_id="correlation_001",
            ...     payload={"file_id": "file_123", "target": "signal_strength"}
            ... )
            >>> print(f"Queued task: {task_id}")
        """
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be non-empty string")
        
        if not isinstance(payload, dict):
            raise ValueError("payload must be dictionary")
        
        task_id: str = str(uuid4())
        task: Dict[str, Any] = {
            "task_id": task_id,
            "agent_id": agent_id,
            "payload": payload,
            "status": "pending",
            "priority": priority,
            "timeout": timeout,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "retry_count": 0,
        }
        
        self._queue.append(task)
        # Sort by priority (descending)
        self._queue.sort(key=lambda t: t["priority"], reverse=True)
        
        logger.info(f"Queued task {task_id} for agent {agent_id}")
        
        # Persist to database if available
        if self._db_manager:
            try:
                self._db_manager.insert_task(
                    task_id=task_id,
                    agent_name=agent_id,
                    status="pending",
                    payload=payload,
                )
            except Exception as e:
                logger.error(f"Failed to persist task to DB: {e}")
        
        return task_id
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve next task from queue without removing it.
        
        Returns:
            Optional[Dict]: Next task if queue not empty, None otherwise
        """
        if self._queue:
            return self._queue[0]
        return None
    
    def start_task(self, task_id: str) -> bool:
        """
        Mark task as running.
        
        Args:
            task_id (str): Task identifier
            
        Returns:
            bool: True if successful, False if task not found
        """
        task = next((t for t in self._queue if t["task_id"] == task_id), None)
        
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        task["status"] = "running"
        task["started_at"] = datetime.utcnow()
        
        logger.info(f"Started task: {task_id}")
        return True
    
    def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
    ) -> bool:
        """
        Mark task as completed with result.
        
        Args:
            task_id (str): Task identifier
            result (Dict[str, Any]): Execution result
            
        Returns:
            bool: True if successful, False if task not found
        """
        task_index = next(
            (i for i, t in enumerate(self._queue) if t["task_id"] == task_id),
            None
        )
        
        if task_index is None:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        task = self._queue[task_index]
        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow()
        
        # Cache result
        self._results[task_id] = result
        
        # Remove from queue
        self._queue.pop(task_index)
        
        logger.info(f"Completed task: {task_id}")
        
        # Persist to database if available
        if self._db_manager:
            try:
                self._db_manager.update_task_status(
                    task_id=task_id,
                    status="completed",
                )
            except Exception as e:
                logger.error(f"Failed to update task in DB: {e}")
        
        return True
    
    def fail_task(
        self,
        task_id: str,
        error_message: str,
        retry: bool = True,
    ) -> bool:
        """
        Mark task as failed with error.
        
        Args:
            task_id (str): Task identifier
            error_message (str): Error description
            retry (bool): Whether to retry. Defaults to True
            
        Returns:
            bool: True if successful, False if task not found
        """
        task = next((t for t in self._queue if t["task_id"] == task_id), None)
        
        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False
        
        # Retry logic
        if retry and task["retry_count"] < MAX_RETRIES:
            task["retry_count"] += 1
            task["status"] = "pending"
            task["started_at"] = None
            logger.warning(
                f"Retrying task {task_id} (attempt {task['retry_count']}/{MAX_RETRIES})"
            )
            return True
        
        # Mark as failed
        task["status"] = "error"
        task["completed_at"] = datetime.utcnow()
        task["error_message"] = error_message
        
        self._results[task_id] = {
            "status": "error",
            "output": None,
            "error_message": error_message,
        }
        
        logger.error(f"Failed task {task_id}: {error_message}")
        
        # Persist to database if available
        if self._db_manager:
            try:
                self._db_manager.update_task_status(
                    task_id=task_id,
                    status="error",
                    error_message=error_message,
                )
            except Exception as e:
                logger.error(f"Failed to update task error in DB: {e}")
        
        return True
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution result of completed task.
        
        Args:
            task_id (str): Task identifier
            
        Returns:
            Optional[Dict]: Result if found, None otherwise
        """
        return self._results.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get current status of a task.
        
        Args:
            task_id (str): Task identifier
            
        Returns:
            Optional[str]: Status ('pending', 'running', 'completed', 'error')
        """
        task = next((t for t in self._queue if t["task_id"] == task_id), None)
        
        if task:
            return task["status"]
        
        # Check results cache
        if task_id in self._results:
            return self._results[task_id].get("status")
        
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get overall queue status.
        
        Returns:
            Dict[str, Any]: Queue statistics including:
                - total_queued (int): Tasks waiting
                - total_results (int): Completed tasks cached
                - queue_details (list): Current queue tasks
        """
        status_counts = {}
        for task in self._queue:
            s = task["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        
        return {
            "total_queued": len(self._queue),
            "total_results_cached": len(self._results),
            "status_breakdown": status_counts,
            "next_task_id": self._queue[0]["task_id"] if self._queue else None,
        }
