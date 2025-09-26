"""Platform connection status API endpoints."""

import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..models.auth import User
from .middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platforms", tags=["platform-status"])


class PlatformStatus(BaseModel):
    platform: str
    connected: bool
    status: str
    mock_mode: bool
    connect_url: str | None = None


class AllPlatformsStatus(BaseModel):
    google: PlatformStatus
    reddit: PlatformStatus
    microsoft: PlatformStatus
    linkedin: PlatformStatus


@router.get("/status", response_model=AllPlatformsStatus)
async def get_all_platform_status(current_user: User = Depends(get_current_user)):
    """Get connection status for all advertising platforms."""
    
    try:
        # Google Ads status
        google_status = _check_google_ads_status()
        
        # Reddit Ads status
        reddit_status = _check_reddit_ads_status()
        
        # Microsoft Ads status
        microsoft_status = _check_microsoft_ads_status()
        
        # LinkedIn Ads status
        linkedin_status = _check_linkedin_ads_status()
        
        return AllPlatformsStatus(
            google=google_status,
            reddit=reddit_status,
            microsoft=microsoft_status,
            linkedin=linkedin_status
        )
        
    except Exception as e:
        logger.error(f"Failed to get platform status: {e}")
        # Return all platforms as disconnected on error
        return AllPlatformsStatus(
            google=PlatformStatus(platform="google", connected=False, status="Error checking status", mock_mode=True),
            reddit=PlatformStatus(platform="reddit", connected=False, status="Error checking status", mock_mode=True),
            microsoft=PlatformStatus(platform="microsoft", connected=False, status="Error checking status", mock_mode=True),
            linkedin=PlatformStatus(platform="linkedin", connected=False, status="Error checking status", mock_mode=True)
        )


def _check_google_ads_status() -> PlatformStatus:
    """Check Google Ads connection status."""
    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    
    if not all([client_id, client_secret, developer_token, customer_id]):
        return PlatformStatus(
            platform="google",
            connected=False,
            status="Google Ads credentials not configured",
            mock_mode=True,
            connect_url="/auth/google/connect"
        )
    
    # TODO: Test actual Google Ads API connection
    # For now, assume connected if credentials are present
    return PlatformStatus(
        platform="google",
        connected=True,
        status="Google Ads connected",
        mock_mode=False
    )


def _check_reddit_ads_status() -> PlatformStatus:
    """Check Reddit Ads connection status."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    mock_mode = os.getenv("MOCK_REDDIT", "true").lower() == "true"
    
    if not client_id or not client_secret:
        return PlatformStatus(
            platform="reddit",
            connected=False,
            status="Reddit API credentials not configured",
            mock_mode=True,
            connect_url="/auth/reddit/connect"
        )
    
    if mock_mode:
        return PlatformStatus(
            platform="reddit",
            connected=False,
            status="Reddit in mock mode - credentials configured",
            mock_mode=True,
            connect_url="/auth/reddit/connect"
        )
    
    # TODO: Test actual Reddit API connection
    # For now, assume connected if credentials are present and not in mock mode
    return PlatformStatus(
        platform="reddit",
        connected=True,
        status="Reddit Ads connected",
        mock_mode=False
    )


def _check_microsoft_ads_status() -> PlatformStatus:
    """Check Microsoft Ads connection status."""
    client_id = os.getenv("MICROSOFT_ADS_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_ADS_CLIENT_SECRET")
    developer_token = os.getenv("MICROSOFT_ADS_DEVELOPER_TOKEN")
    mock_mode = os.getenv("MOCK_MICROSOFT", "true").lower() == "true"
    
    if not all([client_id, client_secret, developer_token]):
        return PlatformStatus(
            platform="microsoft",
            connected=False,
            status="Microsoft Ads credentials not configured",
            mock_mode=True,
            connect_url="/auth/microsoft/connect"
        )
    
    if mock_mode:
        return PlatformStatus(
            platform="microsoft",
            connected=False,
            status="Microsoft in mock mode - credentials configured",
            mock_mode=True,
            connect_url="/auth/microsoft/connect"
        )
    
    # TODO: Test actual Microsoft Ads API connection
    return PlatformStatus(
        platform="microsoft",
        connected=True,
        status="Microsoft Ads connected",
        mock_mode=False
    )


def _check_linkedin_ads_status() -> PlatformStatus:
    """Check LinkedIn Ads connection status."""
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    mock_mode = os.getenv("MOCK_LINKEDIN", "true").lower() == "true"
    
    if not client_id or not client_secret:
        return PlatformStatus(
            platform="linkedin",
            connected=False,
            status="LinkedIn API credentials not configured",
            mock_mode=True,
            connect_url="/auth/linkedin/connect"
        )
    
    if mock_mode:
        return PlatformStatus(
            platform="linkedin",
            connected=False,
            status="LinkedIn in mock mode - credentials configured",
            mock_mode=True,
            connect_url="/auth/linkedin/connect"
        )
    
    if not access_token:
        return PlatformStatus(
            platform="linkedin",
            connected=False,
            status="LinkedIn OAuth required",
            mock_mode=False,
            connect_url="/auth/linkedin/connect"
        )
    
    # TODO: Test actual LinkedIn API connection
    return PlatformStatus(
        platform="linkedin",
        connected=True,
        status="LinkedIn Ads connected",
        mock_mode=False
    )
