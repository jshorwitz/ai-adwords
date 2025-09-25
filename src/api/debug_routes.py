"""Debug API endpoints to check environment variables and configuration."""

import os
from fastapi import APIRouter

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/env")
async def get_environment_variables():
    """Get current environment variables (for debugging)."""
    
    # Only show non-sensitive environment variables
    env_vars = {
        "MOCK_REDDIT": os.getenv("MOCK_REDDIT", "NOT_SET"),
        "MOCK_TWITTER": os.getenv("MOCK_TWITTER", "NOT_SET"), 
        "ENABLE_REAL_MUTATES": os.getenv("ENABLE_REAL_MUTATES", "NOT_SET"),
        "REDDIT_CLIENT_ID": "SET" if os.getenv("REDDIT_CLIENT_ID") else "NOT_SET",
        "REDDIT_CLIENT_SECRET": "SET" if os.getenv("REDDIT_CLIENT_SECRET") else "NOT_SET",
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "NOT_SET"),
        "HOST": os.getenv("HOST", "NOT_SET"),
        "PORT": os.getenv("PORT", "NOT_SET"),
    }
    
    return {
        "environment_variables": env_vars,
        "reddit_status_logic": {
            "mock_reddit_value": os.getenv("MOCK_REDDIT", "true"),
            "mock_reddit_lower": os.getenv("MOCK_REDDIT", "true").lower(),
            "is_true_check": os.getenv("MOCK_REDDIT", "true").lower() == "true",
            "final_status": "mock" if os.getenv("MOCK_REDDIT", "true").lower() == "true" else "active"
        }
    }


@router.get("/platform-status")
async def get_platform_status():
    """Get platform status calculation."""
    
    reddit_status = "mock" if os.getenv("MOCK_REDDIT", "true").lower() == "true" else "active"
    twitter_status = "mock" if os.getenv("MOCK_TWITTER", "true").lower() == "true" else "active"
    google_status = "active" if os.getenv("GOOGLE_ADS_CLIENT_ID") else "mock"
    
    return {
        "platforms": {
            "reddit": {
                "status": reddit_status,
                "mock_env": os.getenv("MOCK_REDDIT", "true"),
                "has_credentials": bool(os.getenv("REDDIT_CLIENT_ID"))
            },
            "twitter": {
                "status": twitter_status,
                "mock_env": os.getenv("MOCK_TWITTER", "true"), 
                "has_credentials": bool(os.getenv("TWITTER_API_KEY"))
            },
            "google": {
                "status": google_status,
                "has_credentials": bool(os.getenv("GOOGLE_ADS_CLIENT_ID"))
            }
        }
    }
