"""Real Google Ads API integration for account discovery and data fetching."""

import logging
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleAdsAccountDiscovery:
    """Google Ads API client for discovering and analyzing accounts."""
    
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET") 
        self.refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
        self.developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
        
    async def search_accounts_by_domain(self, domain: str) -> List[Dict]:
        """Search for Google Ads accounts associated with a domain."""
        
        if not self._has_credentials():
            logger.warning("Google Ads credentials not configured")
            return []
        
        try:
            # Import Google Ads API client
            from google.ads.googleads.client import GoogleAdsClient
            
            # Create authenticated client
            credentials = {
                "developer_token": self.developer_token,
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "login_customer_id": self.login_customer_id,
                "use_proto_plus": True
            }
            
            client = GoogleAdsClient.load_from_dict(credentials)
            
            # Get accessible customer accounts
            accounts = await self._get_accessible_customers(client)
            
            # Filter accounts that might be related to the domain
            domain_accounts = []
            for account in accounts:
                if await self._is_domain_related(client, account, domain):
                    account_details = await self._get_account_details(client, account)
                    domain_accounts.append(account_details)
            
            return domain_accounts
            
        except Exception as e:
            logger.error(f"Google Ads account search failed: {e}")
            return []
    
    async def _get_accessible_customers(self, client) -> List[str]:
        """Get list of customer accounts accessible with current credentials."""
        
        try:
            customer_service = client.get_service("CustomerService")
            
            # Get accessible customers
            accessible_customers = customer_service.list_accessible_customers()
            
            return [customer.id for customer in accessible_customers.resource_names]
            
        except Exception as e:
            logger.error(f"Failed to get accessible customers: {e}")
            return []
    
    async def _is_domain_related(self, client, customer_id: str, domain: str) -> bool:
        """Check if a customer account is related to the given domain."""
        
        try:
            # Search for campaigns that might reference the domain
            query = f"""
                SELECT 
                    campaign.name,
                    campaign.final_url_suffix,
                    campaign.tracking_url_template
                FROM campaign 
                WHERE campaign.status = 'ENABLED'
                LIMIT 10
            """
            
            ga_service = client.get_service("GoogleAdsService")
            search_request = client.get_type("SearchGoogleAdsStreamRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            response = ga_service.search_stream(search_request)
            
            # Check if any campaigns reference the domain
            for batch in response:
                for row in batch.results:
                    campaign_name = row.campaign.name.lower()
                    
                    if (domain.lower() in campaign_name or
                        domain.lower() in (row.campaign.final_url_suffix or "") or
                        domain.lower() in (row.campaign.tracking_url_template or "")):
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Domain relation check failed for {customer_id}: {e}")
            return False
    
    async def _get_account_details(self, client, customer_id: str) -> Dict:
        """Get detailed information about a Google Ads account."""
        
        try:
            # Get customer information
            query = f"""
                SELECT 
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.status
                FROM customer
                LIMIT 1
            """
            
            ga_service = client.get_service("GoogleAdsService")
            search_request = client.get_type("SearchGoogleAdsStreamRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            response = ga_service.search_stream(search_request)
            
            customer_info = None
            for batch in response:
                for row in batch.results:
                    customer_info = row.customer
                    break
            
            if not customer_info:
                return {}
            
            # Get campaign count and spend
            campaigns_data = await self._get_campaigns_summary(client, customer_id)
            
            return {
                "account_id": customer_id,
                "account_name": customer_info.descriptive_name,
                "currency": customer_info.currency_code,
                "timezone": customer_info.time_zone,
                "status": customer_info.status.name.lower(),
                "campaigns_found": campaigns_data["count"],
                "total_spend": campaigns_data["spend"],
                "access_level": "full_access"
            }
            
        except Exception as e:
            logger.error(f"Failed to get account details for {customer_id}: {e}")
            return {
                "account_id": customer_id,
                "account_name": f"Google Ads Account {customer_id}",
                "status": "unknown",
                "campaigns_found": 0,
                "access_level": "limited"
            }
    
    async def _get_campaigns_summary(self, client, customer_id: str) -> Dict:
        """Get summary of campaigns for an account."""
        
        try:
            # Get last 30 days performance
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            query = f"""
                SELECT 
                    metrics.cost_micros,
                    campaign.id,
                    campaign.name,
                    campaign.status
                FROM campaign 
                WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
            """
            
            ga_service = client.get_service("GoogleAdsService")
            search_request = client.get_type("SearchGoogleAdsStreamRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            response = ga_service.search_stream(search_request)
            
            total_spend = 0
            campaign_count = 0
            campaign_ids = set()
            
            for batch in response:
                for row in batch.results:
                    campaign_ids.add(row.campaign.id)
                    total_spend += row.metrics.cost_micros / 1_000_000  # Convert micros to currency
            
            return {
                "count": len(campaign_ids),
                "spend": round(total_spend, 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get campaigns summary: {e}")
            return {"count": 0, "spend": 0.0}
    
    def _has_credentials(self) -> bool:
        """Check if all required Google Ads credentials are available."""
        return all([
            self.client_id,
            self.client_secret,
            self.refresh_token,
            self.developer_token
        ])


class RedditAccountDiscovery:
    """Reddit API client for account discovery."""
    
    def __init__(self):
        self.access_token = os.getenv("REDDIT_ACCESS_TOKEN")
        self.user_agent = "Synter/1.0 Account Discovery"
    
    async def search_accounts_by_domain(self, domain: str) -> List[Dict]:
        """Search for Reddit accounts/communities associated with a domain."""
        
        if not self.access_token:
            return []
        
        try:
            import aiohttp
            
            # Search for subreddits that might be related to the domain
            async with aiohttp.ClientSession() as session:
                # Search for the company/brand subreddit
                search_url = f"https://oauth.reddit.com/subreddits/search"
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "User-Agent": self.user_agent
                }
                
                params = {
                    "q": domain.replace('.com', '').replace('.', ' '),
                    "limit": 5,
                    "type": "subreddit"
                }
                
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        accounts = []
                        for subreddit in data.get("data", {}).get("children", []):
                            sub_data = subreddit["data"]
                            accounts.append({
                                "account_id": sub_data["name"],
                                "account_name": f"r/{sub_data['display_name']}",
                                "subscribers": sub_data.get("subscribers", 0),
                                "status": "community",
                                "access_level": "community_advertising"
                            })
                        
                        return accounts
            
            return []
            
        except Exception as e:
            logger.error(f"Reddit account search failed: {e}")
            return []


class XAccountDiscovery:
    """X (Twitter) API client for account discovery."""
    
    def __init__(self):
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    async def search_accounts_by_domain(self, domain: str) -> List[Dict]:
        """Search for X accounts associated with a domain."""
        
        if not self.bearer_token:
            return []
        
        try:
            import aiohttp
            
            # Search for Twitter accounts related to the domain
            company_name = domain.replace('.com', '').replace('.', '')
            
            async with aiohttp.ClientSession() as session:
                search_url = "https://api.twitter.com/2/users/by"
                headers = {
                    "Authorization": f"Bearer {self.bearer_token}"
                }
                
                params = {
                    "usernames": f"{company_name},{company_name}official,{company_name}inc",
                    "user.fields": "public_metrics,verified,description"
                }
                
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        accounts = []
                        for user in data.get("data", []):
                            accounts.append({
                                "account_id": user["id"],
                                "account_name": f"@{user['username']}",
                                "followers": user.get("public_metrics", {}).get("followers_count", 0),
                                "verified": user.get("verified", False),
                                "status": "active",
                                "access_level": "basic_access"
                            })
                        
                        return accounts
            
            return []
            
        except Exception as e:
            logger.error(f"X account search failed: {e}")
            return []
