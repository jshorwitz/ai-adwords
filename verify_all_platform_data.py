"""Verify all platform data in BigQuery after sync."""

import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_platform_data():
    """Verify data for all platforms in BigQuery."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            logger.error("❌ BigQuery service not available")
            return False
        
        logger.info("🔍 Verifying platform data in BigQuery...")
        logger.info(f"📊 Project: {bq_service.bq_client.project_id}")
        logger.info(f"📚 Dataset: {bq_service.bq_client.dataset_id}")
        
        # Detailed platform breakdown query
        platform_query = f"""
        SELECT 
            platform,
            COUNT(*) as total_records,
            COUNT(DISTINCT date) as unique_dates,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(spend) as total_spend,
            SUM(conversions) as total_conversions,
            ROUND(AVG(ctr), 2) as avg_ctr,
            ROUND(AVG(cpc), 2) as avg_cpc,
            ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2) as cpa,
            COUNT(DISTINCT campaign_id) as unique_campaigns
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
        GROUP BY platform
        ORDER BY total_spend DESC
        """
        
        platform_df = bq_service.bq_client.query(platform_query)
        
        if platform_df.empty:
            logger.warning("⚠️  No data found in ad_metrics table")
            return False
        
        logger.info("📊 Platform Data Summary:")
        logger.info("=" * 100)
        
        total_spend = 0
        total_conversions = 0
        total_clicks = 0
        
        for _, row in platform_df.iterrows():
            platform = row['platform'].title()
            records = int(row['total_records'])
            spend = float(row['total_spend'])
            clicks = int(row['total_clicks'])
            conversions = int(row['total_conversions'])
            campaigns = int(row['unique_campaigns'])
            cpa = row['cpa'] if row['cpa'] else 0
            
            total_spend += spend
            total_conversions += conversions
            total_clicks += clicks
            
            logger.info(f"🎯 {platform} Ads:")
            logger.info(f"    Records: {records:,}")
            logger.info(f"    Campaigns: {campaigns}")
            logger.info(f"    Date Range: {row['earliest_date']} to {row['latest_date']}")
            logger.info(f"    Spend: ${spend:,.2f}")
            logger.info(f"    Clicks: {clicks:,}")
            logger.info(f"    Conversions: {conversions}")
            logger.info(f"    CPA: ${cpa:.2f}")
            logger.info(f"    CTR: {row['avg_ctr']}%")
            logger.info("")
        
        logger.info("📊 Combined Totals:")
        logger.info(f"  Total Spend: ${total_spend:,.2f}")
        logger.info(f"  Total Clicks: {total_clicks:,}")
        logger.info(f"  Total Conversions: {total_conversions}")
        logger.info(f"  Overall CPA: ${total_spend/total_conversions:.2f}" if total_conversions > 0 else "  Overall CPA: N/A")
        
        # Check most recent data updates
        recent_query = f"""
        SELECT 
            platform,
            campaign_name,
            date,
            spend,
            clicks,
            conversions,
            updated_at
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.ad_metrics`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 5 DAY)
        ORDER BY updated_at DESC, spend DESC
        LIMIT 10
        """
        
        recent_df = bq_service.bq_client.query(recent_query)
        
        if not recent_df.empty:
            logger.info("📅 Most Recent Campaign Data:")
            logger.info("-" * 80)
            
            for _, row in recent_df.head(5).iterrows():
                logger.info(f"  {row['platform'].title()}: {row['campaign_name']}")
                logger.info(f"    Date: {row['date']}, Spend: ${row['spend']:.2f}, Conversions: {int(row['conversions'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Platform data verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Platform Data Verification")
    print("=" * 50)
    
    success = asyncio.run(verify_platform_data())
    
    if success:
        print("=" * 50)
        print("✅ Platform data verification completed!")
    else:
        print("=" * 50)
        print("❌ Platform data verification failed")
