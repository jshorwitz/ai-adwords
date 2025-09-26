"""Test BigQuery connection to synter_analytics dataset and verify Google spend data."""

import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bigquery_connection():
    """Test BigQuery connection to synter_analytics dataset."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        logger.info("🔍 Testing BigQuery connection to synter_analytics...")
        
        # Get BigQuery service
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            logger.error("❌ BigQuery service not available")
            return False
        
        logger.info(f"✅ BigQuery client initialized")
        logger.info(f"📊 Project: {bq_service.bq_client.project_id}")
        logger.info(f"📚 Dataset: {bq_service.bq_client.dataset_id}")
        
        # Test direct query to campaigns_performance table
        test_query = f"""
        SELECT 
            date,
            campaign_name,
            impressions,
            clicks,
            -- Show both cost and cost_micros to see which exists
            cost,
            cost_micros,
            COALESCE(
                CAST(cost AS FLOAT64),
                CAST(cost_micros AS FLOAT64) / 1000000,
                0
            ) as spend_usd,
            conversions
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        ORDER BY date DESC, spend_usd DESC
        LIMIT 10
        """
        
        logger.info("🔍 Testing direct query to campaigns_performance table...")
        df = bq_service.bq_client.query(test_query)
        
        if df.empty:
            logger.warning("⚠️  No data found in campaigns_performance table")
        else:
            logger.info(f"✅ Found {len(df)} records in campaigns_performance")
            logger.info("📊 Sample data:")
            for _, row in df.head().iterrows():
                spend = row['spend_usd'] if row['spend_usd'] else 0
                logger.info(f"  {row['date']}: {row['campaign_name']} - Spend: ${spend:.2f}")
        
        # Test KPI summary
        logger.info("🔍 Testing KPI summary query...")
        kpi_data = await bq_service.get_kpi_summary(30)
        
        if kpi_data:
            logger.info("✅ KPI data retrieved successfully")
            logger.info(f"📊 Total Spend: ${kpi_data['total_spend']:,.2f}")
            logger.info(f"📊 Total Impressions: {kpi_data['total_impressions']:,}")
            logger.info(f"📊 Total Clicks: {kpi_data['total_clicks']:,}")
            logger.info(f"📊 Total Conversions: {kpi_data['total_conversions']:,}")
        else:
            logger.warning("⚠️  No KPI data returned")
        
        # Test platform performance
        logger.info("🔍 Testing platform performance query...")
        platform_data = await bq_service.get_platform_performance(30)
        
        if platform_data:
            logger.info("✅ Platform data retrieved successfully")
            for platform in platform_data:
                logger.info(f"📊 {platform['name']}: ${platform['spend']:,.2f} spend, {platform['conversions']} conversions")
        else:
            logger.warning("⚠️  No platform data returned")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_async_test():
    """Run async BigQuery tests."""
    return test_bigquery_connection()

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Testing BigQuery connection to synter_analytics dataset")
    print("=" * 60)
    
    success = asyncio.run(run_async_test())
    
    if success:
        print("=" * 60)
        print("✅ BigQuery test completed successfully!")
    else:
        print("=" * 60)
        print("❌ BigQuery test failed - check logs above")
