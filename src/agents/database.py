"""Database operations for agents - storing metrics, runs, touchpoints."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from ..models.agents import (
    AgentRun,
    AdMetrics,
    Touchpoint,
    Conversion,
    CampaignPolicy,
    KeywordsExternal,
)
from ..models.database import get_async_db

logger = logging.getLogger(__name__)


class AgentDatabase:
    """Database operations for agent system."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_agent_run(
        self,
        agent: str,
        run_id: str,
        started_at: Optional[datetime] = None,
    ) -> AgentRun:
        """Create a new agent run record."""
        
        agent_run = AgentRun(
            agent=agent,
            run_id=run_id,
            started_at=started_at or datetime.utcnow(),
        )
        
        self.db.add(agent_run)
        await self.db.flush()
        await self.db.refresh(agent_run)
        
        logger.debug(f"Created agent run: {agent} - {run_id}")
        return agent_run
    
    async def update_agent_run(
        self,
        run_id: str,
        ok: bool,
        stats: Optional[Dict[str, Any]] = None,
        watermark: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[AgentRun]:
        """Update agent run with completion status."""
        
        stmt = (
            update(AgentRun)
            .where(AgentRun.run_id == run_id)
            .values(
                finished_at=datetime.utcnow(),
                ok=ok,
                stats=stats,
                watermark=watermark,
                error=error,
            )
            .returning(AgentRun)
        )
        
        result = await self.db.execute(stmt)
        agent_run = result.scalar_one_or_none()
        
        if agent_run:
            logger.debug(f"Updated agent run: {run_id} (ok={ok})")
        
        return agent_run
    
    async def get_recent_agent_runs(
        self, agent: Optional[str] = None, limit: int = 50
    ) -> List[AgentRun]:
        """Get recent agent runs."""
        
        stmt = select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)
        
        if agent:
            stmt = stmt.where(AgentRun.agent == agent)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_last_successful_run(self, agent: str) -> Optional[AgentRun]:
        """Get the last successful run for an agent."""
        
        stmt = (
            select(AgentRun)
            .where(AgentRun.agent == agent, AgentRun.ok == True)
            .order_by(AgentRun.finished_at.desc())
            .limit(1)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def upsert_ad_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Upsert ad metrics with conflict resolution."""
        
        if not metrics:
            return 0
        
        # Use PostgreSQL INSERT ... ON CONFLICT for upserts
        stmt = insert(AdMetrics).values(metrics)
        stmt = stmt.on_conflict_do_update(
            index_elements=['platform', 'date', 'account_id', 'campaign_id', 'adgroup_id', 'ad_id'],
            set_={
                'campaign_name': stmt.excluded.campaign_name,
                'impressions': stmt.excluded.impressions,
                'clicks': stmt.excluded.clicks,
                'spend_usd': stmt.excluded.spend_usd,
                'conversions': stmt.excluded.conversions,
                'ctr': stmt.excluded.ctr,
                'cpc_usd': stmt.excluded.cpc_usd,
                'raw_data': stmt.excluded.raw_data,
                'ingested_at': stmt.excluded.ingested_at,
            }
        )
        
        result = await self.db.execute(stmt)
        records_affected = result.rowcount
        
        logger.info(f"Upserted {records_affected} ad metrics records")
        return records_affected
    
    async def get_campaign_performance(
        self,
        platform: Optional[str] = None,
        days: int = 14,
    ) -> List[Dict[str, Any]]:
        """Get campaign performance metrics for optimization."""
        
        # This would be a complex query joining ad_metrics with campaign policies
        # For now, return mock data structure
        
        stmt = (
            select(AdMetrics)
            .where(AdMetrics.date >= (datetime.utcnow().date() - timedelta(days=days)).isoformat())
        )
        
        if platform:
            stmt = stmt.where(AdMetrics.platform == platform)
        
        result = await self.db.execute(stmt)
        metrics = result.scalars().all()
        
        # Aggregate by campaign
        campaign_performance = {}
        for metric in metrics:
            key = f"{metric.platform}_{metric.campaign_id}"
            
            if key not in campaign_performance:
                campaign_performance[key] = {
                    "platform": metric.platform,
                    "campaign_id": metric.campaign_id,
                    "campaign_name": metric.campaign_name,
                    "spend_14d": 0.0,
                    "conversions_14d": 0.0,
                    "impressions_14d": 0,
                    "clicks_14d": 0,
                }
            
            perf = campaign_performance[key]
            perf["spend_14d"] += metric.spend_usd
            perf["conversions_14d"] += metric.conversions
            perf["impressions_14d"] += metric.impressions
            perf["clicks_14d"] += metric.clicks
        
        # Calculate derived metrics
        for perf in campaign_performance.values():
            if perf["conversions_14d"] > 0:
                perf["cac_14d"] = perf["spend_14d"] / perf["conversions_14d"]
            else:
                perf["cac_14d"] = 0
            
            # Mock ROAS calculation (would need revenue data)
            perf["roas_14d"] = perf["conversions_14d"] * 100 / perf["spend_14d"] if perf["spend_14d"] > 0 else 0
        
        return list(campaign_performance.values())
    
    async def upsert_touchpoints(self, touchpoints: List[Dict[str, Any]]) -> int:
        """Upsert touchpoints with deduplication."""
        
        if not touchpoints:
            return 0
        
        stmt = insert(Touchpoint).values(touchpoints)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id', 'timestamp', 'platform', 'campaign'],
            set_={
                'click_id': stmt.excluded.click_id,
                'source': stmt.excluded.source,
                'medium': stmt.excluded.medium,
                'landing_url': stmt.excluded.landing_url,
                'event_type': stmt.excluded.event_type,
                'raw_properties': stmt.excluded.raw_properties,
                'extracted_at': stmt.excluded.extracted_at,
            }
        )
        
        result = await self.db.execute(stmt)
        records_affected = result.rowcount
        
        logger.info(f"Upserted {records_affected} touchpoint records")
        return records_affected
    
    async def get_new_conversions(self, since_watermark: Optional[str] = None) -> List[Conversion]:
        """Get new conversions for upload to platforms."""
        
        stmt = select(Conversion).where(
            Conversion.uploaded_to_platforms.is_(None) |
            (Conversion.uploaded_to_platforms == {})
        )
        
        if since_watermark:
            # Filter by watermark timestamp
            watermark_dt = datetime.fromisoformat(since_watermark)
            stmt = stmt.where(Conversion.created_at > watermark_dt)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_conversions_uploaded(
        self, conversion_ids: List[int], upload_results: Dict[str, Any]
    ):
        """Mark conversions as uploaded to platforms."""
        
        stmt = (
            update(Conversion)
            .where(Conversion.id.in_(conversion_ids))
            .values(uploaded_to_platforms=upload_results)
        )
        
        await self.db.execute(stmt)
        logger.info(f"Marked {len(conversion_ids)} conversions as uploaded")
    
    async def get_campaign_policies(self, platform: Optional[str] = None) -> List[CampaignPolicy]:
        """Get campaign optimization policies."""
        
        stmt = select(CampaignPolicy).where(CampaignPolicy.enabled == True)
        
        if platform:
            stmt = stmt.where(CampaignPolicy.platform == platform)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def upsert_keywords_external(self, keywords: List[Dict[str, Any]]) -> int:
        """Upsert external keyword data."""
        
        if not keywords:
            return 0
        
        stmt = insert(KeywordsExternal).values(keywords)
        stmt = stmt.on_conflict_do_update(
            index_elements=['keyword', 'source'],
            set_={
                'monthly_volume': stmt.excluded.monthly_volume,
                'est_cpc': stmt.excluded.est_cpc,
                'competition': stmt.excluded.competition,
                'pulled_at': stmt.excluded.pulled_at,
            }
        )
        
        result = await self.db.execute(stmt)
        records_affected = result.rowcount
        
        logger.info(f"Upserted {records_affected} external keyword records")
        return records_affected
    
    async def cleanup_old_agent_runs(self, days_to_keep: int = 30):
        """Clean up old agent run records."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        stmt = delete(AgentRun).where(AgentRun.started_at < cutoff_date)
        result = await self.db.execute(stmt)
        
        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old agent runs")
        
        return deleted_count


# Helper function to get database for agents
async def get_agent_db():
    """Get agent database instance."""
    async with get_async_db() as db:
        yield AgentDatabase(db)
