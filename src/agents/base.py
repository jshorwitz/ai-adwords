"""Base agent classes and common agent contract."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentJobInput:
    """Input envelope for agent jobs."""
    
    job_id: str
    run_id: str  # unique per execution
    params: Optional[Dict[str, Any]] = None
    window: Optional[Dict[str, str]] = None  # start/end dates YYYY-MM-DD
    dry_run: bool = False


@dataclass
class AgentResult:
    """Result envelope for agent jobs."""
    
    job_id: str
    run_id: str
    ok: bool
    metrics: Dict[str, int | float] = None
    records_written: Optional[int] = None
    notes: Optional[list[str]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
        if self.notes is None:
            self.notes = []


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    @abstractmethod
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Execute the agent job."""
        pass
    
    def validate_input(self, job_input: AgentJobInput) -> bool:
        """Validate job input. Override in subclasses for specific validation."""
        return job_input.job_id and job_input.run_id
    
    def create_result(
        self,
        job_input: AgentJobInput,
        ok: bool,
        metrics: Dict[str, int | float] = None,
        records_written: int = None,
        notes: list[str] = None,
        error: str = None,
    ) -> AgentResult:
        """Helper to create agent result."""
        return AgentResult(
            job_id=job_input.job_id,
            run_id=job_input.run_id,
            ok=ok,
            metrics=metrics or {},
            records_written=records_written,
            notes=notes or [],
            error=error,
        )


class IngestorAgent(BaseAgent):
    """Base class for data ingestion agents."""
    
    def __init__(self, agent_name: str, platform: str):
        super().__init__(agent_name)
        self.platform = platform
    
    def get_date_range(self, job_input: AgentJobInput) -> tuple[str, str]:
        """Get date range from job input or default to yesterday."""
        if job_input.window and job_input.window.get('start') and job_input.window.get('end'):
            return job_input.window['start'], job_input.window['end']
        
        # Default to yesterday
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)
        return yesterday.isoformat(), yesterday.isoformat()


class TransformAgent(BaseAgent):
    """Base class for data transformation agents."""
    pass


class ActivationAgent(BaseAgent):
    """Base class for activation/upload agents."""
    pass


class DecisionAgent(BaseAgent):
    """Base class for decision-making agents."""
    pass


class SREAgent(BaseAgent):
    """Base class for SRE/monitoring agents."""
    pass
