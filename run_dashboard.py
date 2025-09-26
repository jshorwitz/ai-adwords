"""Launch the Synter Analytics Dashboard."""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Create a simple dashboard app that doesn't use relative imports
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio

# Setup
dashboard_app = FastAPI(title="Synter Analytics Dashboard", version="1.0.0")
templates = Jinja2Templates(directory="src/dashboard/templates")

@dashboard_app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    
    # Get data directly
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if bq_service.is_available():
            kpi_data = await bq_service.get_kpi_summary(30)
            platform_data = await bq_service.get_platform_performance(30)
            
            data = {
                "kpis": kpi_data or {
                    "total_spend": 0, "total_clicks": 0, "total_conversions": 0,
                    "total_impressions": 0, "avg_ctr": 0, "avg_cpc": 0
                },
                "platforms": platform_data or [],
                "connected": True,
                "last_updated": "Just now"
            }
        else:
            # Demo data
            data = {
                "kpis": {
                    "total_spend": 391825.74, "total_clicks": 89193, 
                    "total_conversions": 7131, "total_impressions": 450000,
                    "avg_ctr": 9.7, "avg_cpc": 4.39
                },
                "platforms": [
                    {"name": "Google Ads", "spend": 368296.90, "clicks": 74631, "conversions": 6341, "cpa": 58.08, "status": "Active"},
                    {"name": "Microsoft Ads", "spend": 300738.77, "clicks": 137736, "conversions": 7557, "cpa": 39.81, "status": "Active"},
                    {"name": "LinkedIn Ads", "spend": 46684.95, "clicks": 7081, "conversions": 449, "cpa": 103.97, "status": "Active"}
                ],
                "connected": False,
                "last_updated": "Demo data"
            }
            
    except Exception as e:
        print(f"Error loading data: {e}")
        # Fallback demo data
        data = {
            "kpis": {"total_spend": 715720.62, "total_clicks": 219448, "total_conversions": 14347, "total_impressions": 1200000, "avg_ctr": 18.3, "avg_cpc": 3.26},
            "platforms": [
                {"name": "Google Ads", "spend": 368296.90, "clicks": 74631, "conversions": 6341, "cpa": 58.08, "status": "Active"},
                {"name": "Microsoft Ads", "spend": 300738.77, "clicks": 137736, "conversions": 7557, "cpa": 39.81, "status": "Active"},
                {"name": "LinkedIn Ads", "spend": 46684.95, "clicks": 7081, "conversions": 449, "cpa": 103.97, "status": "Active"}
            ],
            "connected": False,
            "last_updated": "Demo data"
        }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "data": data,
        "title": "Synter Analytics Dashboard"
    })

@dashboard_app.get("/api/data")
async def get_dashboard_api_data():
    """API endpoint for dashboard data."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if bq_service.is_available():
            kpi_data = await bq_service.get_kpi_summary(90)
            platform_data = await bq_service.get_platform_performance(90)
            time_series = await bq_service.get_time_series(90)
            
            return {
                "kpis": kpi_data or {},
                "platforms": platform_data or [],
                "time_series": time_series or [],
                "connected": True
            }
        else:
            return {"status": "BigQuery not available", "connected": False}
    except Exception as e:
        return {"status": f"Error: {e}", "connected": False}

@dashboard_app.get("/api/daily-breakdown")
async def get_daily_breakdown():
    """API endpoint for daily spend breakdown."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            return {"error": "BigQuery not available"}
        
        # Get daily breakdown for all platforms
        daily_query = f"""
        WITH all_platform_daily AS (
            -- Google Ads daily data
            SELECT 
                'Google Ads' as platform,
                date,
                SUM(COALESCE(
                    CAST(cost AS FLOAT64),
                    CAST(cost_micros AS FLOAT64) / 1000000,
                    0
                )) as spend,
                SUM(CAST(clicks AS INT64)) as clicks,
                SUM(CAST(conversions AS FLOAT64)) as conversions
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY date
            
            UNION ALL
            
            -- Microsoft & LinkedIn daily data  
            SELECT 
                CASE 
                    WHEN platform = 'microsoft' THEN 'Microsoft Ads'
                    WHEN platform = 'linkedin' THEN 'LinkedIn Ads'
                END as platform,
                date,
                SUM(CAST(spend AS FLOAT64)) as spend,
                SUM(CAST(clicks AS INT64)) as clicks,
                SUM(CAST(conversions AS FLOAT64)) as conversions
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
            WHERE platform IN ('microsoft', 'linkedin')
              AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY platform, date
        )
        SELECT 
            date,
            platform,
            spend,
            clicks,
            conversions,
            ROUND(clicks / NULLIF(spend, 0), 2) as clicks_per_dollar,
            ROUND(spend / NULLIF(conversions, 0), 2) as cpa
        FROM all_platform_daily
        ORDER BY date DESC, spend DESC
        LIMIT 100
        """
        
        daily_df = bq_service.bq_client.query(daily_query)
        
        if daily_df.empty:
            return {"error": "No daily data found"}
        
        # Format data for frontend
        daily_data = []
        for _, row in daily_df.iterrows():
            daily_data.append({
                "date": str(row['date']),
                "platform": row['platform'],
                "spend": float(row['spend']),
                "clicks": int(row['clicks']),
                "conversions": int(row['conversions']),
                "cpa": float(row['cpa']) if row['cpa'] else 0
            })
        
        return {"daily_breakdown": daily_data, "total_records": len(daily_data)}
        
    except Exception as e:
        return {"error": f"Failed to get daily breakdown: {e}"}

@dashboard_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Synter Analytics Dashboard"}

if __name__ == "__main__":
    print("🚀 Starting Synter Analytics Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    print("🔗 API endpoints at: http://localhost:8080/docs")
    print("=" * 60)
    
    # Run the dashboard
    uvicorn.run(
        dashboard_app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
