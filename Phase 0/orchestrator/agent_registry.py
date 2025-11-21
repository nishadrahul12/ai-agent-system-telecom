"""
Agent Registry: Agent registration, discovery, and lifecycle management.

Provides centralized management of all agents in the system:
    - Register/unregister agents
    - Discover agents by ID, name, or type
    - Maintain agent status
    - Provide health checks

Usage:
    registry = AgentRegistry()
    registry.register(agent)
    agent_list = registry.get_agents_by_type("correlation")
    status = registry.get_agent_status(agent_id)
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Central registry for managing agent lifecycle and discovery.
    
    Attributes:
        _agents (Dict): Internal storage of registered agents by ID
    """
    
    def __init__(self) -> None:
        """Initialize empty agent registry."""
        self._agents: Dict[str, any] = {}
        logger.info("AgentRegistry initialized")
    
    def register(self, agent: any) -> None:
        """
        Register an agent in the system.
        
        Args:
            agent: Agent instance with agent_id and name attributes
            
        Raises:
            ValueError: If agent_id already exists or agent invalid
            AttributeError: If agent missing required attributes
            
        Example:
            >>> from orchestrator.base_agent import BaseAgent
            >>> registry = AgentRegistry()
            >>> registry.register(my_agent)
            >>> assert my_agent.agent_id in registry._agents
        """
        if not hasattr(agent, "agent_id") or not hasattr(agent, "name"):
            raise AttributeError("Agent must have 'agent_id' and 'name' attributes")
        
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent with ID '{agent.agent_id}' already registered")
        
        self._agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} (ID: {agent.agent_id})")
    
    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent from the system.
        
        Args:
            agent_id (str): Agent identifier
            
        Returns:
            bool: True if agent was removed, False if not found
        """
        if agent_id in self._agents:
            agent_name = self._agents[agent_id].name
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_name} (ID: {agent_id})")
            return True
        
        logger.warning(f"Attempted to unregister non-existent agent: {agent_id}")
        return False
    
    def get_agent(self, agent_id: str) -> Optional[any]:
        """
        Retrieve a specific agent by ID.
        
        Args:
            agent_id (str): Agent identifier
            
        Returns:
            Optional[any]: Agent instance if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[any]:
        """
        Retrieve all agents of a specific type.
        
        Args:
            agent_type (str): Type filter (e.g., 'correlation', 'forecasting')
            
        Returns:
            List[any]: List of matching agents
            
        Example:
            >>> correlation_agents = registry.get_agents_by_type("correlation")
            >>> print(f"Found {len(correlation_agents)} correlation agents")
        """
        return [
            agent for agent in self._agents.values()
            if hasattr(agent, "agent_type") and agent.agent_type == agent_type
        ]
    
    def get_agents_by_status(self, status: str) -> List[any]:
        """
        Retrieve all agents with a specific status.
        
        Args:
            status (str): Status filter ('idle', 'running', 'completed', 'error')
            
        Returns:
            List[any]: List of matching agents
        """
        return [
            agent for agent in self._agents.values()
            if hasattr(agent, "status") and agent.status == status
        ]
    
    def get_all_agents(self) -> Dict[str, any]:
        """
        Retrieve all registered agents.
        
        Returns:
            Dict[str, any]: Dictionary mapping agent_id to agent instances
        """
        return dict(self._agents)
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """
        Get status snapshot of a specific agent.
        
        Args:
            agent_id (str): Agent identifier
            
        Returns:
            Optional[Dict]: Status dictionary if agent exists, None otherwise
        """
        agent = self.get_agent(agent_id)
        if agent and hasattr(agent, "get_status"):
            return agent.get_status()
        return None
    
    def get_all_statuses(self) -> Dict[str, Dict]:
        """
        Get status snapshots of all agents.
        
        Returns:
            Dict[str, Dict]: Mapping of agent_id to status dictionaries
        """
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self._agents.items()
            if hasattr(agent, "get_status")
        }
    
    def health_check(self) -> Dict[str, any]:
        """
        Perform system health check.
        
        Returns:
            Dict[str, any]: Health status containing:
                - total_agents (int): Total registered agents
                - agents_by_status (Dict): Count of agents per status
                - agents_by_type (Dict): Count of agents per type
        """
        all_agents = list(self._agents.values())
        
        agents_by_status = {}
        agents_by_type = {}
        
        for agent in all_agents:
            # Count by status
            if hasattr(agent, "status"):
                status = agent.status
                agents_by_status[status] = agents_by_status.get(status, 0) + 1
            
            # Count by type
            if hasattr(agent, "agent_type"):
                atype = agent.agent_type
                agents_by_type[atype] = agents_by_type.get(atype, 0) + 1
        
        health = {
            "total_agents": len(all_agents),
            "agents_by_status": agents_by_status,
            "agents_by_type": agents_by_type,
        }
        
        logger.info(f"Health check: {health}")
        return health
