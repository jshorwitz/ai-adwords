"""Admin routes for triggering data sync and checking platform status."""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from ..models.auth import User
from .middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class SyncResult(BaseModel):
    success: bool
    message: str
    platforms: Dict[str, Any]
    total_records: int
    sync_duration: str | None = None
    errors: list[str] = []


class PlatformConfigStatus(BaseModel):
    reddit: Dict[str, Any]
    microsoft: Dict[str, Any]
    linkedin: Dict[str, Any]
    bigquery: Dict[str, Any]
    ready_for_sync: bool


@router.get("/platform-config", response_model=PlatformConfigStatus)
async def get_platform_config_status(current_user: User = Depends(get_current_user)):
    """Get detailed platform configuration status."""
    
    import os
    
    # Reddit status
    reddit_status = {
        "credentials_configured": bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET")),
        "mock_mode": os.getenv("MOCK_REDDIT", "true").lower() == "true",
        "ready": bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET") and os.getenv("MOCK_REDDIT", "true").lower() == "false")
    }
    
    # Microsoft status  
    ms_creds = ["MICROSOFT_ADS_DEVELOPER_TOKEN", "MICROSOFT_ADS_CLIENT_ID", "MICROSOFT_ADS_CLIENT_SECRET", "MICROSOFT_ADS_CUSTOMER_ID"]
    microsoft_status = {
        "credentials_configured": all(os.getenv(cred) for cred in ms_creds),
        "mock_mode": os.getenv("MOCK_MICROSOFT", "true").lower() == "true",
        "ready": all(os.getenv(cred) for cred in ms_creds) and os.getenv("MOCK_MICROSOFT", "true").lower() == "false"
    }
    
    # LinkedIn status
    linkedin_status = {
        "credentials_configured": bool(os.getenv("LINKEDIN_CLIENT_ID") and os.getenv("LINKEDIN_CLIENT_SECRET")),
        "mock_mode": os.getenv("MOCK_LINKEDIN", "true").lower() == "true", 
        "ready": bool(os.getenv("LINKEDIN_CLIENT_ID") and os.getenv("LINKEDIN_CLIENT_SECRET") and os.getenv("MOCK_LINKEDIN", "true").lower() == "false")
    }
    
    # BigQuery status
    bigquery_status = {
        "project_configured": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "dataset": os.getenv("BIGQUERY_DATASET_ID", "synter_analytics"),
        "credentials": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
        "ready": bool(os.getenv("GOOGLE_CLOUD_PROJECT"))
    }
    
    ready_for_sync = (
        bigquery_status["ready"] and 
        (reddit_status["ready"] or microsoft_status["ready"] or linkedin_status["ready"])
    )
    
    return PlatformConfigStatus(
        reddit=reddit_status,
        microsoft=microsoft_status, 
        linkedin=linkedin_status,
        bigquery=bigquery_status,
        ready_for_sync=ready_for_sync
    )


@router.post("/sync-data", response_model=SyncResult)
async def trigger_data_sync(
    platform: str = Query(default="all", description="Platform to sync (all, reddit, microsoft, linkedin)"),
    days_back: int = Query(default=7, description="Number of days to sync"),
    dry_run: bool = Query(default=False, description="Perform dry run"),
    current_user: User = Depends(get_current_user),
):
    """Trigger manual data synchronization for specified platforms."""
    
    try:
        logger.info(f"Admin triggered data sync: platform={platform}, days_back={days_back}, dry_run={dry_run}")
        
        from src.etl.multi_platform_pipeline import MultiPlatformETLPipeline
        
        pipeline = MultiPlatformETLPipeline()
        
        # Check if any platforms are ready
        enabled_platforms = [p for p, enabled in pipeline.platforms_enabled.items() if enabled]
        
        if not enabled_platforms:
            raise HTTPException(
                status_code=400,
                detail="No platforms configured for live data. Set MOCK_*=false and add API credentials."
            )
        
        start_time = datetime.utcnow()
        
        if platform == "all":
            # Sync all platforms
            results = await pipeline.sync_all_platforms(days_back)
        else:
            # Sync specific platform
            from src.agents.multi_platform_agents import run_reddit_sync, run_microsoft_sync, run_linkedin_sync
            
            if platform == "reddit":
                results = {"platforms": {"reddit": await run_reddit_sync(days_back, dry_run)}}
            elif platform == "microsoft":
                results = {"platforms": {"microsoft": await run_microsoft_sync(days_back, dry_run)}}
            elif platform == "linkedin":
                results = {"platforms": {"linkedin": await run_linkedin_sync(days_back, dry_run)}}
            else:
                raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
            
            # Add metadata
            results["total_records"] = sum(p.get("records_written", 0) for p in results["platforms"].values())
            results["success"] = all(p.get("status") == "success" for p in results["platforms"].values())
            results["errors"] = [f"{p}: {pr.get('error', '')}" for p, pr in results["platforms"].items() if pr.get("status") == "error"]
        
        end_time = datetime.utcnow()
        duration = str(end_time - start_time)
        
        return SyncResult(
            success=results.get("success", False),
            message=f"Sync completed for {platform}",
            platforms=results.get("platforms", {}),
            total_records=results.get("total_records", 0),
            sync_duration=duration,
            errors=results.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"Data sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Data sync failed: {str(e)}")


@router.get("/bigquery-status")
async def check_bigquery_status(current_user: User = Depends(get_current_user)):
    """Check BigQuery data status and table counts."""
    
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            return {"available": False, "error": "BigQuery service not configured"}
        
        # Check table data
        tables_status = {}
        
        # Check campaigns_performance (Google Ads)
        try:
            google_query = f"""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT customer_id) as customers,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                SUM(COALESCE(CAST(cost AS FLOAT64), CAST(cost_micros AS FLOAT64) / 1000000, 0)) as total_spend
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            
            google_df = bq_service.bq_client.query(google_query)
            if not google_df.empty:
                row = google_df.iloc[0]
                tables_status["campaigns_performance"] = {
                    "exists": True,
                    "rows": int(row['total_rows']),
                    "customers": int(row['customers']),
                    "earliest_date": str(row['earliest_date']),
                    "latest_date": str(row['latest_date']),
                    "total_spend": float(row['total_spend'])
                }
            else:
                tables_status["campaigns_performance"] = {"exists": True, "rows": 0}
                
        except Exception as e:
            tables_status["campaigns_performance"] = {"exists": False, "error": str(e)}
        
        # Check ad_metrics table (Multi-platform)
        try:
            metrics_query = f"""
            SELECT 
                platform,
                COUNT(*) as rows,
                SUM(spend) as total_spend,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY platform
            """
            
            metrics_df = bq_service.bq_client.query(metrics_query)
            if not metrics_df.empty:
                platforms_data = {}
                for _, row in metrics_df.iterrows():
                    platform = row['platform']
                    platforms_data[platform] = {
                        "rows": int(row['rows']),
                        "total_spend": float(row['total_spend']),
                        "earliest_date": str(row['earliest_date']),
                        "latest_date": str(row['latest_date'])
                    }
                tables_status["ad_metrics"] = {"exists": True, "platforms": platforms_data}
            else:
                tables_status["ad_metrics"] = {"exists": True, "rows": 0}
                
        except Exception as e:
            tables_status["ad_metrics"] = {"exists": False, "error": str(e)}
        
        return {
            "available": True,
            "project": bq_service.bq_client.project_id,
            "dataset": bq_service.bq_client.dataset_id,
            "tables": tables_status
        }
        
    except Exception as e:
        return {"available": False, "error": str(e)}


@router.post("/test-apis")
async def test_platform_apis(current_user: User = Depends(get_current_user)):
    """Test all platform API connections."""
    
    results = {}
    
    # Test Reddit
    try:
        from src.integrations.reddit_ads import RedditAdsClient
        async with RedditAdsClient() as reddit_client:
            accounts = await reddit_client.get_accounts()
            results["reddit"] = {
                "success": True,
                "accounts_found": len(accounts),
                "status": "Connected successfully"
            }
    except Exception as e:
        results["reddit"] = {
            "success": False,
            "error": str(e),
            "status": "Connection failed"
        }
    
    # Test Microsoft
    try:
        from src.integrations.microsoft_ads import MicrosoftAdsClient
        async with MicrosoftAdsClient() as ms_client:
            connection_status = await ms_client.test_connection()
            results["microsoft"] = {
                "success": connection_status.get("connected", False),
                "status": connection_status.get("status", "Unknown"),
                "mode": connection_status.get("mode", "unknown")
            }
    except Exception as e:
        results["microsoft"] = {
            "success": False,
            "error": str(e),
            "status": "Connection failed"
        }
    
    # Test LinkedIn
    try:
        from src.integrations.linkedin_ads import LinkedInAdsClient
        async with LinkedInAdsClient() as linkedin_client:
            connection_status = await linkedin_client.test_connection()
            results["linkedin"] = {
                "success": connection_status.get("connected", False),
                "status": connection_status.get("status", "Unknown"),
                "mode": connection_status.get("mode", "unknown"),
                "user": connection_status.get("user")
            }
    except Exception as e:
        results["linkedin"] = {
            "success": False,
            "error": str(e),
            "status": "Connection failed"
        }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "platforms": results,
        "summary": {
            "total_platforms": len(results),
            "connected_platforms": sum(1 for r in results.values() if r.get("success")),
            "all_connected": all(r.get("success") for r in results.values())
        }
    }
