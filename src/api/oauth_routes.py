"""OAuth authentication routes for Google, Reddit, and X/Twitter."""

import logging
import os
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Dict, Any

from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["oauth"])

# Demo storage (same as auth_simple.py)
from .auth_simple import DEMO_USERS, DEMO_SESSIONS


def generate_session_token() -> str:
    """Generate session token."""
    import secrets
    return secrets.token_urlsafe(32)


@router.get("/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth flow for provider (google, reddit, twitter)."""
    
    try:
        if provider not in ['google', 'reddit', 'twitter']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
        
        # For demo mode, simulate OAuth without real providers
        if is_demo_mode():
            return await simulate_oauth_flow(provider, request)
        
        # Get OAuth client
        client = oauth.create_client(provider)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth client for {provider} not configured"
            )
        
        # Get redirect URI
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = get_oauth_redirect_uri(provider, base_url)
        
        # Redirect to OAuth provider
        return await client.authorize_redirect(request, redirect_uri)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"OAuth initiation failed for {provider}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth initiation failed: {str(e)}"
        )


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, request: Request, response: Response):
    """Handle OAuth callback from provider."""
    
    try:
        if provider not in ['google', 'reddit', 'twitter']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
        
        # For demo mode, simulate successful OAuth
        if is_demo_mode():
            return await handle_demo_oauth_callback(provider, request, response)
        
        # Get OAuth client
        client = oauth.create_client(provider)
        
        # Get token and user info
        token = await client.authorize_access_token(request)
        
        if provider == 'google':
            user_data = token.get('userinfo')
        elif provider == 'reddit':
            # For Reddit, need to make API call to get user info
            resp = await client.get('https://oauth.reddit.com/api/v1/me', token=token)
            user_data = resp.json()
        elif provider == 'twitter':
            # For Twitter, get user info from API
            resp = await client.get('https://api.twitter.com/1.1/account/verify_credentials.json', token=token)
            user_data = resp.json()
        else:
            user_data = {}
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from OAuth provider"
            )
        
        # Extract user info
        user_info = extract_user_info(provider, user_data)
        
        # Create or link user account
        user = await create_or_link_oauth_user(provider, user_info, token)
        
        # Create session
        session_token = generate_session_token()
        DEMO_SESSIONS[session_token] = {
            "user_id": user["id"],
            "email": user["email"],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Set session cookie
        response.set_cookie(
            key="sid",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400,
        )
        
        logger.info(f"OAuth login successful for {provider}: {user['email']}")
        
        # Redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"OAuth callback failed for {provider}")
        return RedirectResponse(url="/?error=oauth_failed", status_code=302)


async def create_or_link_oauth_user(provider: str, user_info: Dict[str, Any], token: Dict[str, Any]) -> Dict[str, Any]:
    """Create or link OAuth user account."""
    
    email = user_info.get('email')
    
    # If no email provided, create a unique identifier
    if not email:
        email = f"{provider}_{user_info['provider_user_id']}@oauth.local"
    
    email = email.lower()
    
    # Check if user exists
    if email in DEMO_USERS:
        user = DEMO_USERS[email]
        logger.info(f"Linked existing user to {provider}: {email}")
    else:
        # Create new user
        user_id = len(DEMO_USERS) + 1
        user = {
            "id": user_id,
            "email": email,
            "name": user_info.get('name', f"{provider.title()} User"),
            "password_hash": None,  # OAuth users don't have passwords
            "role": "admin" if user_id == 1 else "viewer",
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
            "oauth_provider": provider,
            "oauth_data": user_info
        }
        
        DEMO_USERS[email] = user
        logger.info(f"Created new {provider} OAuth user: {email}")
    
    return user


def is_demo_mode() -> bool:
    """Check if we're in demo mode (no real OAuth credentials)."""
    google_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    return google_id.startswith('demo-') or not google_id


async def simulate_oauth_flow(provider: str, request: Request):
    """Simulate OAuth flow for demo mode."""
    
    # Generate demo OAuth callback with simulated data
    base_url = str(request.base_url).rstrip('/')
    
    # Create demo state parameter
    import secrets
    state = secrets.token_urlsafe(16)
    
    # Simulate OAuth callback URL
    callback_params = {
        'code': f'demo_{provider}_code_{state}',
        'state': state,
        'demo': 'true'
    }
    
    callback_url = f"{base_url}/auth/{provider}/callback?{urlencode(callback_params)}"
    
    return RedirectResponse(url=callback_url, status_code=302)


async def handle_demo_oauth_callback(provider: str, request: Request, response: Response):
    """Handle demo OAuth callback."""
    
    # Check if it's a demo callback
    if not request.query_params.get('demo'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth callback"
        )
    
    # Generate demo user data
    import secrets
    user_id_suffix = secrets.token_hex(4)
    
    demo_users = {
        'google': {
            'provider_user_id': f'google_user_{user_id_suffix}',
            'email': f'user.{user_id_suffix}@gmail.com',
            'name': f'Google User {user_id_suffix}',
            'avatar_url': 'https://lh3.googleusercontent.com/a/default-user',
            'verified': True
        },
        'reddit': {
            'provider_user_id': f'reddit_user_{user_id_suffix}',
            'email': f'reddituser{user_id_suffix}@reddit.local',  # Reddit doesn't provide email
            'name': f'RedditUser{user_id_suffix}',
            'avatar_url': 'https://www.redditstatic.com/avatars/defaults/v2/avatar_default_1.png',
            'verified': False
        },
        'twitter': {
            'provider_user_id': f'twitter_user_{user_id_suffix}',
            'email': f'twitteruser{user_id_suffix}@x.com',
            'name': f'TwitterUser{user_id_suffix}',
            'avatar_url': 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png',
            'verified': False
        }
    }
    
    user_info = demo_users.get(provider, {})
    
    # Create or link user
    user = await create_or_link_oauth_user(provider, user_info, {})
    
    # Create session
    session_token = generate_session_token()
    DEMO_SESSIONS[session_token] = {
        "user_id": user["id"],
        "email": user["email"],
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Set session cookie
    response.set_cookie(
        key="sid",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
    )
    
    logger.info(f"Demo {provider} OAuth login successful: {user['email']}")
    
    # Redirect to dashboard
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/oauth/status")
async def oauth_status():
    """Get OAuth configuration status."""
    return {
        "demo_mode": is_demo_mode(),
        "providers": {
            "google": {
                "configured": bool(os.getenv('GOOGLE_OAUTH_CLIENT_ID')),
                "demo": os.getenv('GOOGLE_OAUTH_CLIENT_ID', '').startswith('demo-')
            },
            "reddit": {
                "configured": bool(os.getenv('REDDIT_CLIENT_ID')),
                "demo": os.getenv('REDDIT_CLIENT_ID', '').startswith('demo-')
            },
            "twitter": {
                "configured": bool(os.getenv('TWITTER_CLIENT_ID')),
                "demo": os.getenv('TWITTER_CLIENT_ID', '').startswith('demo-')
            }
        }
    }
