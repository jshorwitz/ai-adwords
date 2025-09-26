"""BigQuery service for dashboard data queries."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from google.cloud import bigquery

from ..ads.bigquery_client import create_bigquery_client_from_env

logger = logging.getLogger(__name__)


class DashboardBigQueryService:
    """Service for querying BigQuery data for dashboard visualizations."""
    
    def __init__(self):
        """Initialize BigQuery service."""
        try:
            self.bq_client = create_bigquery_client_from_env()
            self.project_id = self.bq_client.project_id
            self.dataset_id = self.bq_client.dataset_id
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            self.bq_client = None
    
    def is_available(self) -> bool:
        """Check if BigQuery client is available."""
        return self.bq_client is not None
    
    async def get_kpi_summary(self, days: int = 30) -> Dict:
        """Get KPI summary data from BigQuery."""
        if not self.is_available():
            raise ValueError("BigQuery client not available")
        
        try:
            # Multi-platform KPI query
            sql = f"""
            WITH platform_data AS (
                -- Google Ads data (handle cost_micros conversion)
                SELECT 
                    'google' as platform,
                    date,
                    CAST(impressions AS INT64) as impressions,
                    CAST(clicks AS INT64) as clicks,
                    -- Handle both cost and cost_micros fields
                    COALESCE(
                        CAST(cost AS FLOAT64),
                        CAST(cost_micros AS FLOAT64) / 1000000,
                        0
                    ) as spend,
                    CAST(conversions AS FLOAT64) as conversions,
                    CAST(ctr AS FLOAT64) as ctr,
                    CASE 
                        WHEN COALESCE(CAST(cost AS FLOAT64), CAST(cost_micros AS FLOAT64) / 1000000, 0) > 0 
                        THEN CAST(conversions AS FLOAT64) * 100 / COALESCE(CAST(cost AS FLOAT64), CAST(cost_micros AS FLOAT64) / 1000000, 0)
                        ELSE 0 
                    END as roas
                    FROM `{self.project_id}.{self.dataset_id}.campaigns_performance`
                    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                    
                    UNION ALL
                
                -- Multi-platform ad metrics (Microsoft, LinkedIn)
                SELECT 
                    platform,
                    date,
                    CAST(impressions AS INT64) as impressions,
                    CAST(clicks AS INT64) as clicks,
                    CAST(spend AS FLOAT64) as spend,
                    CAST(conversions AS FLOAT64) as conversions,
                    CAST(ctr AS FLOAT64) as ctr,
                    CASE 
                        WHEN CAST(spend AS FLOAT64) > 0 THEN CAST(conversions AS FLOAT64) * 100 / CAST(spend AS FLOAT64)
                        ELSE 0 
                    END as roas
                FROM `{self.project_id}.{self.dataset_id}.ad_metrics`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                  AND platform IN ('microsoft', 'linkedin')
            ),
            current_period AS (
                SELECT 
                    SUM(spend) as total_spend,
                    SUM(impressions) as total_impressions,
                    SUM(clicks) as total_clicks,
                    SUM(conversions) as total_conversions,
                    CASE 
                        WHEN SUM(impressions) > 0 THEN SUM(clicks) / SUM(impressions) * 100
                        ELSE 0 
                    END as avg_ctr,
                    CASE 
                        WHEN SUM(spend) > 0 THEN SUM(conversions) * 100 / SUM(spend)
                        ELSE 0 
                    END as avg_roas
                FROM platform_data
            ),
            previous_period AS (
                SELECT 
                    SUM(spend) as prev_spend,
                    SUM(impressions) as prev_impressions,
                    SUM(clicks) as prev_clicks,
                    SUM(conversions) as prev_conversions,
                    CASE 
                        WHEN SUM(impressions) > 0 THEN SUM(clicks) / SUM(impressions) * 100
                        ELSE 0 
                    END as prev_ctr,
                    CASE 
                        WHEN SUM(spend) > 0 THEN SUM(conversions) * 100 / SUM(spend)
                        ELSE 0 
                    END as prev_roas
                FROM (
                    -- Previous period Google Ads data (handle cost_micros conversion)
                    SELECT 
                        'google' as platform,
                        date,
                        CAST(impressions AS INT64) as impressions,
                        CAST(clicks AS INT64) as clicks,
                        -- Handle both cost and cost_micros fields
                        COALESCE(
                            CAST(cost AS FLOAT64),
                            CAST(cost_micros AS FLOAT64) / 1000000,
                            0
                        ) as spend,
                        CAST(conversions AS FLOAT64) as conversions
                    FROM `{self.project_id}.{self.dataset_id}.campaigns_performance`
                    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL @days*2 DAY)
                      AND date < DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
                    
                    UNION ALL
                    
                    SELECT 
                        platform,
                        date,
                        CAST(impressions AS INT64) as impressions,
                        CAST(clicks AS INT64) as clicks,
                        CAST(spend AS FLOAT64) as spend,
                        CAST(conversions AS FLOAT64) as conversions
                    FROM `{self.project_id}.{self.dataset_id}.ad_metrics`
                    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL @days*2 DAY)
                      AND date < DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
                      AND platform IN ('microsoft', 'linkedin')
                )
            )
            SELECT 
                c.total_spend,
                c.total_impressions,
                c.total_clicks,
                c.total_conversions,
                ROUND(c.avg_ctr, 2) as avg_ctr,
                ROUND(c.avg_roas, 1) as avg_roas,
                -- Calculate percentage changes
                CASE 
                    WHEN p.prev_spend > 0 THEN ROUND((c.total_spend - p.prev_spend) / p.prev_spend * 100, 1)
                    ELSE 0 
                END as spend_change,
                CASE 
                    WHEN p.prev_impressions > 0 THEN ROUND((c.total_impressions - p.prev_impressions) / p.prev_impressions * 100, 1)
                    ELSE 0 
                END as impressions_change,
                CASE 
                    WHEN p.prev_clicks > 0 THEN ROUND((c.total_clicks - p.prev_clicks) / p.prev_clicks * 100, 1)
                    ELSE 0 
                END as clicks_change,
                CASE 
                    WHEN p.prev_conversions > 0 THEN ROUND((c.total_conversions - p.prev_conversions) / p.prev_conversions * 100, 1)
                    ELSE 0 
                END as conversions_change,
                CASE 
                    WHEN p.prev_ctr > 0 THEN ROUND((c.avg_ctr - p.prev_ctr) / p.prev_ctr * 100, 1)
                    ELSE 0 
                END as ctr_change,
                CASE 
                    WHEN p.prev_roas > 0 THEN ROUND((c.avg_roas - p.prev_roas) / p.prev_roas * 100, 1)
                    ELSE 0 
                END as roas_change
            FROM current_period c
            CROSS JOIN previous_period p
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("days", "INT64", days),
                ]
            )
            
            df = self.bq_client.client.query(sql, job_config=job_config).to_dataframe()
            
            if df.empty:
                logger.warning("No KPI data found in BigQuery")
                return None
                
            row = df.iloc[0]
            return {
                'total_spend': float(row['total_spend'] or 0),
                'total_impressions': int(row['total_impressions'] or 0),
                'total_clicks': int(row['total_clicks'] or 0),
                'total_conversions': int(row['total_conversions'] or 0),
                'avg_ctr': float(row['avg_ctr'] or 0),
                'avg_roas': float(row['avg_roas'] or 0),
                'changes': {
                    'spend': float(row['spend_change'] or 0),
                    'impressions': float(row['impressions_change'] or 0),
                    'clicks': float(row['clicks_change'] or 0),
                    'conversions': float(row['conversions_change'] or 0),
                    'ctr': float(row['ctr_change'] or 0),
                    'roas': float(row['roas_change'] or 0),
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get KPI summary from BigQuery: {e}")
            return None

    async def get_time_series(self, days: int = 30) -> List[Dict]:
        """Get time series data for charts."""
        if not self.is_available():
            return []
        
        try:
            sql = f"""
            WITH daily_data AS (
                -- Google Ads data
                SELECT 
                    'google' as platform,
                    date,
                    COALESCE(
                        CAST(cost AS FLOAT64),
                        CAST(cost_micros AS FLOAT64) / 1000000,
                        0
                    ) as spend,
                    CAST(impressions AS INT64) as impressions,
                    CAST(clicks AS INT64) as clicks,
                    CAST(conversions AS FLOAT64) as conversions
                FROM `{self.project_id}.{self.dataset_id}.campaigns_performance`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                
                UNION ALL
                
                -- Multi-platform data
                SELECT 
                    platform,
                    date,
                    CAST(spend AS FLOAT64) as spend,
                    CAST(impressions AS INT64) as impressions,
                    CAST(clicks AS INT64) as clicks,
                    CAST(conversions AS FLOAT64) as conversions
                FROM `{self.project_id}.{self.dataset_id}.ad_metrics`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                  AND platform IN ('microsoft', 'linkedin')
            )
            SELECT 
                date,
                SUM(spend) as daily_spend,
                SUM(impressions) as daily_impressions,
                SUM(clicks) as daily_clicks,
                SUM(conversions) as daily_conversions
            FROM daily_data
            GROUP BY date
            ORDER BY date
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("days", "INT64", days)
                ]
            )
            
            df = self.bq_client.query(sql, job_config=job_config)
            
            if df.empty:
                return []
            
            results = []
            for _, row in df.iterrows():
                results.append({
                    "date": str(row['date']),
                    "spend": float(row['daily_spend']) if row['daily_spend'] else 0.0,
                    "impressions": int(row['daily_impressions']) if row['daily_impressions'] else 0,
                    "clicks": int(row['daily_clicks']) if row['daily_clicks'] else 0,
                    "conversions": int(row['daily_conversions']) if row['daily_conversions'] else 0
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get time series data: {e}")
            return []

    async def get_platform_performance(self, days: int = 30) -> List[Dict]:
        """Get platform performance breakdown from BigQuery."""
        if not self.is_available():
            raise ValueError("BigQuery client not available")
        
        try:
            sql = f"""
            WITH platform_data AS (
                -- Google Ads data (handle cost_micros conversion)
                SELECT 
                    'google' as platform,
                    'Google Ads' as name,
                    SUM(CAST(impressions AS INT64)) as impressions,
                    SUM(CAST(clicks AS INT64)) as clicks,
                    -- Handle both cost and cost_micros fields
                    SUM(COALESCE(
                        CAST(cost AS FLOAT64),
                        CAST(cost_micros AS FLOAT64) / 1000000,
                        0
                    )) as spend,
                    SUM(CAST(conversions AS FLOAT64)) as conversions
                FROM `{self.project_id}.{self.dataset_id}.campaigns_performance`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                GROUP BY platform, name
                
                UNION ALL
                
                -- Multi-platform ad metrics
                SELECT 
                    platform,
                    CASE platform
                        WHEN 'reddit' THEN 'Reddit Ads'
                        WHEN 'microsoft' THEN 'Microsoft Ads' 
                        WHEN 'linkedin' THEN 'LinkedIn Ads'
                        ELSE INITCAP(platform) || ' Ads'
                    END as name,
                    SUM(CAST(impressions AS INT64)) as impressions,
                    SUM(CAST(clicks AS INT64)) as clicks,
                    SUM(CAST(spend AS FLOAT64)) as spend,
                    SUM(CAST(conversions AS FLOAT64)) as conversions
                FROM `{self.project_id}.{self.dataset_id}.ad_metrics`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                  AND platform IN ('microsoft', 'linkedin')
                GROUP BY platform, name
            )
            SELECT 
                platform,
                name,
                impressions,
                clicks,
                spend,
                conversions,
                CASE 
                    WHEN impressions > 0 THEN ROUND(clicks / impressions * 100, 2)
                    ELSE 0 
                END as ctr,
                CASE 
                    WHEN spend > 0 THEN ROUND(conversions * 100 / spend, 1)
                    ELSE 0 
                END as roas,
                'active' as status  -- TODO: Determine actual status from data
            FROM platform_data
            ORDER BY spend DESC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("days", "INT64", days),
                ]
            )
            
            df = self.bq_client.client.query(sql, job_config=job_config).to_dataframe()
            
            if df.empty:
                logger.warning("No platform data found in BigQuery")
                return []
                
            return [
                {
                    'platform': row['platform'],
                    'name': row['name'],
                    'impressions': int(row['impressions'] or 0),
                    'clicks': int(row['clicks'] or 0),
                    'spend': float(row['spend'] or 0),
                    'conversions': int(row['conversions'] or 0),
                    'ctr': float(row['ctr'] or 0),
                    'roas': float(row['roas'] or 0),
                    'status': row['status']
                }
                for _, row in df.iterrows()
            ]
            
        except Exception as e:
            logger.error(f"Failed to get platform performance from BigQuery: {e}")
            return []

    async def get_time_series_data(self, days: int = 30) -> Dict:
        """Get time series data from BigQuery for performance trends."""
        if not self.is_available():
            raise ValueError("BigQuery client not available")
        
        try:
            sql = f"""
            WITH platform_daily AS (
                -- Google Ads daily data (handle cost_micros conversion)
                SELECT 
                    date,
                    'google' as platform,
                    -- Handle both cost and cost_micros fields
                    SUM(COALESCE(
                        CAST(cost AS FLOAT64),
                        CAST(cost_micros AS FLOAT64) / 1000000,
                        0
                    )) as spend,
                    SUM(CAST(conversions AS FLOAT64)) as conversions,
                    CASE 
                        WHEN SUM(CAST(impressions AS INT64)) > 0 THEN SUM(CAST(clicks AS INT64)) / SUM(CAST(impressions AS INT64)) * 100
                        ELSE 0 
                    END as ctr,
                    CASE 
                        WHEN SUM(COALESCE(CAST(cost AS FLOAT64), CAST(cost_micros AS FLOAT64) / 1000000, 0)) > 0 
                        THEN SUM(CAST(conversions AS FLOAT64)) * 100 / SUM(COALESCE(CAST(cost AS FLOAT64), CAST(cost_micros AS FLOAT64) / 1000000, 0))
                        ELSE 0 
                    END as roas
                FROM `{self.project_id}.{self.dataset_id}.campaigns_performance`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                GROUP BY date, platform
                
                UNION ALL
                
                -- Multi-platform daily data
                SELECT 
                    date,
                    platform,
                    SUM(CAST(spend AS FLOAT64)) as spend,
                    SUM(CAST(conversions AS FLOAT64)) as conversions,
                    CASE 
                        WHEN SUM(CAST(impressions AS INT64)) > 0 THEN SUM(CAST(clicks AS INT64)) / SUM(CAST(impressions AS INT64)) * 100
                        ELSE 0 
                    END as ctr,
                    CASE 
                        WHEN SUM(CAST(spend AS FLOAT64)) > 0 THEN SUM(CAST(conversions AS FLOAT64)) * 100 / SUM(CAST(spend AS FLOAT64))
                        ELSE 0 
                    END as roas
                FROM `{self.project_id}.{self.dataset_id}.ad_metrics`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL GREATEST(@days, 90) DAY)
                  AND platform IN ('microsoft', 'linkedin')
                GROUP BY date, platform
            )
            SELECT 
                date,
                platform,
                spend,
                conversions,
                ROUND(ctr, 2) as ctr,
                ROUND(roas, 1) as roas
            FROM platform_daily
            ORDER BY date, platform
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("days", "INT64", days),
                ]
            )
            
            df = self.bq_client.client.query(sql, job_config=job_config).to_dataframe()
            
            if df.empty:
                logger.warning("No time series data found in BigQuery")
                return {"dates": [], "google": [], "reddit": [], "microsoft": [], "linkedin": []}
            
            # Pivot the data for time series format
            platforms = ['google', 'reddit', 'microsoft', 'linkedin']
            dates = sorted(df['date'].unique())
            
            result = {
                "dates": [date.strftime('%Y-%m-%d') for date in dates],
                "google": [],
                "reddit": [],
                "microsoft": [],
                "linkedin": []
            }
            
            for date in dates:
                day_data = df[df['date'] == date]
                for platform in platforms:
                    platform_data = day_data[day_data['platform'] == platform]
                    if not platform_data.empty:
                        row = platform_data.iloc[0]
                        result[platform].append({
                            'spend': float(row['spend'] or 0),
                            'conversions': float(row['conversions'] or 0),
                            'ctr': float(row['ctr'] or 0),
                            'roas': float(row['roas'] or 0)
                        })
                    else:
                        result[platform].append({
                            'spend': 0,
                            'conversions': 0,
                            'ctr': 0,
                            'roas': 0
                        })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get time series data from BigQuery: {e}")
            return {"dates": [], "google": [], "reddit": [], "microsoft": [], "linkedin": []}


# Global service instance
_bigquery_service = None

def get_bigquery_service() -> DashboardBigQueryService:
    """Get or create the global BigQuery service instance."""
    global _bigquery_service
    if _bigquery_service is None:
        _bigquery_service = DashboardBigQueryService()
    return _bigquery_service
