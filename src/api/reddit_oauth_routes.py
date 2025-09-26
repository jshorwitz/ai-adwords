"""Reddit OAuth routes for Reddit Ads API authentication."""

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

router = APIRouter(prefix="/auth/reddit", tags=["reddit-oauth"])


@router.get("/connect")
async def reddit_connect(current_user: User = Depends(get_current_user)):
    """Initiate Reddit OAuth flow to connect Reddit Ads account."""
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    redirect_uri = os.getenv("REDDIT_REDIRECT_URI", "https://web-production-97620.up.railway.app/auth/reddit/callback")
    
    if not client_id:
        raise HTTPException(status_code=500, detail="Reddit OAuth not configured")
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Reddit OAuth parameters for advertising API access
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "read ads",  # Required scopes for Reddit Ads API
        "duration": "permanent"
    }
    
    auth_url = f"https://www.reddit.com/api/v1/authorize?{urlencode(params)}"
    
    logger.info(f"Reddit OAuth redirect for user {current_user.email}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def reddit_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Reddit"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from Reddit OAuth")
):
    """Handle Reddit OAuth callback and exchange code for access token."""
    
    if error:
        logger.error(f"Reddit OAuth error: {error}")
        return RedirectResponse(url="/dashboard?reddit_error=oauth_failed")
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    redirect_uri = os.getenv("REDDIT_REDIRECT_URI", "https://web-production-97620.up.railway.app/auth/reddit/callback")
    
    if not all([client_id, client_secret]):
        raise HTTPException(status_code=500, detail="Reddit OAuth credentials not configured")
    
    try:
        # Exchange authorization code for access token
        token_url = "https://www.reddit.com/api/v1/access_token"
        
        # Reddit requires Basic Auth for token exchange
        import base64
        auth_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data=token_data,
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "SynterApp/1.0"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Reddit token exchange failed: {token_response.status_code} - {token_response.text}")
                return RedirectResponse(url="/dashboard?reddit_error=token_failed")
            
            token_info = token_response.json()
            access_token = token_info.get("access_token")
            refresh_token = token_info.get("refresh_token")
            expires_in = token_info.get("expires_in", 3600)
            
            if not access_token:
                logger.error("No access token received from Reddit")
                return RedirectResponse(url="/dashboard?reddit_error=no_token")
        
        # Test the access token by getting user info
        me_url = "https://oauth.reddit.com/api/v1/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "SynterApp/1.0"
        }
        
        user_info = {}
        async with httpx.AsyncClient() as client:
            me_response = await client.get(me_url, headers=headers)
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                user_info = {
                    "username": user_data.get("name", ""),
                    "id": user_data.get("id", "")
                }
        
        # Store the access token and account info
        # TODO: In production, store this in database associated with user
        # For now, log the successful connection
        
        logger.info(f"Reddit OAuth successful!")
        logger.info(f"User: {user_info.get('username', 'Unknown')}")
        logger.info(f"Access token expires in: {expires_in} seconds")
        
        # In production, you would:
        # 1. Store the access_token and refresh_token in database
        # 2. Associate it with the current user
        # 3. Set up token refresh mechanism
        # 4. Store Reddit ad account information
        
        return RedirectResponse(url="/dashboard?reddit_connected=true")
        
    except Exception as e:
        logger.error(f"Reddit OAuth callback error: {e}")
        return RedirectResponse(url="/dashboard?reddit_error=callback_failed")


@router.get("/status")
async def reddit_status(current_user: User = Depends(get_current_user)):
    """Get Reddit connection status for current user."""
    
    # TODO: In production, check database for stored Reddit tokens
    # For now, check environment variables and mock status
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    mock_mode = os.getenv("MOCK_REDDIT", "true").lower() == "true"
    
    if not client_id or not client_secret:
        return {
            "connected": False,
            "status": "Reddit OAuth not configured",
            "client_configured": False
        }
    
    if mock_mode:
        return {
            "connected": False,
            "status": "Reddit in mock mode",
            "client_configured": True,
            "mock_mode": True,
            "connect_url": "/auth/reddit/connect"
        }
    
    # TODO: Test actual stored token
    return {
        "connected": False,
        "status": "Reddit account not connected",
        "client_configured": True,
        "connect_url": "/auth/reddit/connect"
    }


@router.post("/disconnect")
async def reddit_disconnect(current_user: User = Depends(get_current_user)):
    """Disconnect Reddit Ads account."""
    
    # TODO: In production, remove tokens from database
    
    logger.info(f"Reddit disconnect requested for user {current_user.email}")
    
    return {
        "success": True,
        "message": "Reddit account disconnected."
    }
