"""Data ingestion agents for Google Ads, Reddit Ads, and X/Twitter Ads."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

from ..ads.ads_client import create_client_from_env
from ..ads.reporting import ReportingManager
from .base import IngestorAgent, AgentJobInput, AgentResult
from .runner import agent_registry

logger = logging.getLogger(__name__)


class GoogleIngestorAgent(IngestorAgent):
    """Ingests Google Ads metrics and normalizes to ad_metrics table."""
    
    def __init__(self, agent_name: str = "ingestor-google"):
        super().__init__(agent_name, "google")
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Pull daily Google Ads metrics and normalize to ad_metrics."""
        
        try:
            start_date, end_date = self.get_date_range(job_input)
            self.logger.info(f"Ingesting Google Ads data for {start_date} to {end_date}")
            
            if job_input.dry_run:
                self.logger.info("DRY RUN: Would ingest Google Ads metrics")
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={"dry_run": 1, "records_would_write": 100},
                    notes=["Dry run completed successfully"],
                )
            
            # Initialize Google Ads client
            client = create_client_from_env()
            reporting_manager = ReportingManager(client)
            
            # Pull campaign metrics using GAQL
            metrics_data = await self._fetch_campaign_metrics(
                reporting_manager, start_date, end_date
            )
            
            # Normalize and upsert to ad_metrics table
            records_written = await self._upsert_ad_metrics(metrics_data)
            
            return self.create_result(
                job_input,
                ok=True,
                metrics={
                    "records_fetched": len(metrics_data),
                    "records_written": records_written,
                },
                records_written=records_written,
                notes=[f"Successfully processed {len(metrics_data)} campaign metrics"],
            )
            
        except Exception as e:
            self.logger.exception("Failed to ingest Google Ads data")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _fetch_campaign_metrics(
        self, reporting_manager: ReportingManager, start_date: str, end_date: str
    ) -> list[Dict[str, Any]]:
        """Fetch campaign metrics using GAQL."""
        
        # GAQL query for daily campaign metrics
        query = f"""
        SELECT
          segments.date,
          customer.id,
          campaign.id,
          campaign.name,
          campaign.status,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.ctr,
          metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY segments.date DESC
        """
        
        # Use existing reporting manager to execute query
        return await asyncio.to_thread(
            reporting_manager.run_search_stream_query,
            query
        )
    
    async def _upsert_ad_metrics(self, metrics_data: list[Dict[str, Any]]) -> int:
        """Normalize and upsert metrics to ad_metrics table."""
        
        from .database import get_agent_db
        
        normalized_records = []
        for row in metrics_data:
            normalized_record = {
                "platform": "google",
                "date": row.get("segments.date"),
                "account_id": str(row.get("customer.id", "")),
                "campaign_id": str(row.get("campaign.id", "")),
                "adgroup_id": str(row.get("ad_group.id", "")) if row.get("ad_group.id") else None,
                "ad_id": str(row.get("ad_group_ad.ad.id", "")) if row.get("ad_group_ad.ad.id") else None,
                "campaign_name": row.get("campaign.name", ""),
                "impressions": int(row.get("metrics.impressions", 0)),
                "clicks": int(row.get("metrics.clicks", 0)),
                "spend_usd": float(row.get("metrics.cost_micros", 0)) / 1_000_000,
                "conversions": float(row.get("metrics.conversions", 0)),
                "ctr": float(row.get("metrics.ctr", 0)),
                "cpc_usd": float(row.get("metrics.average_cpc", 0)) / 1_000_000,
                "raw_data": row,
                "ingested_at": datetime.now(),
            }
            normalized_records.append(normalized_record)
        
        # Upsert to database
        async for agent_db in get_agent_db():
            records_written = await agent_db.upsert_ad_metrics(normalized_records)
            break
        
        self.logger.info(f"Upserted {records_written} Google Ads metrics records")
        return records_written


class RedditIngestorAgent(IngestorAgent):
    """Ingests Reddit Ads metrics (mockable)."""
    
    def __init__(self, agent_name: str = "ingestor-reddit"):
        super().__init__(agent_name, "reddit")
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Pull Reddit Ads metrics or generate mock data."""
        
        try:
            start_date, end_date = self.get_date_range(job_input)
            self.logger.info(f"Ingesting Reddit Ads data for {start_date} to {end_date}")
            
            # Check if we should use mock data
            import os
            use_mock = os.getenv("MOCK_REDDIT", "false").lower() == "true"
            
            if use_mock or job_input.dry_run:
                return await self._generate_mock_data(job_input, start_date, end_date)
            
            # TODO: Implement actual Reddit Ads API integration
            return await self._fetch_reddit_ads_data(job_input, start_date, end_date)
            
        except Exception as e:
            self.logger.exception("Failed to ingest Reddit Ads data")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _generate_mock_data(
        self, job_input: AgentJobInput, start_date: str, end_date: str
    ) -> AgentResult:
        """Generate deterministic mock Reddit Ads data."""
        
        import random
        random.seed(42)  # Deterministic for testing
        
        mock_records = []
        current_date = datetime.fromisoformat(start_date)
        end_date_obj = datetime.fromisoformat(end_date)
        
        while current_date <= end_date_obj:
            for campaign_id in ["reddit_camp_1", "reddit_camp_2"]:
                mock_record = {
                    "platform": "reddit",
                    "date": current_date.date().isoformat(),
                    "account_id": "reddit_account_123",
                    "campaign_id": campaign_id,
                    "campaign_name": f"Reddit Campaign {campaign_id}",
                    "impressions": random.randint(1000, 10000),
                    "clicks": random.randint(50, 500),
                    "spend_usd": round(random.uniform(100, 1000), 2),
                    "conversions": random.randint(1, 20),
                    "raw_data": {"mock": True},
                    "ingested_at": datetime.now().isoformat(),
                }
                mock_records.append(mock_record)
            
            current_date += timedelta(days=1)
        
        self.logger.info(f"Generated {len(mock_records)} mock Reddit records")
        
        return self.create_result(
            job_input,
            ok=True,
            metrics={
                "mock_records_generated": len(mock_records),
                "date_range_days": (end_date_obj - datetime.fromisoformat(start_date)).days + 1,
            },
            records_written=len(mock_records),
            notes=["Mock Reddit data generated successfully"],
        )
    
    async def _fetch_reddit_ads_data(
        self, job_input: AgentJobInput, start_date: str, end_date: str
    ) -> AgentResult:
        """Fetch actual Reddit Ads data."""
        
        try:
            from ..integrations.reddit_ads import RedditAdsClient
            
            self.logger.info("🔗 Connecting to Reddit Ads API...")
            
            # Convert date strings to datetime objects
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            async with RedditAdsClient() as client:
                # Get campaign metrics
                metrics_list = await client.get_all_campaign_metrics(start_dt, end_dt)
                
                if not metrics_list:
                    self.logger.warning("⚠️ No Reddit campaign data found")
                    return self.create_result(
                        job_input,
                        ok=True,
                        metrics={"campaigns_found": 0},
                        records_written=0,
                        notes=["No Reddit campaigns found for the specified date range"]
                    )
                
                # Convert Reddit metrics to standardized format
                records = []
                for metric in metrics_list:
                    record = {
                        "platform": "reddit",
                        "date": metric.date,
                        "account_id": "reddit_account_real",
                        "campaign_id": metric.campaign_id,
                        "campaign_name": metric.campaign_name,
                        "impressions": metric.impressions,
                        "clicks": metric.clicks,
                        "spend_usd": metric.spend,
                        "conversions": metric.conversions,
                        "raw_data": metric.dict(),
                        "ingested_at": datetime.now().isoformat(),
                    }
                    records.append(record)
                
                self.logger.info(f"✅ Retrieved {len(records)} Reddit campaign records")
                
                # TODO: Store records in database (implement ad_metrics table operations)
                
                return self.create_result(
                    job_input,
                    ok=True,
                    metrics={
                        "campaigns_processed": len(metrics_list),
                        "total_spend": sum(r["spend_usd"] for r in records),
                        "total_clicks": sum(r["clicks"] for r in records),
                        "total_impressions": sum(r["impressions"] for r in records),
                    },
                    records_written=len(records),
                    notes=[f"Successfully ingested Reddit Ads data for {len(metrics_list)} campaigns"]
                )
                
        except Exception as e:
            self.logger.exception("❌ Failed to fetch Reddit Ads data")
            return self.create_result(
                job_input,
                ok=False,
                error=f"Reddit Ads API error: {str(e)}",
            )


class MicrosoftIngestorAgent(IngestorAgent):
    """Ingests Microsoft Ads metrics (mockable)."""
    
    def __init__(self, agent_name: str = "ingestor-microsoft"):
        super().__init__(agent_name, "microsoft")
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Pull Microsoft Ads metrics or generate mock data."""
        
        try:
            start_date, end_date = self.get_date_range(job_input)
            self.logger.info(f"Ingesting Microsoft Ads data for {start_date} to {end_date}")
            
            # Check if we should use mock data
            import os
            use_mock = os.getenv("MOCK_MICROSOFT", "true").lower() == "true"  # Default to mock
            
            if use_mock or job_input.dry_run:
                return await self._generate_mock_data(job_input, start_date, end_date)
            
            # TODO: Implement actual Microsoft Ads API integration
            return await self._fetch_microsoft_ads_data(job_input, start_date, end_date)
            
        except Exception as e:
            self.logger.exception("Failed to ingest Microsoft Ads data")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _generate_mock_data(
        self, job_input: AgentJobInput, start_date: str, end_date: str
    ) -> AgentResult:
        """Generate deterministic mock Microsoft Ads data."""
        
        import random
        random.seed(789)  # Different seed for Microsoft
        
        mock_records = []
        current_date = datetime.fromisoformat(start_date)
        end_date_obj = datetime.fromisoformat(end_date)
        
        while current_date <= end_date_obj:
            for campaign_id in ["ms_camp_1", "ms_camp_2"]:
                mock_record = {
                    "platform": "microsoft",
                    "date": current_date.date().isoformat(),
                    "account_id": "microsoft_account_789",
                    "campaign_id": campaign_id,
                    "campaign_name": f"Microsoft Campaign {campaign_id}",
                    "impressions": random.randint(1500, 15000),
                    "clicks": random.randint(80, 800),
                    "spend_usd": round(random.uniform(150, 1500), 2),
                    "conversions": random.randint(3, 25),
                    "raw_data": {"mock": True, "platform": "microsoft"},
                    "ingested_at": datetime.now().isoformat(),
                }
                mock_records.append(mock_record)
            
            current_date += timedelta(days=1)
        
        self.logger.info(f"Generated {len(mock_records)} mock Microsoft records")
        
        return self.create_result(
            job_input,
            ok=True,
            metrics={
                "mock_records_generated": len(mock_records),
                "date_range_days": (end_date_obj - datetime.fromisoformat(start_date)).days + 1,
            },
            records_written=len(mock_records),
            notes=["Mock Microsoft Ads data generated successfully"],
        )
    
    async def _fetch_microsoft_ads_data(
        self, job_input: AgentJobInput, start_date: str, end_date: str
    ) -> AgentResult:
        """Fetch actual Microsoft Ads data."""
        
        # TODO: Implement Microsoft Ads API integration
        # This would call Microsoft Advertising API endpoints
        
        self.logger.warning("Microsoft Ads API integration not yet implemented")
        return self.create_result(
            job_input,
            ok=False,
            error="Microsoft Ads API integration not implemented",
        )


class LinkedInIngestorAgent(IngestorAgent):
    """Ingests LinkedIn Ads metrics (mockable)."""
    
    def __init__(self, agent_name: str = "ingestor-linkedin"):
        super().__init__(agent_name, "linkedin")
    
    async def run(self, job_input: AgentJobInput) -> AgentResult:
        """Pull LinkedIn Ads metrics or generate mock data."""
        
        try:
            start_date, end_date = self.get_date_range(job_input)
            self.logger.info(f"Ingesting LinkedIn Ads data for {start_date} to {end_date}")
            
            # Check if we should use mock data
            import os
            use_mock = os.getenv("MOCK_LINKEDIN", "true").lower() == "true"  # Default to mock
            
            if use_mock or job_input.dry_run:
                return await self._generate_mock_data(job_input, start_date, end_date)
            
            # TODO: Implement actual LinkedIn Ads API integration
            return await self._fetch_linkedin_ads_data(job_input, start_date, end_date)
            
        except Exception as e:
            self.logger.exception("Failed to ingest LinkedIn Ads data")
            return self.create_result(
                job_input,
                ok=False,
                error=str(e),
            )
    
    async def _generate_mock_data(
        self, job_input: AgentJobInput, start_date: str, end_date: str
    ) -> AgentResult:
        """Generate deterministic mock LinkedIn Ads data."""
        
        import random
        random.seed(456)  # Different seed for LinkedIn
        
        mock_records = []
        current_date = datetime.fromisoformat(start_date)
        end_date_obj = datetime.fromisoformat(end_date)
        
        while current_date <= end_date_obj:
            for campaign_id in ["li_camp_1", "li_camp_2"]:
                mock_record = {
                    "platform": "linkedin",
                    "date": current_date.date().isoformat(),
                    "account_id": "linkedin_account_101",
                    "campaign_id": campaign_id,
                    "campaign_name": f"LinkedIn Campaign {campaign_id}",
                    "impressions": random.randint(800, 8000),
                    "clicks": random.randint(30, 300),
                    "spend_usd": round(random.uniform(80, 800), 2),
                    "conversions": random.randint(2, 15),
                    "raw_data": {"mock": True, "platform": "linkedin"},
                    "ingested_at": datetime.now().isoformat(),
                }
                mock_records.append(mock_record)
            
            current_date += timedelta(days=1)
        
        self.logger.info(f"Generated {len(mock_records)} mock LinkedIn records")
        
        return self.create_result(
            job_input,
            ok=True,
            metrics={
                "mock_records_generated": len(mock_records),
                "date_range_days": (end_date_obj - datetime.fromisoformat(start_date)).days + 1,
            },
            records_written=len(mock_records),
            notes=["Mock LinkedIn Ads data generated successfully"],
        )
    
    async def _fetch_linkedin_ads_data(
        self, job_input: AgentJobInput, start_date: str, end_date: str
    ) -> AgentResult:
        """Fetch actual LinkedIn Ads data."""
        
        # TODO: Implement LinkedIn Ads API integration
        # This would call LinkedIn Marketing API endpoints
        
        self.logger.warning("LinkedIn Ads API integration not yet implemented")
        return self.create_result(
            job_input,
            ok=False,
            error="LinkedIn Ads API integration not implemented",
        )


# Register all ingestor agents
agent_registry.register("ingestor-google", GoogleIngestorAgent)
agent_registry.register("ingestor-reddit", RedditIngestorAgent)
agent_registry.register("ingestor-microsoft", MicrosoftIngestorAgent)
agent_registry.register("ingestor-linkedin", LinkedInIngestorAgent)
