"""
Base Agent Template Class.

All specialized agents (CorrelationAgent, ForecastingAgent, AnomalyAgent) inherit
from this class. Provides standard lifecycle, error handling, and integration points.

Responsibilities:
    - Initialize with unique agent ID and name
    - Execute tasks with standard input/output format
    - Handle errors and logging
    - Manage agent state and status
    - Integrate with memory and orchestrator

Usage:
    class MyAgent(BaseAgent):
        def execute(self, task_input: dict) -> dict:
            self.logger.info(f"Executing with: {task_input}")
            result = self.process(task_input)
            return {"status": "completed", "output": result}
    
    agent = MyAgent(agent_id="agent_001", name="MyAgent")
    result = agent.execute({"data": [1, 2, 3]})
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Attributes:
        agent_id (str): Unique identifier for the agent
        name (str): Human-readable agent name
        agent_type (str): Type classification (e.g., 'correlation', 'forecasting')
        status (str): Current status ('idle', 'running', 'completed', 'error')
        created_at (datetime): Agent creation timestamp
        last_executed (Optional[datetime]): Last execution timestamp
    """
    
    def __init__(
        self, 
        agent_id: str, 
        name: str, 
        agent_type: str = "base"
    ) -> None:
        """
        Initialize base agent.
        
        Args:
            agent_id (str): Unique agent identifier
            name (str): Human-readable agent name
            agent_type (str): Agent classification. Defaults to "base"
            
        Raises:
            ValueError: If agent_id or name is empty
        """
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be non-empty string")
        if not name or not isinstance(name, str):
            raise ValueError("name must be non-empty string")
            
        self.agent_id: str = agent_id
        self.name: str = name
        self.agent_type: str = agent_type
        self.status: str = "idle"
        self.created_at: datetime = datetime.utcnow()
        self.last_executed: Optional[datetime] = None
        self.logger: logging.Logger = logging.getLogger(f"Agent.{self.name}")
        
        logger.info(f"Initialized {self.agent_type} agent: {self.name} (ID: {self.agent_id})")
    
    @abstractmethod
    def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent's main task. Must be implemented by subclasses.
        
        Args:
            task_input (Dict[str, Any]): Input parameters for execution
            
        Returns:
            Dict[str, Any]: Result dictionary with keys:
                - status (str): 'completed', 'error', 'pending'
                - output (Any): Main result payload
                - metadata (Dict): Execution metadata
                - error_message (str): Error description (if status='error')
                
        Raises:
            NotImplementedError: If not overridden by subclass
            
        Example:
            >>> result = agent.execute({"target": "column_name"})
            >>> assert result["status"] in ["completed", "error"]
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def run(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task with status tracking and error handling.
        
        Wraps the execute() method to provide:
        - Automatic status updates
        - Exception catching and logging
        - Execution timing
        - Last execution timestamp update
        
        Args:
            task_input (Dict[str, Any]): Task parameters
            
        Returns:
            Dict[str, Any]: Execution result with standardized format
        """
        execution_id: str = str(uuid4())
        start_time: datetime = datetime.utcnow()
        
        try:
            self.status = "running"
            self.logger.info(f"Starting execution: {execution_id}")
            
            result: Dict[str, Any] = self.execute(task_input)
            
            # Ensure result has required fields
            if "status" not in result:
                result["status"] = "completed"
            if "metadata" not in result:
                result["metadata"] = {}
            
            # Add execution metadata
            result["metadata"]["execution_id"] = execution_id
            result["metadata"]["agent_id"] = self.agent_id
            result["metadata"]["agent_name"] = self.name
            result["metadata"]["execution_time_ms"] = (
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            self.status = "completed"
            self.last_executed = datetime.utcnow()
            self.logger.info(f"Completed execution: {execution_id}")
            
            return result
            
        except Exception as e:
            self.status = "error"
            self.logger.error(f"Execution failed: {str(e)}", exc_info=True)
            
            return {
                "status": "error",
                "output": None,
                "error_message": str(e),
                "metadata": {
                    "execution_id": execution_id,
                    "agent_id": self.agent_id,
                    "agent_name": self.name,
                    "execution_time_ms": (
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    ),
                }
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status snapshot.
        
        Returns:
            Dict[str, Any]: Status information containing:
                - agent_id (str): Agent identifier
                - name (str): Agent name
                - type (str): Agent type
                - status (str): Current status
                - created_at (str): Creation timestamp (ISO format)
                - last_executed (str): Last execution timestamp (ISO format or None)
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
        }
    
    def reset_status(self) -> None:
        """
        Reset agent to idle state.
        
        Usage:
            agent.reset_status()
            assert agent.status == "idle"
        """
        self.status = "idle"
        self.logger.debug(f"Status reset to idle")
