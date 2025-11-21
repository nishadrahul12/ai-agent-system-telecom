"""
Orchestrator Module: Core agent coordination and execution engine.

This module provides the foundation for multi-agent coordination, task management,
and agent lifecycle handling in the Telecom AI Multi-Agent System.

Key Components:
    - BaseAgent: Template class for all agents
    - AgentRegistry: Agent registration and discovery
    - TaskManager: Task queue and execution engine
    - Orchestrator: Main coordinator
    - LLMConfig: LLM configuration and management

Usage:
    from orchestrator import Orchestrator, BaseAgent
    
    orchestrator = Orchestrator()
    orchestrator.initialize()
    result = orchestrator.execute_task(task_id="task_001", payload={...})
"""

__version__ = "0.1.0"
__author__ = "Telecom AI Team"

from orchestrator.base_agent import BaseAgent
from orchestrator.agent_registry import AgentRegistry
from orchestrator.task_manager import TaskManager
from orchestrator.orchestrator import Orchestrator
from orchestrator.llm_config import LLMConfig

__all__ = [
    "BaseAgent",
    "AgentRegistry", 
    "TaskManager",
    "Orchestrator",
    "LLMConfig",
]
