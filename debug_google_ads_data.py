"""Debug why Google Ads data is missing from the dashboard."""

import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_google_ads_data():
    """Debug Google Ads data availability in BigQuery."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        logger.info("🔍 Debugging Google Ads Data in BigQuery")
        logger.info("=" * 70)
        
        if not bq_service.is_available():
            logger.error("❌ BigQuery service not available")
            return False
        
        logger.info(f"📊 Project: {bq_service.bq_client.project_id}")
        logger.info(f"📚 Dataset: {bq_service.bq_client.dataset_id}")
        logger.info("")
        
        # 1. Check campaigns_performance table (legacy Google Ads)
        logger.info("🔍 Checking campaigns_performance table (legacy Google Ads):")
        
        google_legacy_query = f"""
        SELECT 
            COUNT(*) as total_records,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            SUM(COALESCE(CAST(cost AS FLOAT64), CAST(cost_micros AS FLOAT64) / 1000000, 0)) as total_spend,
            SUM(CAST(clicks AS INT64)) as total_clicks,
            SUM(CAST(conversions AS FLOAT64)) as total_conversions
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        """
        
        legacy_df = bq_service.bq_client.query(google_legacy_query)
        
        if not legacy_df.empty:
            row = legacy_df.iloc[0]
            logger.info(f"  📊 Legacy Google Ads Data:")
            logger.info(f"     Records: {int(row['total_records']):,}")
            logger.info(f"     Date Range: {row['earliest_date']} to {row['latest_date']}")
            logger.info(f"     Spend: ${row['total_spend']:,.2f}")
            logger.info(f"     Clicks: {int(row['total_clicks']):,}")
            logger.info(f"     Conversions: {int(row['total_conversions'])}")
        else:
            logger.info("  ❌ No data in campaigns_performance table")
        
        # 2. Check Google Ads Data Transfer tables (p_* tables)
        logger.info("\n🔍 Checking Google Ads Data Transfer tables:")
        
        # List all tables starting with p_
        list_tables_query = f"""
        SELECT 
            table_id as table_name,
            row_count,
            TIMESTAMP_MILLIS(last_modified_time) as last_modified
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.__TABLES__`
        WHERE table_id LIKE 'p_%'
        ORDER BY row_count DESC
        LIMIT 10
        """
        
        tables_df = bq_service.bq_client.query(list_tables_query)
        
        if not tables_df.empty:
            logger.info(f"  📊 Found {len(tables_df)} Google Ads Data Transfer tables:")
            total_rows = 0
            for _, row in tables_df.iterrows():
                total_rows += row['row_count']
                logger.info(f"     {row['table_name']}: {int(row['row_count']):,} rows (modified: {row['last_modified']})")
            logger.info(f"  📊 Total rows in Data Transfer tables: {total_rows:,}")
        else:
            logger.info("  ❌ No Google Ads Data Transfer tables found")
        
        # 3. Check specific campaign stats from Data Transfer
        try:
            campaign_stats_query = f"""
            SELECT 
                COUNT(*) as records,
                MIN(segments_date) as earliest_date,
                MAX(segments_date) as latest_date,
                SUM(metrics_cost_micros) / 1000000 as total_spend,
                SUM(metrics_clicks) as total_clicks,
                SUM(metrics_conversions) as total_conversions
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.p_ads_CampaignStats_7431593382`
            WHERE segments_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            """
            
            campaign_df = bq_service.bq_client.query(campaign_stats_query)
            
            if not campaign_df.empty:
                row = campaign_df.iloc[0]
                logger.info(f"\n📊 Google Ads Data Transfer Campaign Stats:")
                logger.info(f"     Records: {int(row['records']):,}")
                logger.info(f"     Date Range: {row['earliest_date']} to {row['latest_date']}")
                logger.info(f"     Spend: ${row['total_spend']:,.2f}")
                logger.info(f"     Clicks: {int(row['total_clicks']):,}")
                logger.info(f"     Conversions: {int(row['total_conversions'])}")
            else:
                logger.info("\n❌ No recent data in p_ads_CampaignStats table")
                
        except Exception as e:
            logger.info(f"\n⚠️  Could not query campaign stats: {e}")
        
        # 4. Check what the BigQuery service is actually returning
        logger.info("\n🔍 Testing BigQuery service methods:")
        
        # Test KPI summary
        kpi_data = await bq_service.get_kpi_summary(30)
        if kpi_data:
            logger.info(f"  📊 KPI Summary:")
            logger.info(f"     Total Spend: ${kpi_data['total_spend']:,.2f}")
            logger.info(f"     Total Clicks: {kpi_data['total_clicks']:,}")
            logger.info(f"     Total Conversions: {kpi_data['total_conversions']:,}")
        else:
            logger.info("  ❌ KPI summary returned no data")
        
        # Test platform performance
        platform_data = await bq_service.get_platform_performance(30)
        if platform_data:
            logger.info(f"  📊 Platform Performance ({len(platform_data)} platforms):")
            for platform in platform_data:
                logger.info(f"     {platform['name']}: ${platform['spend']:,.2f} spend, {platform['conversions']} conversions")
        else:
            logger.info("  ❌ Platform performance returned no data")
        
        # 5. Check the actual query being used in platform performance
        logger.info("\n🔍 Testing raw platform query:")
        
        platform_query = f"""
        WITH platform_data AS (
            -- Google Ads data
            SELECT 
                'google' as platform,
                'Google Ads' as platform_name,
                COALESCE(
                    CAST(cost AS FLOAT64),
                    CAST(cost_micros AS FLOAT64) / 1000000,
                    0
                ) as spend,
                CAST(impressions AS INT64) as impressions,
                CAST(clicks AS INT64) as clicks,
                CAST(conversions AS FLOAT64) as conversions
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            
            UNION ALL
            
            -- Multi-platform data
            SELECT 
                platform,
                CASE 
                    WHEN platform = 'microsoft' THEN 'Microsoft Ads'
                    WHEN platform = 'linkedin' THEN 'LinkedIn Ads'
                    WHEN platform = 'reddit' THEN 'Reddit Ads'
                    ELSE INITCAP(platform) || ' Ads'
                END as platform_name,
                CAST(spend AS FLOAT64) as spend,
                CAST(impressions AS INT64) as impressions,
                CAST(clicks AS INT64) as clicks,
                CAST(conversions AS FLOAT64) as conversions
            FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        )
        SELECT 
            platform,
            platform_name,
            SUM(spend) as total_spend,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(conversions) as total_conversions
        FROM platform_data
        GROUP BY platform, platform_name
        HAVING SUM(spend) > 0 OR SUM(clicks) > 0
        ORDER BY total_spend DESC
        """
        
        raw_platform_df = bq_service.bq_client.query(platform_query)
        
        if not raw_platform_df.empty:
            logger.info(f"  📊 Raw Platform Query Results ({len(raw_platform_df)} platforms):")
            for _, row in raw_platform_df.iterrows():
                logger.info(f"     {row['platform_name']}: ${row['total_spend']:,.2f} spend, {int(row['total_clicks']):,} clicks, {int(row['total_conversions'])} conversions")
        else:
            logger.info("  ❌ Raw platform query returned no data")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_google_ads_data())
    
    if success:
        print("=" * 70)
        print("✅ Google Ads data debugging completed!")
    else:
        print("=" * 70)
        print("❌ Google Ads data debugging failed")
