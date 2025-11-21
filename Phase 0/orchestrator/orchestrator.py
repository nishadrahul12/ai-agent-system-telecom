"""
Orchestrator: Main coordinator for multi-agent system.

Central hub orchestrating:
    - Agent initialization and registration
    - Task queuing and execution
    - Memory and state management
    - Safety and trust validation
    - Database persistence
    - API integration

This is the PRIMARY ENTRY POINT for the entire system.

Usage:
    orchestrator = Orchestrator()
    orchestrator.initialize()
    result = orchestrator.execute_task(
        agent_id="correlation_001",
        payload={"file_id": "file_123"}
    )
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator coordinating all system components.
    
    Responsibilities:
        - Initialize all modules (agents, database, memory)
        - Queue and route tasks
        - Execute agents in FIFO order
        - Integrate safety checks
        - Manage system state
    
    Attributes:
        registry: Agent registry
        task_manager: Task queue manager
        db_manager: Database connection
        memory_manager: In-memory cache
        safety_guard: Input validation
        _initialized (bool): System initialization state
    """
    
    def __init__(
        self,
        registry: Optional[any] = None,
        task_manager: Optional[any] = None,
        db_manager: Optional[any] = None,
        memory_manager: Optional[any] = None,
        safety_guard: Optional[any] = None,
    ) -> None:
        """
        Initialize orchestrator with dependencies.
        
        Args:
            registry: AgentRegistry instance
            task_manager: TaskManager instance
            db_manager: Database manager
            memory_manager: Memory manager
            safety_guard: Safety validation module
        """
        self.registry = registry
        self.task_manager = task_manager
        self.db_manager = db_manager
        self.memory_manager = memory_manager
        self.safety_guard = safety_guard
        self._initialized = False
        
        logger.info("Orchestrator created")
    
    def initialize(self) -> bool:
        """
        Initialize all system components.
        
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            RuntimeError: If initialization fails
            
        Example:
            >>> orchestrator = Orchestrator(...)
            >>> if orchestrator.initialize():
            ...     print("System ready")
        """
        try:
            logger.info("Initializing orchestrator...")
            
            # Initialize database
            if self.db_manager:
                self.db_manager.initialize()
                logger.info("Database initialized")
            
            # Initialize memory
            if self.memory_manager:
                self.memory_manager.initialize()
                logger.info("Memory manager initialized")
            
            # Initialize safety guard
            if self.safety_guard:
                self.safety_guard.initialize()
                logger.info("Safety guard initialized")
            
            self._initialized = True
            logger.info("Orchestrator initialization complete")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            self._initialized = False
            raise RuntimeError(f"Orchestrator initialization failed: {e}")
    
    def is_initialized(self) -> bool:
        """
        Check if orchestrator is initialized.
        
        Returns:
            bool: True if ready, False otherwise
        """
        return self._initialized
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform system health check.
        
        Returns:
            Dict[str, Any]: Health status containing:
                - initialized (bool): System ready state
                - components (dict): Status of each component
                - agents (dict): Agent registry health
                - queue (dict): Task queue status
        """
        health = {
            "initialized": self._initialized,
            "components": {},
            "agents": None,
            "queue": None,
        }
        
        # Check database
        if self.db_manager:
            try:
                health["components"]["database"] = "ok"
            except Exception as e:
                health["components"]["database"] = f"error: {e}"
        
        # Check memory
        if self.memory_manager:
            try:
                health["components"]["memory"] = "ok"
            except Exception as e:
                health["components"]["memory"] = f"error: {e}"
        
        # Check safety guard
        if self.safety_guard:
            try:
                health["components"]["safety"] = "ok"
            except Exception as e:
                health["components"]["safety"] = f"error: {e}"
        
        # Check agents
        if self.registry:
            health["agents"] = self.registry.health_check()
        
        # Check queue
        if self.task_manager:
            health["queue"] = self.task_manager.get_queue_status()
        
        logger.info(f"Health check complete: {health}")
        return health
    
    def register_agent(self, agent: any) -> bool:
        """
        Register an agent with the system.
        
        Args:
            agent: Agent instance to register
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If agent invalid
        """
        try:
            if not self.registry:
                logger.error("Registry not available")
                return False
            
            self.registry.register(agent)
            logger.info(f"Registered agent: {agent.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return False
    
    def execute_task(
        self,
        agent_id: str,
        payload: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """
        Queue and execute a task.
        
        Args:
            agent_id (str): Target agent identifier
            payload (Dict[str, Any]): Task input data
            priority (int): Task priority. Defaults to 0
            
        Returns:
            str: Task ID for status tracking
            
        Raises:
            ValueError: If parameters invalid
            RuntimeError: If system not initialized
            
        Example:
            >>> task_id = orchestrator.execute_task(
            ...     agent_id="correlation_001",
            ...     payload={"file_id": "file_123", "target": "column"}
            ... )
            >>> print(f"Task queued: {task_id}")
        """
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized")
        
        if not self.registry or not self.task_manager:
            raise RuntimeError("Required components not available")
        
        # Validate agent exists
        agent = self.registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Safety validation
        if self.safety_guard:
            try:
                if not self.safety_guard.validate_input(payload):
                    raise ValueError("Input validation failed")
            except Exception as e:
                logger.error(f"Safety validation failed: {e}")
                raise
        
        # Queue task
        task_id = self.task_manager.queue_task(
            agent_id=agent_id,
            payload=payload,
            priority=priority,
        )
        
        logger.info(f"Task {task_id} queued for agent {agent_id}")
        
        # Execute next task in queue (if not currently running)
        self._process_next_task()
        
        return task_id
    
    def _process_next_task(self) -> bool:
        """
        Execute next task from queue (FIFO).
        
        Internal method called after queuing new task.
        
        Returns:
            bool: True if task executed, False if queue empty
        """
        if not self.task_manager or not self.registry:
            return False
        
        task = self.task_manager.get_next_task()
        if not task:
            logger.debug("No tasks in queue")
            return False
        
        task_id = task["task_id"]
        agent_id = task["agent_id"]
        payload = task["payload"]
        
        try:
            # Get agent
            agent = self.registry.get_agent(agent_id)
            if not agent:
                self.task_manager.fail_task(
                    task_id,
                    f"Agent not found: {agent_id}",
                    retry=False,
                )
                return False
            
            # Mark task as running
            self.task_manager.start_task(task_id)
            
            # Execute agent
            logger.info(f"Executing task {task_id} with agent {agent_id}")
            result = agent.run(payload)
            
            # Complete task
            self.task_manager.complete_task(task_id, result)
            
            # Persist result if database available
            if self.db_manager:
                try:
                    self.db_manager.update_task_status(
                        task_id=task_id,
                        status="completed",
                    )
                except Exception as e:
                    logger.error(f"Failed to persist result: {e}")
            
            logger.info(f"Task {task_id} completed")
            return True
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            self.task_manager.fail_task(task_id, str(e), retry=True)
            return False
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Get status of a task.
        
        Args:
            task_id (str): Task identifier
            
        Returns:
            Optional[str]: Status ('pending', 'running', 'completed', 'error')
        """
        if not self.task_manager:
            return None
        
        return self.task_manager.get_task_status(task_id)
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result of completed task.
        
        Args:
            task_id (str): Task identifier
            
        Returns:
            Optional[Dict]: Result if completed, None otherwise
        """
        if not self.task_manager:
            return None
        
        return self.task_manager.get_task_result(task_id)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dict[str, Any]: Complete system state
        """
        return {
            "initialized": self._initialized,
            "health": self.health_check(),
            "queue": self.task_manager.get_queue_status() if self.task_manager else None,
            "agents": self.registry.get_all_statuses() if self.registry else None,
        }
