"""Dashboard API endpoints for performance data and KPIs."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..models.auth import User
from .middleware import get_current_user

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
                "colors": ["#4285f4", "#ff4500", "#000000"]
            }
        elif chart_type == "conversions":
            return {
                "labels": [p.name for p in platforms],
                "data": [p.conversions for p in platforms],
                "colors": ["#4285f4", "#ff4500", "#000000"]
            }
        elif chart_type == "ctr":
            return {
                "labels": [p.name for p in platforms],
                "data": [p.ctr for p in platforms],
                "colors": ["#4285f4", "#ff4500", "#000000"]
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
    
    try:
        # TODO: Implement actual database query for historical data
        # This would query ad_metrics table grouped by date and platform
        
        # Generate mock time series data
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
                "x": {
                    "spend": 150 + random.uniform(-30, 80) + (base_trend * 30),
                    "conversions": 6 + random.uniform(-1, 3) + (base_trend * 1.5),
                    "ctr": 3.4 + random.uniform(-0.6, 0.6),
                    "roas": 2.9 + random.uniform(-0.4, 0.5)
                }
            })
        
        return {
            "dates": [item["date"] for item in time_series],
            "google": [item["google"] for item in time_series],
            "reddit": [item["reddit"] for item in time_series],
            "x": [item["x"] for item in time_series]
        }
        
    except Exception as e:
        logger.exception("Failed to get time series data")
        return {"error": str(e)}


# Internal helper functions
async def get_kpi_data(days: int) -> KPIData:
    """Get KPI data from database or return mock data."""
    
    try:
        # TODO: Implement actual database queries
        # This would query ad_metrics table and aggregate data
        
        # For now, return mock data with some randomization
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
        
    except Exception as e:
        logger.exception("Failed to get KPI data")
        # Fallback to static mock data
        return KPIData(
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
        )


async def get_platform_performance(days: int) -> List[PlatformPerformance]:
    """Get platform performance data from database or return mock data."""
    
    try:
        # TODO: Implement actual database queries
        # This would query ad_metrics table grouped by platform
        
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
                "platform": "x",
                "name": "X (Twitter) Ads", 
                "base_spend": 7850.00,
                "base_impressions": 433100,
                "base_clicks": 14930,
                "base_conversions": 569,
                "status": "mock" if os.getenv("MOCK_TWITTER", "true").lower() == "true" else "active"
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
        
    except Exception as e:
        logger.exception("Failed to get platform performance")
        # Fallback to static mock data
        return [
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
                status="mock"
            ),
            PlatformPerformance(
                platform="x",
                name="X (Twitter) Ads",
                spend=7850.00,
                impressions=433100,
                clicks=14930,
                conversions=569,
                ctr=3.45,
                roas=2.9,
                status="mock"
            )
        ]


def get_mock_dashboard_summary() -> DashboardSummary:
    """Get mock dashboard data when real data fails."""
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
                status="mock"
            ),
            PlatformPerformance(
                platform="x",
                name="X (Twitter) Ads",
                spend=7850.00,
                impressions=433100,
                clicks=14930,
                conversions=569,
                ctr=3.45,
                roas=2.9,
                status="mock"
            )
        ],
        agents_healthy=7,
        last_updated=datetime.utcnow().isoformat(),
    )
