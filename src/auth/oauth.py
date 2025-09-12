"""OAuth configuration for Google, Reddit, and X/Twitter SSO."""

import os
from typing import Dict, Any

from authlib.integrations.starlette_client import OAuth

# OAuth configuration
oauth_config = {
    'google': {
        'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID', 'demo-google-client-id'),
        'client_secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', 'demo-google-secret'),
        'server_metadata_url': 'https://accounts.google.com/.well-known/openid_configuration',
        'client_kwargs': {
            'scope': 'openid email profile'
        }
    },
    'reddit': {
        'client_id': os.getenv('REDDIT_CLIENT_ID', 'demo-reddit-client-id'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'demo-reddit-secret'),
        'authorize_url': 'https://www.reddit.com/api/v1/authorize',
        'access_token_url': 'https://www.reddit.com/api/v1/access_token',
        'client_kwargs': {
            'scope': 'identity',
            'duration': 'permanent'
        }
    },
    'twitter': {
        'client_id': os.getenv('TWITTER_CLIENT_ID', 'demo-twitter-client-id'),
        'client_secret': os.getenv('TWITTER_CLIENT_SECRET', 'demo-twitter-secret'),
        'request_token_url': 'https://api.twitter.com/oauth/request_token',
        'authorize_url': 'https://api.twitter.com/oauth/authorize',
        'access_token_url': 'https://api.twitter.com/oauth/access_token',
        'client_kwargs': {
            'signature_type': 'AUTH_HEADER'
        }
    }
}

# Initialize OAuth
oauth = OAuth()

def configure_oauth(app):
    """Configure OAuth providers for the FastAPI app."""
    
    # Google OAuth
    oauth.register(
        name='google',
        **oauth_config['google']
    )
    
    # Reddit OAuth
    oauth.register(
        name='reddit',
        **oauth_config['reddit']
    )
    
    # Twitter OAuth (X)
    oauth.register(
        name='twitter',
        **oauth_config['twitter']
    )
    
    return oauth


def get_oauth_redirect_uri(provider: str, base_url: str) -> str:
    """Get OAuth redirect URI for a provider."""
    return f"{base_url}/auth/{provider}/callback"


def extract_user_info(provider: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract standardized user info from OAuth provider data."""
    
    if provider == 'google':
        return {
            'provider_user_id': user_data.get('sub'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'avatar_url': user_data.get('picture'),
            'verified': user_data.get('email_verified', False)
        }
    
    elif provider == 'reddit':
        return {
            'provider_user_id': user_data.get('id'),
            'email': None,  # Reddit doesn't provide email
            'name': user_data.get('name'),
            'avatar_url': user_data.get('icon_img'),
            'verified': user_data.get('is_employee', False)
        }
    
    elif provider == 'twitter':
        return {
            'provider_user_id': user_data.get('id_str'),
            'email': user_data.get('email'),  # May not be available
            'name': user_data.get('name'),
            'avatar_url': user_data.get('profile_image_url_https'),
            'verified': user_data.get('verified', False)
        }
    
    else:
        return {
            'provider_user_id': str(user_data.get('id', 'unknown')),
            'email': user_data.get('email'),
            'name': user_data.get('name', 'Unknown User'),
            'avatar_url': None,
            'verified': False
        }
