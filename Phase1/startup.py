"""
Phase 1: Initialize all agents and register with orchestrator.

This module is called from api_server.py during startup.
Initializes all Phase 1 agents and registers them with Phase 0 orchestrator.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def initialize_phase1_agents(orchestrator: Any) -> Dict[str, Any]:
    """
    Initialize all Phase 1 agents and register with orchestrator.
    
    Initialization sequence:
    1. Import CorrelationAgent
    2. Create agent instance
    3. Register with orchestrator
    4. Return status
    
    Args:
        orchestrator: Phase 0 Orchestrator instance
        
    Returns:
        Dict with initialization status:
        {
            "status": "success" or "error",
            "agents_initialized": count,
            "correlation_agent": "registered" or "error"
        }
        
    Raises:
        Exception: If any agent fails to initialize
    """
    try:
        from Phase1.agents.correlation_agent import CorrelationAgent
        
        logger.info("🔄 Initializing Phase 1 agents...")
        
        # Initialize CorrelationAgent
        correlation_agent = CorrelationAgent(
            name="correlation_agent_001",
            version="0.1.0"
        )
        logger.info(f"✅ CorrelationAgent created: {correlation_agent.name}")
        
        # Register with orchestrator
        orchestrator.register_agent(correlation_agent)
        logger.info("✅ CorrelationAgent registered with orchestrator")
        
        logger.info("✅ Phase 1 initialization complete")
        
        return {
            "status": "success",
            "agents_initialized": 1,
            "correlation_agent": "registered",
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Phase 1 agents: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "agents_initialized": 0,
        }
