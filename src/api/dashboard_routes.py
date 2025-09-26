"""Dashboard API endpoints for performance data and KPIs."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..models.auth import User
from .middleware import get_current_user, get_current_user_optional
from ..services.bigquery_service import get_bigquery_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Response models
class KPIData(BaseModel):
    total_spend: float
    total_impressions: int
    total_clicks: int
    total_conversions: int
    avg_ctr: float
    avg_roas: float
    changes: Dict[str, float]


class PlatformPerformance(BaseModel):
    platform: str
    name: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    roas: float
    status: str


class DashboardSummary(BaseModel):
    kpis: KPIData
    platforms: List[PlatformPerformance]
    agents_healthy: int
    last_updated: str


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    days: int = Query(default=30, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
):
    """Get complete dashboard summary with KPIs and platform data."""
    
    try:
        # Get KPI data
        kpi_data = await get_kpi_data(days)
        
        # Get platform performance
        platform_data = await get_platform_performance(days)
        
        # Get agent health count
        try:
            from ..agents.runner import agent_registry
            agents_healthy = len(agent_registry.list_agents())
        except Exception:
            agents_healthy = 0
        
        return DashboardSummary(
            kpis=kpi_data,
            platforms=platform_data,
            agents_healthy=agents_healthy,
            last_updated=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        logger.exception("Failed to get dashboard summary")
        # Return mock data if real data fails
        return get_mock_dashboard_summary()


@router.get("/kpis", response_model=KPIData)
async def get_dashboard_kpis(
    days: int = Query(default=30, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
):
    """Get KPI summary data."""
    return await get_kpi_data(days)


@router.get("/platforms", response_model=List[PlatformPerformance])
async def get_platform_performance_data(
    days: int = Query(default=30, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
):
    """Get platform performance breakdown."""
    return await get_platform_performance(days)


@router.get("/chart-data")
async def get_chart_data(
    chart_type: str = Query(description="Type of chart: spend, conversions, ctr, timeseries"),
    days: int = Query(default=7, description="Number of days"),
    current_user: User = Depends(get_current_user),
):
    """Get data for dashboard charts."""
    
    try:
        if chart_type == "timeseries":
            return await get_time_series_data(days)
        
        platforms = await get_platform_performance(days)
        
        if chart_type == "spend":
            return {
                "labels": [p.name for p in platforms],
                "data": [p.spend for p in platforms],
                "colors": ["#000000", "#ff6b35", "#0078D4", "#0077B5"]
            }
        elif chart_type == "conversions":
            return {
                "labels": [p.name for p in platforms],
                "data": [p.conversions for p in platforms],
                "colors": ["#000000", "#ff6b35", "#0078D4", "#0077B5"]
            }
        elif chart_type == "ctr":
            return {
                "labels": [p.name for p in platforms],
                "data": [p.ctr for p in platforms],
                "colors": ["#000000", "#ff6b35", "#0078D4", "#0077B5"]
            }
        else:
            return {"error": "Invalid chart type"}
            
    except Exception as e:
        logger.exception(f"Failed to get chart data for {chart_type}")
        return {"error": str(e)}


@router.get("/timeseries")
async def get_time_series_data(
    days: int = Query(default=30, description="Number of days"),
    current_user: User = Depends(get_current_user),
):
    """Get time series data for performance trends."""
    
    bigquery_service = get_bigquery_service()
    
    # Try to get data from BigQuery first
    if bigquery_service.is_available():
        try:
            logger.info(f"Getting time series data from BigQuery for {days} days")
            time_series_data = await bigquery_service.get_time_series_data(days)
            
            if time_series_data and time_series_data.get('dates'):
                return time_series_data
        except Exception as e:
            logger.error(f"Failed to get time series data from BigQuery: {e}")
    
    # Fallback to mock time series data
    logger.info("Using mock time series data")
    try:
        import random
        from datetime import date, timedelta
        
        time_series = []
        end_date = date.today()
        
        for i in range(days):
            current_date = end_date - timedelta(days=days-1-i)
            
            # Generate realistic trending data with some randomness
            base_trend = i / days  # Gradual increase over time
            
            time_series.append({
                "date": current_date.isoformat(),
                "google": {
                    "spend": 800 + random.uniform(-200, 300) + (base_trend * 200),
                    "conversions": 20 + random.uniform(-5, 10) + (base_trend * 5),
                    "ctr": 4.5 + random.uniform(-1, 1),
                    "roas": 3.2 + random.uniform(-0.5, 0.8)
                },
                "reddit": {
                    "spend": 200 + random.uniform(-50, 100) + (base_trend * 50),
                    "conversions": 8 + random.uniform(-2, 4) + (base_trend * 2),
                    "ctr": 4.1 + random.uniform(-0.8, 0.8),
                    "roas": 2.8 + random.uniform(-0.3, 0.6)
                },
                "microsoft": {
                    "spend": 140 + random.uniform(-25, 70) + (base_trend * 25),
                    "conversions": 5 + random.uniform(-1, 2.5) + (base_trend * 1.2),
                    "ctr": 3.6 + random.uniform(-0.5, 0.5),
                    "roas": 3.1 + random.uniform(-0.3, 0.4)
                },
                "linkedin": {
                    "spend": 110 + random.uniform(-20, 60) + (base_trend * 20),
                    "conversions": 4 + random.uniform(-0.5, 2) + (base_trend * 1),
                    "ctr": 3.7 + random.uniform(-0.4, 0.4),
                    "roas": 4.2 + random.uniform(-0.2, 0.3)
                }
            })
        
        return {
            "dates": [item["date"] for item in time_series],
            "google": [item["google"] for item in time_series],
            "reddit": [item["reddit"] for item in time_series],
            "microsoft": [item["microsoft"] for item in time_series],
            "linkedin": [item["linkedin"] for item in time_series]
        }
        
    except Exception as e:
        logger.exception("Failed to get time series data")
        return {"error": str(e)}


# Public demo endpoints (no auth required)
@router.get("/demo/kpis", response_model=KPIData)
async def get_demo_kpis():
    """Get demo KPI data (no authentication required)."""
    return await get_kpi_data(90)


@router.get("/demo/platforms", response_model=List[PlatformPerformance])
async def get_demo_platforms():
    """Get demo platform data (no authentication required)."""
    return await get_platform_performance(90)


@router.get("/demo/summary", response_model=DashboardSummary)
async def get_demo_summary():
    """Get demo dashboard summary (no authentication required)."""
    return get_mock_dashboard_summary()


# Internal helper functions
async def get_kpi_data(days: int) -> KPIData:
    """Get KPI data from BigQuery or return mock data."""
    
    bigquery_service = get_bigquery_service()
    
    # Try to get data from BigQuery first
    if bigquery_service.is_available():
        try:
            logger.info(f"Getting KPI data from BigQuery for {days} days")
            kpi_data = await bigquery_service.get_kpi_summary(days)
            
            if kpi_data:
                return KPIData(
                    total_spend=kpi_data['total_spend'],
                    total_impressions=kpi_data['total_impressions'],
                    total_clicks=kpi_data['total_clicks'],
                    total_conversions=kpi_data['total_conversions'],
                    avg_ctr=kpi_data['avg_ctr'],
                    avg_roas=kpi_data['avg_roas'],
                    changes=kpi_data['changes']
                )
        except Exception as e:
            logger.error(f"Failed to get KPI data from BigQuery: {e}")
    
    # Fallback to mock data with some randomization
    logger.info("Using mock KPI data")
    import random
    base_multiplier = days / 30  # Scale based on date range
    
    return KPIData(
        total_spend=round(45250.75 * base_multiplier * random.uniform(0.8, 1.2), 2),
        total_impressions=int(2847391 * base_multiplier * random.uniform(0.9, 1.1)),
        total_clicks=int(127583 * base_multiplier * random.uniform(0.85, 1.15)),
        total_conversions=int(3492 * base_multiplier * random.uniform(0.7, 1.3)),
        avg_ctr=round(4.48 * random.uniform(0.9, 1.1), 2),
        avg_roas=round(3.2 * random.uniform(0.8, 1.2), 1),
        changes={
            "spend": round(random.uniform(-5, 25), 1),
            "impressions": round(random.uniform(-10, 20), 1),
            "clicks": round(random.uniform(-15, 30), 1),
            "conversions": round(random.uniform(-20, 40), 1),
            "ctr": round(random.uniform(-10, 10), 1),
            "roas": round(random.uniform(-15, 25), 1),
        }
    )


async def get_platform_performance(days: int) -> List[PlatformPerformance]:
    """Get platform performance data from BigQuery or return mock data."""
    
    bigquery_service = get_bigquery_service()
    
    # Try to get data from BigQuery first
    if bigquery_service.is_available():
        try:
            logger.info(f"Getting platform performance from BigQuery for {days} days")
            platform_data = await bigquery_service.get_platform_performance(days)
            
            if platform_data:
                return [
                    PlatformPerformance(
                        platform=p['platform'],
                        name=p['name'],
                        spend=p['spend'],
                        impressions=p['impressions'],
                        clicks=p['clicks'],
                        conversions=p['conversions'],
                        ctr=p['ctr'],
                        roas=p['roas'],
                        status=p['status']
                    )
                    for p in platform_data
                ]
        except Exception as e:
            logger.error(f"Failed to get platform performance from BigQuery: {e}")
    
    # Fallback to mock data with some randomization
    logger.info("Using mock platform performance data")
    import random
    import os
    
    base_multiplier = days / 30
    
    platforms = [
        {
            "platform": "google",
            "name": "Google Ads",
            "base_spend": 28450.25,
            "base_impressions": 1847291,
            "base_clicks": 89234,
            "base_conversions": 2134,
            "status": "active" if os.getenv("GOOGLE_ADS_CLIENT_ID") else "mock"
        },
        {
            "platform": "reddit", 
            "name": "Reddit Ads",
            "base_spend": 8950.50,
            "base_impressions": 567000,
            "base_clicks": 23419,
            "base_conversions": 789,
            "status": "mock" if os.getenv("MOCK_REDDIT", "true").lower() == "true" else "active"
        },
        {
            "platform": "microsoft",
            "name": "Microsoft Ads", 
            "base_spend": 6850.00,
            "base_impressions": 383100,
            "base_clicks": 13930,
            "base_conversions": 489,
            "status": "mock" if os.getenv("MOCK_MICROSOFT", "true").lower() == "true" else "active"
        },
        {
            "platform": "linkedin",
            "name": "LinkedIn Ads", 
            "base_spend": 5200.00,
            "base_impressions": 245600,
            "base_clicks": 8950,
            "base_conversions": 325,
            "status": "mock" if os.getenv("MOCK_LINKEDIN", "true").lower() == "true" else "active"
        }
    ]
    
    result = []
    for p in platforms:
        spend = round(p["base_spend"] * base_multiplier * random.uniform(0.8, 1.2), 2)
        impressions = int(p["base_impressions"] * base_multiplier * random.uniform(0.9, 1.1))
        clicks = int(p["base_clicks"] * base_multiplier * random.uniform(0.85, 1.15))
        conversions = int(p["base_conversions"] * base_multiplier * random.uniform(0.7, 1.3))
        
        ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0
        roas = round((conversions * 100 / spend), 1) if spend > 0 else 0
        
        result.append(PlatformPerformance(
            platform=p["platform"],
            name=p["name"],
            spend=spend,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            ctr=ctr,
            roas=roas,
            status=p["status"]
        ))
    
    return result


def get_mock_dashboard_summary() -> DashboardSummary:
    """Get mock dashboard data when real data fails."""
    import os
    return DashboardSummary(
        kpis=KPIData(
            total_spend=45250.75,
            total_impressions=2847391,
            total_clicks=127583,
            total_conversions=3492,
            avg_ctr=4.48,
            avg_roas=3.2,
            changes={
                "spend": 12.5,
                "impressions": 8.7,
                "clicks": 15.2,
                "conversions": 22.1,
                "ctr": -2.3,
                "roas": 18.9,
            }
        ),
        platforms=[
            PlatformPerformance(
                platform="google",
                name="Google Ads",
                spend=28450.25,
                impressions=1847291,
                clicks=89234,
                conversions=2134,
                ctr=4.83,
                roas=3.5,
                status="active"
            ),
            PlatformPerformance(
                platform="reddit",
                name="Reddit Ads",
                spend=8950.50,
                impressions=567000,
                clicks=23419,
                conversions=789,
                ctr=4.13,
                roas=2.8,
                status="mock" if os.getenv("MOCK_REDDIT", "true").lower() == "true" else "active"
            ),
            PlatformPerformance(
                platform="microsoft",
                name="Microsoft Ads",
                spend=6850.00,
                impressions=383100,
                clicks=13930,
                conversions=489,
                ctr=3.64,
                roas=3.1,
                status="mock" if os.getenv("MOCK_MICROSOFT", "true").lower() == "true" else "active"
            ),
            PlatformPerformance(
                platform="linkedin",
                name="LinkedIn Ads",
                spend=5200.00,
                impressions=245600,
                clicks=8950,
                conversions=325,
                ctr=3.65,
                roas=4.2,
                status="mock" if os.getenv("MOCK_LINKEDIN", "true").lower() == "true" else "active"
            )
        ],
        agents_healthy=7,
        last_updated=datetime.utcnow().isoformat(),
    )
