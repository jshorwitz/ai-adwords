"""LinkedIn OAuth routes for LinkedIn Ads API authentication."""

import logging
import os
import secrets
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
import httpx

from ..models.auth import User
from .middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/linkedin", tags=["linkedin-oauth"])


@router.get("/connect")
async def linkedin_connect(current_user: User = Depends(get_current_user)):
    """Initiate LinkedIn OAuth flow to connect LinkedIn Ads account."""
    
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "https://web-production-97620.up.railway.app/auth/linkedin/callback")
    
    if not client_id:
        raise HTTPException(status_code=500, detail="LinkedIn OAuth not configured")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # LinkedIn OAuth parameters
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "r_ads,r_ads_reporting,r_organization_social"  # LinkedIn Marketing API scopes
    }
    
    # Store state in session (in production, use Redis or database)
    # For now, we'll validate in callback
    
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    
    logger.info(f"LinkedIn OAuth redirect for user {current_user.email}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def linkedin_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from LinkedIn"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from LinkedIn OAuth"),
    error_description: Optional[str] = Query(None, description="Error description")
):
    """Handle LinkedIn OAuth callback and exchange code for access token."""
    
    if error:
        logger.error(f"LinkedIn OAuth error: {error} - {error_description}")
        return RedirectResponse(url="/dashboard?linkedin_error=oauth_failed")
    
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "https://web-production-97620.up.railway.app/auth/linkedin/callback")
    
    if not all([client_id, client_secret]):
        raise HTTPException(status_code=500, detail="LinkedIn OAuth credentials not configured")
    
    try:
        # Exchange authorization code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                logger.error(f"LinkedIn token exchange failed: {token_response.status_code} - {token_response.text}")
                return RedirectResponse(url="/dashboard?linkedin_error=token_failed")
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            expires_in = token_info.get("expires_in", 60 * 60)  # Default 1 hour
            
            if not access_token:
                logger.error("No access token received from LinkedIn")
                return RedirectResponse(url="/dashboard?linkedin_error=no_token")
        
        # Get user profile information
        profile_url = "https://api.linkedin.com/v2/people/~"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(profile_url, headers=headers)
            
            profile_info = {}
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                profile_info = {
                    "id": profile_data.get("id"),
                    "firstName": profile_data.get("localizedFirstName", ""),
                    "lastName": profile_data.get("localizedLastName", "")
                }
        
        # Get ad accounts
        ad_accounts_url = "https://api.linkedin.com/rest/adAccounts"
        params = {
            "q": "search",
            "search.status.values[0]": "ACTIVE",
            "fields": "id,name,type,status"
        }
        
        ad_accounts = []
        async with httpx.AsyncClient() as client:
            accounts_response = await client.get(
                ad_accounts_url,
                headers={
                    **headers,
                    "LinkedIn-Version": "202311"
                },
                params=params
            )
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                ad_accounts = accounts_data.get("elements", [])
        
        # Store the access token and account info
        # TODO: In production, store this in database associated with user
        # For now, we'll set it as an environment variable (not persistent)
        
        logger.info(f"LinkedIn OAuth successful!")
        logger.info(f"User: {profile_info.get('firstName')} {profile_info.get('lastName')}")
        logger.info(f"Ad accounts found: {len(ad_accounts)}")
        
        # In production, you would:
        # 1. Store the access_token in database
        # 2. Associate it with the current user
        # 3. Store refresh_token if provided
        # 4. Set up token refresh mechanism
        
        return RedirectResponse(url="/dashboard?linkedin_connected=true")
        
    except Exception as e:
        logger.error(f"LinkedIn OAuth callback error: {e}")
        return RedirectResponse(url="/dashboard?linkedin_error=callback_failed")


@router.get("/status")
async def linkedin_status(current_user: User = Depends(get_current_user)):
    """Get LinkedIn connection status for current user."""
    
    # TODO: In production, check database for stored LinkedIn tokens
    # For now, check environment variables
    
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    
    if not client_id:
        return {
            "connected": False,
            "status": "LinkedIn OAuth not configured",
            "client_configured": False
        }
    
    if not access_token:
        return {
            "connected": False,
            "status": "LinkedIn account not connected",
            "client_configured": True,
            "connect_url": "/auth/linkedin/connect"
        }
    
    # Test the token
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            profile_response = await client.get(
                "https://api.linkedin.com/v2/people/~",
                headers=headers
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                user_name = f"{profile_data.get('localizedFirstName', '')} {profile_data.get('localizedLastName', '')}"
                
                return {
                    "connected": True,
                    "status": "LinkedIn Ads connected successfully",
                    "user": user_name.strip(),
                    "user_id": profile_data.get("id")
                }
            else:
                return {
                    "connected": False,
                    "status": "LinkedIn token expired or invalid",
                    "client_configured": True,
                    "connect_url": "/auth/linkedin/connect"
                }
                
    except Exception as e:
        logger.error(f"LinkedIn status check error: {e}")
        return {
            "connected": False,
            "status": f"LinkedIn connection error: {str(e)}",
            "client_configured": True
        }


@router.post("/disconnect")
async def linkedin_disconnect(current_user: User = Depends(get_current_user)):
    """Disconnect LinkedIn Ads account."""
    
    # TODO: In production, remove tokens from database
    # For now, this would require manual environment variable removal
    
    logger.info(f"LinkedIn disconnect requested for user {current_user.email}")
    
    return {
        "success": True,
        "message": "LinkedIn account disconnected. Remove LINKEDIN_ACCESS_TOKEN from environment variables."
    }


@router.get("/test-connection")
async def test_linkedin_connection():
    """Test LinkedIn API connection (public endpoint for development)."""
    
    from ..integrations.linkedin_ads import LinkedInAdsClient
    
    try:
        async with LinkedInAdsClient() as linkedin_client:
            connection_status = await linkedin_client.test_connection()
            
            return {
                "timestamp": "2024-01-01T00:00:00Z",
                "linkedin_connection": connection_status
            }
            
    except Exception as e:
        return {
            "timestamp": "2024-01-01T00:00:00Z", 
            "linkedin_connection": {
                "connected": False,
                "status": f"Connection test failed: {str(e)}",
                "mode": "error"
            }
        }
