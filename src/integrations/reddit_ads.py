"""Reddit Ads API integration for campaign data."""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RedditAdMetrics(BaseModel):
    """Reddit Ads metrics data model."""
    campaign_id: str
    campaign_name: str
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    conversion_rate: float = 0.0
    date: str


class RedditAdsClient:
    """Reddit Ads API client for retrieving campaign performance data."""
    
    BASE_URL = "https://ads-api.reddit.com/api/v2.0"
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET") 
        self.access_token = None
        self.session = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit API credentials not configured")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate with Reddit Ads API using OAuth2 client credentials flow."""
        try:
            # Reddit uses basic auth for client credentials
            auth_headers = {
                'Authorization': f'Basic {self._encode_credentials()}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'AI-AdWords/1.0'
            }
            
            auth_data = {
                'grant_type': 'client_credentials',
                'scope': 'ads_read'
            }
            
            async with self.session.post(
                'https://www.reddit.com/api/v1/access_token',
                headers=auth_headers,
                data=urlencode(auth_data)
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get('access_token')
                    logger.info("✅ Reddit Ads API authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Reddit auth failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Reddit authentication error: {e}")
            return False
    
    def _encode_credentials(self) -> str:
        """Encode client credentials for basic auth."""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    async def get_campaigns(self) -> List[Dict]:
        """Get list of campaigns."""
        if not self.access_token:
            await self.authenticate()
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'AI-AdWords/1.0'
        }
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}/campaigns",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"❌ Failed to fetch campaigns: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"❌ Error fetching campaigns: {e}")
            return []
    
    async def get_campaign_metrics(
        self, 
        campaign_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[RedditAdMetrics]:
        """Get metrics for a specific campaign."""
        if not self.access_token:
            await self.authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': 'AI-AdWords/1.0'
        }
        
        params = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'metrics': 'impressions,clicks,spend,conversions'
        }
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}/campaigns/{campaign_id}/metrics",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    metrics_data = data.get('data', {})
                    
                    # Calculate derived metrics
                    impressions = metrics_data.get('impressions', 0)
                    clicks = metrics_data.get('clicks', 0)
                    spend = float(metrics_data.get('spend', 0))
                    conversions = metrics_data.get('conversions', 0)
                    
                    ctr = (clicks / impressions * 100) if impressions > 0 else 0
                    cpc = (spend / clicks) if clicks > 0 else 0
                    conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
                    
                    return RedditAdMetrics(
                        campaign_id=campaign_id,
                        campaign_name=metrics_data.get('campaign_name', f'Campaign {campaign_id}'),
                        impressions=impressions,
                        clicks=clicks,
                        spend=spend,
                        conversions=conversions,
                        ctr=round(ctr, 2),
                        cpc=round(cpc, 2),
                        conversion_rate=round(conversion_rate, 2),
                        date=start_date.strftime('%Y-%m-%d')
                    )
                else:
                    logger.error(f"❌ Failed to fetch metrics for campaign {campaign_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error fetching metrics for campaign {campaign_id}: {e}")
            return None
    
    async def get_all_campaign_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[RedditAdMetrics]:
        """Get metrics for all campaigns."""
        logger.info(f"📊 Fetching Reddit campaign metrics from {start_date} to {end_date}")
        
        campaigns = await self.get_campaigns()
        if not campaigns:
            logger.warning("⚠️ No Reddit campaigns found")
            return []
        
        metrics_list = []
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            if campaign_id:
                metrics = await self.get_campaign_metrics(campaign_id, start_date, end_date)
                if metrics:
                    # Update campaign name from campaign data
                    metrics.campaign_name = campaign.get('name', metrics.campaign_name)
                    metrics_list.append(metrics)
                
                # Add small delay to respect rate limits
                await asyncio.sleep(0.1)
        
        logger.info(f"✅ Retrieved metrics for {len(metrics_list)} Reddit campaigns")
        return metrics_list


async def test_reddit_ads_integration():
    """Test Reddit Ads API integration."""
    logger.info("🧪 Testing Reddit Ads integration...")
    
    try:
        async with RedditAdsClient() as client:
            # Test authentication
            if not client.access_token:
                logger.error("❌ Authentication failed")
                return False
            
            # Test fetching campaigns
            campaigns = await client.get_campaigns()
            logger.info(f"📊 Found {len(campaigns)} campaigns")
            
            # Test metrics for last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            metrics = await client.get_all_campaign_metrics(start_date, end_date)
            logger.info(f"📈 Retrieved metrics for {len(metrics)} campaigns")
            
            for metric in metrics:
                logger.info(f"  {metric.campaign_name}: ${metric.spend:.2f} spend, {metric.clicks} clicks")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Reddit Ads test failed: {e}")
        return False


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Run test
    asyncio.run(test_reddit_ads_integration())
