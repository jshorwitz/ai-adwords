"""Multi-platform advertising agents for automated ETL to BigQuery synter_analytics."""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..etl.multi_platform_pipeline import MultiPlatformETLPipeline
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MultiPlatformIngestorAgent(BaseAgent):
    """Agent for ingesting data from multiple advertising platforms to BigQuery."""
    
    def __init__(self):
        super().__init__(
            agent_name="multi-platform-ingestor",
            description="Ingest advertising data from Reddit, Microsoft, and LinkedIn to BigQuery",
            schedule="0 */2 * * *",  # Every 2 hours
            dependencies=[]
        )
        self.pipeline = MultiPlatformETLPipeline()
    
    async def execute(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute multi-platform data ingestion."""
        try:
            # Get parameters
            days_back = params.get("days_back", 1) if params else 1
            dry_run = params.get("dry_run", False) if params else False
            
            self.logger.info(f"Starting multi-platform ETL (days_back={days_back}, dry_run={dry_run})")
            
            if dry_run:
                self.logger.info("DRY RUN: Would sync data from all platforms to BigQuery")
                return {
                    "status": "success",
                    "mode": "dry_run", 
                    "platforms_checked": ["reddit", "microsoft", "linkedin"],
                    "would_sync": True
                }
            
            # Execute the actual ETL pipeline
            results = await self.pipeline.sync_all_platforms(days_back)
            
            # Log results
            total_records = results.get("total_records", 0)
            platforms = results.get("platforms", {})
            errors = results.get("errors", [])
            
            self.logger.info(f"Multi-platform ETL completed: {total_records} total records")
            
            for platform, platform_result in platforms.items():
                status = platform_result.get("status", "unknown")
                records = platform_result.get("records_written", 0)
                self.logger.info(f"  {platform}: {status} ({records} records)")
            
            if errors:
                for error in errors:
                    self.logger.error(f"  Error: {error}")
            
            return {
                "status": "success" if results.get("success") else "partial_failure",
                "total_records": total_records,
                "platforms": platforms,
                "errors": errors,
                "sync_duration": results.get("sync_completed_at"),
                "date_range": results.get("date_range")
            }
            
        except Exception as e:
            self.logger.error(f"Multi-platform ETL failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "platforms": [],
                "total_records": 0
            }


class RedditAdsIngestorAgent(BaseAgent):
    """Dedicated agent for Reddit Ads data ingestion."""
    
    def __init__(self):
        super().__init__(
            agent_name="reddit-ads-ingestor",
            description="Ingest Reddit Ads data to BigQuery synter_analytics",
            schedule="0 1,13 * * *",  # Twice daily at 1 AM and 1 PM
            dependencies=[]
        )
        self.pipeline = MultiPlatformETLPipeline()
    
    async def execute(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute Reddit Ads data ingestion."""
        try:
            days_back = params.get("days_back", 1) if params else 1
            dry_run = params.get("dry_run", False) if params else False
            
            self.logger.info(f"Starting Reddit Ads ETL (days_back={days_back})")
            
            if dry_run:
                self.logger.info("DRY RUN: Would sync Reddit Ads data to BigQuery")
                return {
                    "status": "success",
                    "mode": "dry_run",
                    "platform": "reddit"
                }
            
            # Check if Reddit is enabled
            if not self.pipeline.platforms_enabled.get("reddit"):
                self.logger.warning("Reddit Ads not enabled - skipping")
                return {
                    "status": "skipped",
                    "reason": "Reddit Ads not configured or in mock mode",
                    "platform": "reddit"
                }
            
            # Execute Reddit ETL
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            result = await self.pipeline._sync_reddit_data(start_date, end_date)
            
            self.logger.info(f"Reddit ETL completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Reddit ETL failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "platform": "reddit"
            }


class MicrosoftAdsIngestorAgent(BaseAgent):
    """Dedicated agent for Microsoft Ads data ingestion."""
    
    def __init__(self):
        super().__init__(
            agent_name="microsoft-ads-ingestor", 
            description="Ingest Microsoft Ads data to BigQuery synter_analytics",
            schedule="0 2,14 * * *",  # Twice daily at 2 AM and 2 PM
            dependencies=[]
        )
        self.pipeline = MultiPlatformETLPipeline()
    
    async def execute(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute Microsoft Ads data ingestion."""
        try:
            days_back = params.get("days_back", 1) if params else 1
            dry_run = params.get("dry_run", False) if params else False
            
            self.logger.info(f"Starting Microsoft Ads ETL (days_back={days_back})")
            
            if dry_run:
                self.logger.info("DRY RUN: Would sync Microsoft Ads data to BigQuery")
                return {
                    "status": "success",
                    "mode": "dry_run",
                    "platform": "microsoft"
                }
            
            # Check if Microsoft is enabled
            if not self.pipeline.platforms_enabled.get("microsoft"):
                self.logger.warning("Microsoft Ads not enabled - skipping")
                return {
                    "status": "skipped", 
                    "reason": "Microsoft Ads not configured or in mock mode",
                    "platform": "microsoft"
                }
            
            # Execute Microsoft ETL
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            result = await self.pipeline._sync_microsoft_data(start_date, end_date)
            
            self.logger.info(f"Microsoft ETL completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Microsoft ETL failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "platform": "microsoft"
            }


class LinkedInAdsIngestorAgent(BaseAgent):
    """Dedicated agent for LinkedIn Ads data ingestion."""
    
    def __init__(self):
        super().__init__(
            agent_name="linkedin-ads-ingestor",
            description="Ingest LinkedIn Ads data to BigQuery synter_analytics", 
            schedule="0 3,15 * * *",  # Twice daily at 3 AM and 3 PM
            dependencies=[]
        )
        self.pipeline = MultiPlatformETLPipeline()
    
    async def execute(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute LinkedIn Ads data ingestion."""
        try:
            days_back = params.get("days_back", 1) if params else 1
            dry_run = params.get("dry_run", False) if params else False
            
            self.logger.info(f"Starting LinkedIn Ads ETL (days_back={days_back})")
            
            if dry_run:
                self.logger.info("DRY RUN: Would sync LinkedIn Ads data to BigQuery")
                return {
                    "status": "success",
                    "mode": "dry_run",
                    "platform": "linkedin"
                }
            
            # Execute LinkedIn ETL (currently mock implementation)
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d") 
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            result = await self.pipeline._sync_linkedin_data(start_date, end_date)
            
            self.logger.info(f"LinkedIn ETL completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"LinkedIn ETL failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "platform": "linkedin"
            }


# Agent registry for the multi-platform agents
MULTI_PLATFORM_AGENTS = {
    "multi-platform-ingestor": MultiPlatformIngestorAgent(),
    "reddit-ads-ingestor": RedditAdsIngestorAgent(),
    "microsoft-ads-ingestor": MicrosoftAdsIngestorAgent(),
    "linkedin-ads-ingestor": LinkedInAdsIngestorAgent(),
}


def register_multi_platform_agents(agent_registry):
    """Register all multi-platform agents with the main agent registry."""
    for agent_name, agent in MULTI_PLATFORM_AGENTS.items():
        agent_registry.register_agent(agent_name, agent)
        logger.info(f"Registered multi-platform agent: {agent_name}")


# Convenience functions for manual execution
async def run_multi_platform_sync(days_back: int = 1, dry_run: bool = False):
    """Manually run multi-platform sync."""
    agent = MultiPlatformIngestorAgent()
    params = {"days_back": days_back, "dry_run": dry_run}
    return await agent.execute(params)


async def run_reddit_sync(days_back: int = 1, dry_run: bool = False):
    """Manually run Reddit sync."""
    agent = RedditAdsIngestorAgent()
    params = {"days_back": days_back, "dry_run": dry_run}
    return await agent.execute(params)


async def run_microsoft_sync(days_back: int = 1, dry_run: bool = False):
    """Manually run Microsoft sync."""
    agent = MicrosoftAdsIngestorAgent()
    params = {"days_back": days_back, "dry_run": dry_run}
    return await agent.execute(params)


async def run_linkedin_sync(days_back: int = 1, dry_run: bool = False):
    """Manually run LinkedIn sync."""
    agent = LinkedInAdsIngestorAgent()
    params = {"days_back": days_back, "dry_run": dry_run}
    return await agent.execute(params)


if __name__ == "__main__":
    # Test the agents
    async def test_agents():
        print("🤖 Testing Multi-Platform ETL Agents")
        print("=" * 50)
        
        # Test multi-platform sync (dry run)
        print("\n1. Testing Multi-Platform Sync (Dry Run)...")
        result = await run_multi_platform_sync(days_back=7, dry_run=True)
        print(f"Result: {result}")
        
        # Test individual platform syncs (dry run)
        print("\n2. Testing Reddit Sync (Dry Run)...")
        result = await run_reddit_sync(days_back=7, dry_run=True)
        print(f"Result: {result}")
        
        print("\n3. Testing Microsoft Sync (Dry Run)...")
        result = await run_microsoft_sync(days_back=7, dry_run=True)
        print(f"Result: {result}")
        
        print("\n4. Testing LinkedIn Sync (Dry Run)...")
        result = await run_linkedin_sync(days_back=7, dry_run=True)
        print(f"Result: {result}")
        
        print("\n✅ Agent testing completed!")
    
    import asyncio
    from datetime import timedelta
    asyncio.run(test_agents())
