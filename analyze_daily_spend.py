"""Analyze daily spend breakdown for Google Ads and extend Microsoft/LinkedIn to 90 days."""

import logging
import asyncio
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_daily_spend():
    """Analyze daily spend patterns and prepare 90-day view."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        logger.info("📊 Daily Spend Analysis - Live Platforms Only")
        logger.info("=" * 80)
        
        if not bq_service.is_available():
            logger.error("❌ BigQuery service not available")
            return False
        
        # 1. Google Ads daily breakdown
        logger.info("🔍 Google Ads Daily Spend Breakdown:")
        
        google_daily_query = f"""
        SELECT 
            date,
            COUNT(*) as campaigns,
            SUM(CAST(impressions AS INT64)) as impressions,
            SUM(CAST(clicks AS INT64)) as clicks,
            SUM(COALESCE(
                CAST(cost AS FLOAT64),
                CAST(cost_micros AS FLOAT64) / 1000000,
                0
            )) as spend,
            SUM(CAST(conversions AS FLOAT64)) as conversions,
            ROUND(AVG(CAST(ctr AS FLOAT64)), 2) as avg_ctr
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY date
        ORDER BY date DESC
        LIMIT 20
        """
        
        google_df = bq_service.bq_client.query(google_daily_query)
        
        if not google_df.empty:
            logger.info("📅 Last 20 days of Google Ads activity:")
            total_google_spend = 0
            for _, row in google_df.iterrows():
                total_google_spend += row['spend']
                logger.info(f"  {row['date']}: ${row['spend']:,.2f} spend, {int(row['clicks']):,} clicks, {int(row['conversions'])} conversions ({row['campaigns']} campaigns)")
            
            logger.info(f"📊 Google Ads Total (last 20 days): ${total_google_spend:,.2f}")
        else:
            logger.warning("⚠️  No Google Ads daily data found")
        
        # 2. Microsoft Ads - expand to 90 days of mock data
        logger.info("\n🔍 Microsoft Ads - Generating 90 days of data:")
        
        microsoft_daily_query = f"""
        SELECT 
            platform,
            date,
            SUM(CAST(spend AS FLOAT64)) as spend,
            SUM(CAST(clicks AS INT64)) as clicks,
            SUM(CAST(conversions AS FLOAT64)) as conversions
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
        WHERE platform = 'microsoft'
          AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY platform, date
        ORDER BY date DESC
        """
        
        microsoft_df = bq_service.bq_client.query(microsoft_daily_query)
        
        if not microsoft_df.empty:
            logger.info(f"📅 Microsoft Ads current data ({len(microsoft_df)} days):")
            total_ms_spend = 0
            for _, row in microsoft_df.iterrows():
                total_ms_spend += row['spend']
                logger.info(f"  {row['date']}: ${row['spend']:,.2f} spend, {int(row['clicks']):,} clicks, {int(row['conversions'])} conversions")
            
            logger.info(f"📊 Microsoft Ads Total: ${total_ms_spend:,.2f}")
        else:
            logger.warning("⚠️  No Microsoft Ads data found")
        
        # 3. LinkedIn Ads - expand to 90 days
        logger.info("\n🔍 LinkedIn Ads - Current data range:")
        
        linkedin_daily_query = f"""
        SELECT 
            platform,
            date,
            SUM(CAST(spend AS FLOAT64)) as spend,
            SUM(CAST(clicks AS INT64)) as clicks,
            SUM(CAST(conversions AS FLOAT64)) as conversions
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
        WHERE platform = 'linkedin'
          AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY platform, date
        ORDER BY date DESC
        """
        
        linkedin_df = bq_service.bq_client.query(linkedin_daily_query)
        
        if not linkedin_df.empty:
            logger.info(f"📅 LinkedIn Ads current data ({len(linkedin_df)} days):")
            total_li_spend = 0
            for _, row in linkedin_df.iterrows():
                total_li_spend += row['spend']
                logger.info(f"  {row['date']}: ${row['spend']:,.2f} spend, {int(row['clicks']):,} clicks, {int(row['conversions'])} conversions")
            
            logger.info(f"📊 LinkedIn Ads Total: ${total_li_spend:,.2f}")
        else:
            logger.warning("⚠️  No LinkedIn Ads data found")
        
        # 4. Create comprehensive daily view
        logger.info("\n🔍 Combined Daily View (All Live Platforms):")
        
        combined_daily_query = f"""
        WITH all_platform_data AS (
            -- Google Ads data
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
            
            -- Microsoft & LinkedIn Ads
            SELECT 
                CASE 
                    WHEN platform = 'microsoft' THEN 'Microsoft Ads'
                    WHEN platform = 'linkedin' THEN 'LinkedIn Ads'
                    ELSE platform
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
            SUM(spend) as total_daily_spend,
            SUM(clicks) as total_daily_clicks,
            SUM(conversions) as total_daily_conversions,
            COUNT(DISTINCT platform) as active_platforms,
            STRING_AGG(DISTINCT platform ORDER BY platform) as platforms
        FROM all_platform_data
        GROUP BY date
        ORDER BY date DESC
        LIMIT 15
        """
        
        combined_df = bq_service.bq_client.query(combined_daily_query)
        
        if not combined_df.empty:
            logger.info("📅 Combined daily performance (last 15 days):")
            for _, row in combined_df.iterrows():
                logger.info(f"  {row['date']}: ${row['total_daily_spend']:,.2f} spend, {int(row['total_daily_clicks']):,} clicks, {int(row['total_daily_conversions'])} conversions ({int(row['active_platforms'])} platforms: {row['platforms']})")
        else:
            logger.warning("⚠️  No combined daily data found")
        
        # 5. Summary for dashboard requirements
        logger.info("\n📋 Dashboard Requirements Summary:")
        logger.info("✅ Google Ads: Daily breakdown available (historical data from July-August)")
        logger.info("⚠️  Microsoft Ads: Limited to a few days, need 90-day mock data generation")
        logger.info("⚠️  LinkedIn Ads: Limited data range, need 90-day expansion")
        logger.info("❌ Reddit Ads: Remove from dashboard (not live)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Daily spend analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(analyze_daily_spend())
    
    if success:
        print("=" * 80)
        print("✅ Daily spend analysis completed!")
        print("💡 Next steps:")
        print("  1. Generate 90 days of Microsoft/LinkedIn mock data")
        print("  2. Remove Reddit from dashboard")
        print("  3. Create daily breakdown charts")
    else:
        print("=" * 80)
        print("❌ Daily spend analysis failed")
