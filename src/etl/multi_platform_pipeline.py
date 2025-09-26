"""Multi-platform ETL pipeline for Reddit, Microsoft, and LinkedIn Ads to BigQuery."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import pandas as pd

from ..ads.bigquery_client import create_bigquery_client_from_env
from ..integrations.reddit_ads import RedditAdsClient
from ..integrations.microsoft_ads import MicrosoftAdsClient

logger = logging.getLogger(__name__)


class MultiPlatformETLPipeline:
    """ETL Pipeline for multiple ad platforms to BigQuery synter_analytics."""
    
    def __init__(self):
        """Initialize the multi-platform ETL pipeline."""
        self.bq_client = create_bigquery_client_from_env()
        self.platforms_enabled = self._check_platform_availability()
        logger.info(f"Initialized ETL pipeline for platforms: {list(self.platforms_enabled.keys())}")
    
    def _check_platform_availability(self) -> Dict[str, bool]:
        """Check which platforms have proper API credentials configured."""
        platforms = {}
        
        # Reddit Ads
        reddit_enabled = bool(
            os.getenv("REDDIT_CLIENT_ID") and 
            os.getenv("REDDIT_CLIENT_SECRET") and
            os.getenv("MOCK_REDDIT", "true").lower() == "false"
        )
        platforms["reddit"] = reddit_enabled
        
        # Microsoft Ads  
        microsoft_enabled = bool(
            os.getenv("MICROSOFT_ADS_DEVELOPER_TOKEN") and
            os.getenv("MICROSOFT_ADS_CLIENT_ID") and
            os.getenv("MICROSOFT_ADS_CLIENT_SECRET") and
            os.getenv("MOCK_MICROSOFT", "true").lower() == "false"
        )
        platforms["microsoft"] = microsoft_enabled
        
        # LinkedIn Ads (currently mock only)
        linkedin_enabled = bool(
            os.getenv("LINKEDIN_CLIENT_ID") and
            os.getenv("LINKEDIN_CLIENT_SECRET") and
            os.getenv("MOCK_LINKEDIN", "true").lower() == "false"
        )
        platforms["linkedin"] = linkedin_enabled
        
        logger.info(f"Platform availability: {platforms}")
        return platforms
    
    async def sync_all_platforms(self, days_back: int = 7) -> Dict[str, Any]:
        """Sync data from all available platforms to BigQuery."""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Starting multi-platform ETL sync for date range: {start_date} to {end_date}")
        
        results = {
            "sync_started_at": datetime.utcnow().isoformat(),
            "date_range": {"start": start_date, "end": end_date},
            "platforms": {},
            "total_records": 0,
            "errors": []
        }
        
        # Run platform syncs in parallel
        sync_tasks = []
        
        if self.platforms_enabled.get("reddit"):
            sync_tasks.append(self._sync_reddit_data(start_date, end_date))
            
        if self.platforms_enabled.get("microsoft"):
            sync_tasks.append(self._sync_microsoft_data(start_date, end_date))
            
        if self.platforms_enabled.get("linkedin"):
            sync_tasks.append(self._sync_linkedin_data(start_date, end_date))
        
        # Execute all platform syncs
        if sync_tasks:
            platform_results = await asyncio.gather(*sync_tasks, return_exceptions=True)
            
            for i, result in enumerate(platform_results):
                platform = ["reddit", "microsoft", "linkedin"][i] if i < 3 else f"platform_{i}"
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to sync {platform} data: {result}")
                    results["errors"].append(f"{platform}: {str(result)}")
                    results["platforms"][platform] = {"status": "failed", "error": str(result)}
                else:
                    results["platforms"][platform] = result
                    results["total_records"] += result.get("records_written", 0)
        
        results["sync_completed_at"] = datetime.utcnow().isoformat()
        results["success"] = len(results["errors"]) == 0
        
        logger.info(f"Multi-platform ETL sync completed. Total records: {results['total_records']}")
        return results
    
    async def _sync_reddit_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Sync Reddit Ads data to BigQuery."""
        logger.info("🔴 Starting Reddit Ads data sync...")
        
        try:
            async with RedditAdsClient() as client:
                # Get all campaign metrics for date range
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                logger.info(f"Fetching Reddit campaign metrics from {start_date} to {end_date}")
                
                # Use the built-in get_all_campaign_metrics method
                metrics_list = await client.get_all_campaign_metrics(start_dt, end_dt)
                
                if not metrics_list:
                    logger.warning("No Reddit campaign metrics found")
                    return {
                        "platform": "reddit",
                        "status": "success",
                        "records_written": 0,
                        "campaigns_processed": 0
                    }
                
                logger.info(f"Retrieved metrics for {len(metrics_list)} Reddit campaigns")
                
                all_records = []
                
                for metrics in metrics_list:
                    # Transform to unified schema
                    record = self._transform_reddit_metrics(
                        metrics.date, "reddit_account", "Reddit Account", 
                        metrics.campaign_id, metrics.campaign_name, 
                        {
                            "impressions": metrics.impressions,
                            "clicks": metrics.clicks,
                            "spend": metrics.spend,
                            "conversions": metrics.conversions,
                            "ctr": metrics.ctr,
                            "cpc": metrics.cpc,
                            "conversion_rate": metrics.conversion_rate
                        }
                    )
                    all_records.append(record)
                
                if all_records:
                    # Load to BigQuery
                    df = pd.DataFrame(all_records)
                    records_written = await self._load_to_bigquery(df)
                    
                    logger.info(f"✅ Reddit sync completed: {records_written} records")
                    return {
                        "platform": "reddit",
                        "status": "success", 
                        "records_written": records_written,
                        "campaigns_processed": len(metrics_list)
                    }
                else:
                    logger.warning("⚠️ No Reddit records to sync")
                    return {
                        "platform": "reddit",
                        "status": "success",
                        "records_written": 0,
                        "campaigns_processed": len(metrics_list)
                    }
                
        except Exception as e:
            logger.error(f"❌ Reddit sync failed: {e}")
            raise
    
    async def _sync_microsoft_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Sync Microsoft Ads data to BigQuery."""
        logger.info("🔵 Starting Microsoft Ads data sync...")
        
        try:
            async with MicrosoftAdsClient() as client:
                # Get all campaign metrics for date range
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                logger.info(f"Fetching Microsoft campaign metrics from {start_date} to {end_date}")
                
                # Use the built-in get_all_campaign_metrics method
                metrics_list = await client.get_all_campaign_metrics(start_dt, end_dt)
                
                if not metrics_list:
                    logger.warning("No Microsoft campaign metrics found")
                    return {
                        "platform": "microsoft",
                        "status": "success",
                        "records_written": 0,
                        "campaigns_processed": 0
                    }
                
                logger.info(f"Retrieved metrics for {len(metrics_list)} Microsoft campaigns")
                
                all_records = []
                
                for metrics in metrics_list:
                    # Transform to unified schema
                    record = self._transform_microsoft_metrics(
                        metrics.date, "microsoft_account", "Microsoft Account",
                        metrics.campaign_id, metrics.campaign_name,
                        {
                            "impressions": metrics.impressions,
                            "clicks": metrics.clicks,
                            "spend": metrics.spend,
                            "conversions": metrics.conversions,
                            "ctr": metrics.ctr,
                            "cpc": metrics.cpc,
                            "conversion_rate": metrics.conversion_rate
                        }
                    )
                    all_records.append(record)
                
                if all_records:
                    # Load to BigQuery
                    df = pd.DataFrame(all_records)
                    records_written = await self._load_to_bigquery(df)
                    
                    logger.info(f"✅ Microsoft sync completed: {records_written} records")
                    return {
                        "platform": "microsoft",
                        "status": "success",
                        "records_written": records_written,
                        "campaigns_processed": len(metrics_list)
                    }
                else:
                    logger.warning("⚠️ No Microsoft records to sync")
                    return {
                        "platform": "microsoft", 
                        "status": "success",
                        "records_written": 0,
                        "campaigns_processed": len(metrics_list)
                    }
                
        except Exception as e:
            logger.error(f"❌ Microsoft sync failed: {e}")
            raise
    
    async def _sync_linkedin_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Sync LinkedIn Ads data to BigQuery."""
        logger.info("🔗 Starting LinkedIn Ads data sync...")
        
        mock_linkedin = os.getenv("MOCK_LINKEDIN", "true").lower() == "true"
        
        try:
            if mock_linkedin:
                # Generate mock data when in mock mode
                logger.info("LinkedIn in mock mode - generating mock data")
                all_records = []
                
                current_date = datetime.strptime(start_date, "%Y-%m-%d")
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                
                while current_date <= end_date_obj:
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    mock_record = {
                        "date": date_str,
                        "platform": "linkedin",
                        "account_id": "linkedin_demo_account",
                        "account_name": "Demo LinkedIn Ads Account",
                        "campaign_id": "linkedin_demo_campaign",
                        "campaign_name": "LinkedIn Demo Campaign",
                        "adgroup_id": None,
                        "adgroup_name": None,
                        "ad_id": None,
                        "ad_name": None,
                        "impressions": int(5000 + (current_date.day * 100)),
                        "clicks": int(150 + (current_date.day * 5)),
                        "spend": round(300.0 + (current_date.day * 10.5), 2),
                        "conversions": int(8 + (current_date.day * 0.5)),
                        "ctr": round((150 + (current_date.day * 5)) / (5000 + (current_date.day * 100)) * 100, 2),
                        "cpc": round((300.0 + (current_date.day * 10.5)) / (150 + (current_date.day * 5)), 2),
                        "cpm": round((300.0 + (current_date.day * 10.5)) / (5000 + (current_date.day * 100)) * 1000, 2),
                        "conversion_rate": round((8 + (current_date.day * 0.5)) / (150 + (current_date.day * 5)) * 100, 2),
                        "cost_per_conversion": round((300.0 + (current_date.day * 10.5)) / (8 + (current_date.day * 0.5)), 2),
                        "revenue": round((8 + (current_date.day * 0.5)) * 125.0, 2),
                        "roas": round(((8 + (current_date.day * 0.5)) * 125.0) / (300.0 + (current_date.day * 10.5)), 2),
                        "raw": {"source": "mock", "generated_at": datetime.utcnow().isoformat()},
                        "updated_at": datetime.utcnow()
                    }
                    all_records.append(mock_record)
                    current_date += timedelta(days=1)
                
                if all_records:
                    df = pd.DataFrame(all_records)
                    records_written = await self._load_to_bigquery(df)
                    
                    logger.info(f"✅ LinkedIn sync completed (mock): {records_written} records")
                    return {
                        "platform": "linkedin",
                        "status": "success (mock)",
                        "records_written": records_written,
                        "campaigns_processed": 1
                    }
            else:
                # Real LinkedIn API integration
                from ..integrations.linkedin_ads import LinkedInAdsClient
                
                async with LinkedInAdsClient() as client:
                    # Get ad accounts
                    accounts = await client.get_ad_accounts()
                    if not accounts:
                        logger.warning("No LinkedIn ad accounts found")
                        return {
                            "platform": "linkedin",
                            "status": "success",
                            "records_written": 0,
                            "campaigns_processed": 0
                        }
                    
                    logger.info(f"Found {len(accounts)} LinkedIn ad accounts")
                    
                    all_records = []
                    total_campaigns = 0
                    
                    for account in accounts:
                        account_id = account.get("id")
                        account_name = account.get("name", f"Account {account_id}")
                        
                        # Get campaigns for this account
                        campaigns = await client.get_campaigns(account_id)
                        total_campaigns += len(campaigns)
                        
                        for campaign in campaigns:
                            campaign_id = campaign.get("id")
                            campaign_name = campaign.get("name", f"Campaign {campaign_id}")
                            
                            try:
                                # Get analytics for this campaign
                                analytics = await client.get_campaign_analytics(campaign_id, start_date, end_date)
                                
                                # Transform daily analytics to records
                                for date_str, metrics in analytics.items():
                                    record = {
                                        "date": date_str,
                                        "platform": "linkedin",
                                        "account_id": account_id,
                                        "account_name": account_name,
                                        "campaign_id": campaign_id,
                                        "campaign_name": campaign_name,
                                        "adgroup_id": None,
                                        "adgroup_name": None,
                                        "ad_id": None,
                                        "ad_name": None,
                                        "impressions": metrics.get("impressions", 0),
                                        "clicks": metrics.get("clicks", 0),
                                        "spend": metrics.get("spend", 0.0),
                                        "conversions": metrics.get("conversions", 0),
                                        "ctr": metrics.get("ctr", 0.0),
                                        "cpc": metrics.get("cpc", 0.0),
                                        "cpm": metrics.get("cpm", 0.0),
                                        "conversion_rate": metrics.get("conversion_rate", 0.0),
                                        "cost_per_conversion": metrics.get("cost_per_conversion", 0.0),
                                        "revenue": metrics.get("conversions", 0) * 125.0,  # Assume $125 per conversion
                                        "roas": round((metrics.get("conversions", 0) * 125.0) / max(metrics.get("spend", 1), 1), 2),
                                        "raw": metrics,
                                        "updated_at": datetime.utcnow()
                                    }
                                    all_records.append(record)
                                    
                            except Exception as e:
                                logger.error(f"Failed to get analytics for LinkedIn campaign {campaign_id}: {e}")
                                continue
                    
                    if all_records:
                        df = pd.DataFrame(all_records)
                        records_written = await self._load_to_bigquery(df)
                        
                        logger.info(f"✅ LinkedIn sync completed: {records_written} records")
                        return {
                            "platform": "linkedin",
                            "status": "success",
                            "records_written": records_written,
                            "campaigns_processed": total_campaigns
                        }
                    else:
                        logger.warning("⚠️ No LinkedIn records to sync")
                        return {
                            "platform": "linkedin",
                            "status": "success",
                            "records_written": 0,
                            "campaigns_processed": total_campaigns
                        }
            
            return {
                "platform": "linkedin",
                "status": "success",
                "records_written": 0,
                "campaigns_processed": 0
            }
                
        except Exception as e:
            logger.error(f"❌ LinkedIn sync failed: {e}")
            raise
    
    def _transform_reddit_metrics(self, date_str: str, account_id: str, account_name: str,
                                 campaign_id: str, campaign_name: str, metrics: Dict) -> Dict:
        """Transform Reddit metrics to unified ad_metrics schema."""
        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        spend = metrics.get("spend", 0.0)
        conversions = metrics.get("conversions", 0)
        
        return {
            "date": date_str,
            "platform": "reddit",
            "account_id": account_id,
            "account_name": account_name,
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "adgroup_id": None,
            "adgroup_name": None,
            "ad_id": None,
            "ad_name": None,
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "conversions": conversions,
            "ctr": round((clicks / impressions * 100), 2) if impressions > 0 else 0,
            "cpc": round((spend / clicks), 2) if clicks > 0 else 0,
            "cpm": round((spend / impressions * 1000), 2) if impressions > 0 else 0,
            "conversion_rate": round((conversions / clicks * 100), 2) if clicks > 0 else 0,
            "cost_per_conversion": round((spend / conversions), 2) if conversions > 0 else 0,
            "revenue": round(conversions * 100.0, 2),  # Assume $100 per conversion
            "roas": round((conversions * 100.0 / spend), 2) if spend > 0 else 0,
            "raw": metrics,
            "updated_at": datetime.utcnow()
        }
    
    def _transform_microsoft_metrics(self, date_str: str, account_id: str, account_name: str,
                                   campaign_id: str, campaign_name: str, metrics: Dict) -> Dict:
        """Transform Microsoft Ads metrics to unified ad_metrics schema."""
        impressions = metrics.get("Impressions", 0)
        clicks = metrics.get("Clicks", 0)
        spend = float(metrics.get("Spend", 0))
        conversions = metrics.get("Conversions", 0)
        
        return {
            "date": date_str,
            "platform": "microsoft",
            "account_id": str(account_id),
            "account_name": account_name,
            "campaign_id": str(campaign_id),
            "campaign_name": campaign_name,
            "adgroup_id": None,
            "adgroup_name": None,
            "ad_id": None,
            "ad_name": None,
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "conversions": conversions,
            "ctr": round((clicks / impressions * 100), 2) if impressions > 0 else 0,
            "cpc": round((spend / clicks), 2) if clicks > 0 else 0,
            "cpm": round((spend / impressions * 1000), 2) if impressions > 0 else 0,
            "conversion_rate": round((conversions / clicks * 100), 2) if clicks > 0 else 0,
            "cost_per_conversion": round((spend / conversions), 2) if conversions > 0 else 0,
            "revenue": round(conversions * 120.0, 2),  # Assume $120 per conversion
            "roas": round((conversions * 120.0 / spend), 2) if spend > 0 else 0,
            "raw": metrics,
            "updated_at": datetime.utcnow()
        }
    
    async def _load_to_bigquery(self, df: pd.DataFrame) -> int:
        """Load DataFrame to BigQuery ad_metrics table."""
        try:
            # Ensure all required columns are present
            required_columns = [
                "date", "platform", "account_id", "account_name",
                "campaign_id", "campaign_name", "adgroup_id", "adgroup_name", 
                "ad_id", "ad_name", "impressions", "clicks", "spend", 
                "conversions", "ctr", "cpc", "cpm", "conversion_rate",
                "cost_per_conversion", "revenue", "roas", "raw", "updated_at"
            ]
            
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Convert date strings to date objects
            df["date"] = pd.to_datetime(df["date"]).dt.date
            
            # Insert to BigQuery
            self.bq_client.insert_dataframe("ad_metrics", df)
            
            logger.info(f"Successfully loaded {len(df)} records to BigQuery ad_metrics table")
            return len(df)
            
        except Exception as e:
            logger.error(f"Failed to load data to BigQuery: {e}")
            raise


# Convenience functions for manual execution
async def sync_reddit_to_bigquery(days_back: int = 7) -> Dict[str, Any]:
    """Sync Reddit Ads data to BigQuery."""
    pipeline = MultiPlatformETLPipeline()
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    return await pipeline._sync_reddit_data(start_date, end_date)


async def sync_microsoft_to_bigquery(days_back: int = 7) -> Dict[str, Any]:
    """Sync Microsoft Ads data to BigQuery.""" 
    pipeline = MultiPlatformETLPipeline()
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    return await pipeline._sync_microsoft_data(start_date, end_date)


async def sync_all_platforms_to_bigquery(days_back: int = 7) -> Dict[str, Any]:
    """Sync all available platforms to BigQuery."""
    pipeline = MultiPlatformETLPipeline()
    return await pipeline.sync_all_platforms(days_back)
