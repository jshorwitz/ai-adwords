"""Google Ads API client factory and authentication."""

from typing import Optional


class GoogleAdsClient:
    """Google Ads API client with OAuth refresh token management."""
    
    def __init__(
        self,
        developer_token: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        login_customer_id: Optional[str] = None,
    ):
        """Initialize Google Ads client.
        
        Args:
            developer_token: Google Ads API developer token
            refresh_token: OAuth refresh token
            client_id: OAuth client ID
            client_secret: OAuth client secret
            login_customer_id: MCC customer ID (digits only)
        """
        pass
