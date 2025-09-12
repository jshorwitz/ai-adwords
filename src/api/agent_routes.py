"""Agent management API routes."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..agents.database import AgentDatabase, get_agent_db
from ..agents.runner import agent_registry, AgentRunner
from ..models.auth import User, UserRole
from .middleware import get_current_user, require_admin_or_analyst

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# Request/Response models
class AgentRunRequest(BaseModel):
    agent: str
    params: Optional[Dict] = None
    window: Optional[Dict[str, str]] = None
    dry_run: bool = False


class AgentRunResponse(BaseModel):
    job_id: str
    run_id: str
    ok: bool
    metrics: Dict = {}
    records_written: Optional[int] = None
    notes: List[str] = []
    error: Optional[str] = None


class AgentListResponse(BaseModel):
    agent_name: str
    type: str
    description: str


class AgentStatusResponse(BaseModel):
    agent: str
    run_id: str
    started_at: str
    finished_at: Optional[str]
    ok: Optional[bool]
    duration_seconds: Optional[float]
    records_written: Optional[int]
    error: Optional[str]


@router.get("/list", response_model=List[AgentListResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
):
    """List all available agents."""
    
    agent_info = {
        "ingestor-google": ("Ingestor", "Pull Google Ads metrics via GAQL"),
        "ingestor-reddit": ("Ingestor", "Pull Reddit Ads metrics (mockable)"),  
        "ingestor-x": ("Ingestor", "Pull X/Twitter Ads metrics (mockable)"),
        "touchpoint-extractor": ("Transform", "Extract touchpoints from events"),
        "conversion-uploader": ("Activation", "Upload conversions to platforms"),
        "budget-optimizer": ("Decision", "Optimize campaign budgets based on CAC/ROAS"),
        "keywords-hydrator": ("Decision", "Enrich keywords from external APIs"),
    }
    
    agents = agent_registry.list_agents()
    
    return [
        AgentListResponse(
            agent_name=agent_name,
            type=agent_info.get(agent_name, ("Unknown", ""))[0],
            description=agent_info.get(agent_name, ("", "No description"))[1],
        )
        for agent_name in sorted(agents)
    ]


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(require_admin_or_analyst),  # Only admin/analyst can run agents
):
    """Run an agent job."""
    
    # Validate agent exists
    if request.agent not in agent_registry.list_agents():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{request.agent}' not found"
        )
    
    try:
        runner = AgentRunner(agent_registry)
        
        # Run the agent
        result = await runner.run_agent(
            agent_name=request.agent,
            params=request.params,
            window=request.window,
            dry_run=request.dry_run,
        )
        
        # Log the execution
        logger.info(
            f"Agent {request.agent} executed by {current_user.email} "
            f"(dry_run={request.dry_run}, ok={result.ok})"
        )
        
        return AgentRunResponse(
            job_id=result.job_id,
            run_id=result.run_id,
            ok=result.ok,
            metrics=result.metrics,
            records_written=result.records_written,
            notes=result.notes,
            error=result.error,
        )
        
    except Exception as e:
        logger.exception(f"Failed to run agent {request.agent}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.get("/status", response_model=List[AgentStatusResponse])
async def get_agent_status(
    agent: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    agent_db: AgentDatabase = Depends(get_agent_db),
):
    """Get agent run status and history."""
    
    try:
        agent_runs = await agent_db.get_recent_agent_runs(agent=agent, limit=limit)
        
        status_list = []
        for run in agent_runs:
            duration_seconds = None
            if run.finished_at and run.started_at:
                duration = run.finished_at - run.started_at
                duration_seconds = duration.total_seconds()
            
            records_written = None
            if run.stats and "records_written" in run.stats:
                records_written = run.stats["records_written"]
            
            status_list.append(
                AgentStatusResponse(
                    agent=run.agent,
                    run_id=run.run_id[:8],  # Shortened for display
                    started_at=run.started_at.isoformat(),
                    finished_at=run.finished_at.isoformat() if run.finished_at else None,
                    ok=run.ok,
                    duration_seconds=duration_seconds,
                    records_written=records_written,
                    error=run.error,
                )
            )
        
        return status_list
        
    except Exception as e:
        logger.exception("Failed to get agent status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/runs/{run_id}")
async def get_agent_run_details(
    run_id: str,
    current_user: User = Depends(get_current_user),
    agent_db: AgentDatabase = Depends(get_agent_db),
):
    """Get detailed information about a specific agent run."""
    
    try:
        # Find the agent run
        recent_runs = await agent_db.get_recent_agent_runs(limit=1000)  # Search more broadly
        agent_run = None
        
        for run in recent_runs:
            if run.run_id == run_id or run.run_id.startswith(run_id):
                agent_run = run
                break
        
        if not agent_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent run not found"
            )
        
        return {
            "agent": agent_run.agent,
            "run_id": agent_run.run_id,
            "started_at": agent_run.started_at.isoformat(),
            "finished_at": agent_run.finished_at.isoformat() if agent_run.finished_at else None,
            "ok": agent_run.ok,
            "stats": agent_run.stats,
            "watermark": agent_run.watermark,
            "error": agent_run.error,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get agent run details for {run_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get run details: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_runs(
    days_to_keep: int = 30,
    current_user: User = Depends(require_admin_or_analyst),
    agent_db: AgentDatabase = Depends(get_agent_db),
):
    """Clean up old agent run records (admin/analyst only)."""
    
    try:
        deleted_count = await agent_db.cleanup_old_agent_runs(days_to_keep)
        
        logger.info(f"Admin cleanup: {current_user.email} deleted {deleted_count} old runs")
        
        return {
            "message": f"Cleaned up {deleted_count} agent runs older than {days_to_keep} days",
            "deleted_count": deleted_count,
        }
        
    except Exception as e:
        logger.exception("Failed to cleanup old runs")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def agent_health_check():
    """Basic health check for agent system."""
    
    try:
        # Check agent registry
        agents = agent_registry.list_agents()
        
        return {
            "status": "healthy",
            "agents_registered": len(agents),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.exception("Agent health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent system unhealthy: {str(e)}"
        )
