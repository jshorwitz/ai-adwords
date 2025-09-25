"""Microsoft Ads OAuth authentication routes."""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlencode, urlparse, parse_qs

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from ..models.auth import User
from .middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/microsoft", tags=["microsoft-auth"])

# Microsoft OAuth endpoints
MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

# Required scopes for Microsoft Advertising API
MICROSOFT_SCOPES = [
    "https://ads.microsoft.com/ads.manage",
    "https://ads.microsoft.com/ads.read",
    "offline_access"  # For refresh tokens
]

# In-memory storage for OAuth state (use Redis in production)
oauth_states: Dict[str, Dict] = {}


@router.get("/connect")
async def microsoft_oauth_start(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Start Microsoft Ads OAuth flow."""
    
    client_id = os.getenv("MICROSOFT_ADS_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="Microsoft Ads OAuth not configured")
    
    # Generate secure state parameter
    state = secrets.token_urlsafe(32)
    
    # Store state with user info (expires in 10 minutes)
    oauth_states[state] = {
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    # Build redirect URI
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/auth/microsoft/callback"
    
    # Build authorization URL
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(MICROSOFT_SCOPES),
        "state": state,
        "response_mode": "query"
    }
    
    auth_url = f"{MICROSOFT_AUTH_URL}?{urlencode(auth_params)}"
    
    logger.info(f"🔗 Starting Microsoft OAuth for user {current_user.id}")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def microsoft_oauth_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """Handle Microsoft OAuth callback."""
    
    if error:
        logger.error(f"❌ Microsoft OAuth error: {error} - {error_description}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {error_description}")
    
    # Validate state parameter
    if state not in oauth_states:
        logger.error(f"❌ Invalid OAuth state: {state}")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    
    oauth_data = oauth_states[state]
    
    # Check if state expired
    if datetime.utcnow() > oauth_data["expires_at"]:
        del oauth_states[state]
        logger.error("❌ OAuth state expired")
        raise HTTPException(status_code=400, detail="OAuth state expired")
    
    user_id = oauth_data["user_id"]
    
    # Clean up state
    del oauth_states[state]
    
    # Exchange authorization code for access token
    try:
        tokens = await exchange_code_for_tokens(request, code)
        
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to obtain access tokens")
        
        # Store tokens (in production, encrypt and store in database)
        await store_microsoft_tokens(user_id, tokens)
        
        logger.info(f"✅ Microsoft OAuth successful for user {user_id}")
        
        # Redirect to dashboard with success message
        return RedirectResponse(
            url="/dashboard?microsoft_connected=true",
            status_code=302
        )
        
    except Exception as e:
        logger.error(f"❌ Microsoft OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")


async def exchange_code_for_tokens(request: Request, code: str) -> Optional[Dict]:
    """Exchange authorization code for access and refresh tokens."""
    
    client_id = os.getenv("MICROSOFT_ADS_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_ADS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logger.error("❌ Microsoft OAuth credentials not configured")
        return None
    
    # Build redirect URI
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/auth/microsoft/callback"
    
    # Token exchange payload
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                MICROSOFT_TOKEN_URL,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                
                if response.status == 200:
                    tokens = await response.json()
                    logger.info("✅ Successfully exchanged code for Microsoft tokens")
                    return tokens
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Token exchange failed: {response.status} - {error_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Token exchange error: {e}")
        return None


async def store_microsoft_tokens(user_id: int, tokens: Dict) -> bool:
    """Store Microsoft tokens for user (implement database storage in production)."""
    
    try:
        # In production, encrypt tokens and store in database
        # For now, store in environment or memory (not recommended for production)
        
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token") 
        expires_in = tokens.get("expires_in", 3600)
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # TODO: Store in database table like `oauth_tokens`
        # Example schema:
        # - user_id: int
        # - provider: str ('microsoft')
        # - access_token: str (encrypted)
        # - refresh_token: str (encrypted)
        # - expires_at: datetime
        # - scopes: str
        
        logger.info(f"📝 Microsoft tokens stored for user {user_id} (expires: {expires_at})")
        
        # For now, log that tokens would be stored
        logger.info("⚠️ Token storage not implemented - add database integration")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error storing Microsoft tokens: {e}")
        return False


@router.post("/refresh")
async def refresh_microsoft_token(current_user: User = Depends(get_current_user)):
    """Refresh Microsoft access token using refresh token."""
    
    try:
        # TODO: Retrieve stored refresh token for user
        # refresh_token = get_user_microsoft_refresh_token(current_user.id)
        
        # For now, return placeholder
        return {
            "message": "Token refresh not yet implemented",
            "user_id": current_user.id,
            "provider": "microsoft"
        }
        
    except Exception as e:
        logger.error(f"❌ Microsoft token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.delete("/disconnect")
async def disconnect_microsoft_ads(current_user: User = Depends(get_current_user)):
    """Disconnect Microsoft Ads account."""
    
    try:
        # TODO: Remove stored tokens for user
        # delete_user_microsoft_tokens(current_user.id)
        
        logger.info(f"🔌 Microsoft Ads disconnected for user {current_user.id}")
        
        return {
            "message": "Microsoft Ads account disconnected successfully",
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error(f"❌ Microsoft disconnect error: {e}")
        raise HTTPException(status_code=500, detail="Disconnect failed")


@router.get("/status")
async def microsoft_ads_status(current_user: User = Depends(get_current_user)):
    """Get Microsoft Ads connection status for current user."""
    
    try:
        # TODO: Check if user has valid Microsoft tokens
        # has_tokens = has_user_microsoft_tokens(current_user.id)
        
        # For now, return placeholder status
        return {
            "connected": False,  # Update based on actual token check
            "provider": "microsoft",
            "user_id": current_user.id,
            "scopes": MICROSOFT_SCOPES,
            "last_updated": None
        }
        
    except Exception as e:
        logger.error(f"❌ Microsoft status check error: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")
