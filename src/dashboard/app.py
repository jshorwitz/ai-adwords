"""Modern web dashboard for multi-platform advertising analytics."""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ..services.bigquery_service import get_bigquery_service

logger = logging.getLogger(__name__)

# Create FastAPI app for dashboard
dashboard_app = FastAPI(title="Synter Analytics Dashboard", version="1.0.0")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

templates = Jinja2Templates(directory=templates_dir)

# Setup static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

dashboard_app.mount("/static", StaticFiles(directory=static_dir), name="static")


class SynterDashboard:
    """Main dashboard class for multi-platform advertising analytics."""

    def __init__(self):
        """Initialize dashboard with BigQuery connection."""
        try:
            self.bq_service = get_bigquery_service()
            self.connected = self.bq_service.is_available()
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery service: {e}")
            self.bq_service = None
            self.connected = False

    async def get_dashboard_data(self, days: int = 30):
        """Get comprehensive dashboard data from BigQuery."""
        if not self.connected:
            return self._get_demo_data()

        try:
            # Get KPI summary
            kpi_data = await self.bq_service.get_kpi_summary(days)
            
            # Get platform performance
            platform_data = await self.bq_service.get_platform_performance(days)
            
            # Get time series data for charts
            time_series_data = await self.bq_service.get_time_series(days)
            
            return {
                "kpis": kpi_data or {},
                "platforms": platform_data or [],
                "time_series": time_series_data or [],
                "connected": True,
                "last_updated": "Just now"
            }
            
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return self._get_demo_data()

    def _get_demo_data(self):
        """Return demo data when BigQuery is not available."""
        return {
            "kpis": {
                "total_spend": 23528.84,
                "total_impressions": 150000,
                "total_clicks": 14562,
                "total_conversions": 790,
                "avg_ctr": 9.7,
                "avg_cpc": 1.62,
                "avg_roas": 3.2
            },
            "platforms": [
                {
                    "name": "Microsoft Ads",
                    "spend": 10082.49,
                    "clicks": 7153,
                    "conversions": 382,
                    "cpa": 26.39,
                    "status": "Active"
                },
                {
                    "name": "LinkedIn Ads", 
                    "spend": 7960.00,
                    "clicks": 3480,
                    "conversions": 185,
                    "cpa": 43.03,
                    "status": "Active"
                },
                {
                    "name": "Reddit Ads",
                    "spend": 5486.35,
                    "clicks": 3929,
                    "conversions": 223,
                    "cpa": 24.60,
                    "status": "Active"
                }
            ],
            "time_series": [],
            "connected": False,
            "last_updated": "Demo data"
        }


# Initialize dashboard
dashboard = SynterDashboard()


@dashboard_app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    data = await dashboard.get_dashboard_data()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "data": data,
        "title": "Synter Analytics Dashboard"
    })


@dashboard_app.get("/api/data")
async def get_dashboard_api_data(days: int = 30):
    """API endpoint for dashboard data."""
    return await dashboard.get_dashboard_data(days)


@dashboard_app.get("/platforms")
async def platforms_page(request: Request):
    """Platform-specific dashboard page."""
    data = await dashboard.get_dashboard_data()
    
    return templates.TemplateResponse("platforms.html", {
        "request": request,
        "data": data,
        "title": "Platform Performance"
    })


@dashboard_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "bigquery_connected": dashboard.connected,
        "service": "Synter Analytics Dashboard"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(dashboard_app, host="0.0.0.0", port=8080)
