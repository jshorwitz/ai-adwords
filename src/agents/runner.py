"""Agent job runner and orchestration system."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Type

from .base import BaseAgent, AgentJobInput, AgentResult

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry of all available agents."""
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
    
    def register(self, agent_name: str, agent_class: Type[BaseAgent]):
        """Register an agent class."""
        self._agents[agent_name] = agent_class
        logger.info(f"Registered agent: {agent_name}")
    
    def get_agent(self, agent_name: str) -> Optional[Type[BaseAgent]]:
        """Get agent class by name."""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())


class AgentRunner:
    """Orchestrates and runs agents."""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
    
    async def run_agent(
        self,
        agent_name: str,
        params: Optional[Dict] = None,
        window: Optional[Dict[str, str]] = None,
        dry_run: bool = False,
    ) -> AgentResult:
        """Run a single agent job."""
        
        # Generate unique IDs
        job_id = f"{agent_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_id = str(uuid.uuid4())
        
        job_input = AgentJobInput(
            job_id=job_id,
            run_id=run_id,
            params=params,
            window=window,
            dry_run=dry_run,
        )
        
        logger.info(f"Starting agent job: {job_id} (run_id: {run_id})")
        
        # Get agent class
        agent_class = self.registry.get_agent(agent_name)
        if not agent_class:
            error_msg = f"Agent '{agent_name}' not found"
            logger.error(error_msg)
            return AgentResult(
                job_id=job_id,
                run_id=run_id,
                ok=False,
                error=error_msg,
            )
        
        # Create and run agent
        try:
            agent = agent_class(agent_name)
            
            # Validate input
            if not agent.validate_input(job_input):
                error_msg = "Invalid job input"
                logger.error(error_msg)
                return AgentResult(
                    job_id=job_id,
                    run_id=run_id,
                    ok=False,
                    error=error_msg,
                )
            
            # Run the agent
            start_time = datetime.now()
            result = await agent.run(job_input)
            end_time = datetime.now()
            
            # Add timing info
            duration = (end_time - start_time).total_seconds()
            result.metrics['duration_seconds'] = duration
            
            logger.info(f"Agent job completed: {job_id} (ok={result.ok}, duration={duration:.2f}s)")
            return result
            
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            logger.exception(error_msg)
            return AgentResult(
                job_id=job_id,
                run_id=run_id,
                ok=False,
                error=error_msg,
            )


# Global registry instance
agent_registry = AgentRegistry()
