"""Debug routes for testing BigQuery connection in production."""

import logging
import os
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/bigquery-test")
async def test_bigquery_connection():
    """Test BigQuery connection and configuration."""
    try:
        # Check environment variables
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        dataset_id = os.getenv("BIGQUERY_DATASET_ID")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        env_status = {
            "GOOGLE_CLOUD_PROJECT": project_id,
            "BIGQUERY_DATASET_ID": dataset_id,
            "GOOGLE_APPLICATION_CREDENTIALS": credentials_path,
            "credentials_file_exists": os.path.exists(credentials_path) if credentials_path else False
        }
        
        # Test BigQuery service
        from ..services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        if bq_service.is_available():
            # Test a simple query
            kpi_data = await bq_service.get_kpi_summary(90)
            platform_data = await bq_service.get_platform_performance(90)
            
            return {
                "status": "success",
                "environment": env_status,
                "bigquery_available": True,
                "project": bq_service.bq_client.project_id,
                "dataset": bq_service.bq_client.dataset_id,
                "kpi_summary": {
                    "total_spend": kpi_data["total_spend"],
                    "total_conversions": kpi_data["total_conversions"],
                    "total_clicks": kpi_data["total_clicks"]
                },
                "platforms_count": len(platform_data),
                "platforms": [p["name"] for p in platform_data]
            }
        else:
            return {
                "status": "bigquery_unavailable",
                "environment": env_status,
                "bigquery_available": False,
                "error": "BigQuery service not available"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "environment": {
                "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "BIGQUERY_DATASET_ID": os.getenv("BIGQUERY_DATASET_ID"),
                "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            },
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/platform-data-real")
async def get_real_platform_data():
    """Force get real platform data from BigQuery."""
    try:
        from ..services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            return {"error": "BigQuery service not available"}
        
        # Force real data query
        platform_data = await bq_service.get_platform_performance(90)
        kpi_data = await bq_service.get_kpi_summary(90)
        
        return {
            "status": "success",
            "source": "real_bigquery_data",
            "kpis": kpi_data,
            "platforms": platform_data,
            "total_platforms": len(platform_data),
            "total_spend": sum(p["spend"] for p in platform_data)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "source": "bigquery_query_failed"
        }
