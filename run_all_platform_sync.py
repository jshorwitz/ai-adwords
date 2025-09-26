"""Run data transfer for all platforms (Google, LinkedIn, Microsoft) to BigQuery."""

import os
import logging
import asyncio
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_all_platform_sync():
    """Run data sync for all platforms to BigQuery."""
    try:
        # Configure API keys and mock modes
        os.environ["MICROSOFT_ADS_DEVELOPER_TOKEN"] = "11085M29YT845526"
        os.environ["MOCK_MICROSOFT"] = "true"
        os.environ["MOCK_LINKEDIN"] = "true"
        os.environ["MOCK_REDDIT"] = "true"
        
        logger.info("🚀 Starting multi-platform data sync...")
        logger.info("📊 Platforms: Google Ads, Microsoft Ads, LinkedIn Ads")
        logger.info("🔧 Mode: Mock data generation (OAuth issues with live APIs)")
        
        # Initialize ETL pipeline
        from src.etl.multi_platform_pipeline import MultiPlatformETLPipeline
        
        pipeline = MultiPlatformETLPipeline()
        
        logger.info(f"📊 Platform availability: {pipeline.platforms_enabled}")
        
        # Run sync for last 30 days
        days_back = 30
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"📅 Date range: {start_date} to {end_date}")
        
        # Run all platform syncs
        results = await pipeline.sync_all_platforms(days_back)
        
        logger.info("📊 Sync Results Summary:")
        logger.info(f"  Success: {'✅ Yes' if results.get('success') else '❌ No'}")
        logger.info(f"  Total Records: {results.get('total_records', 0)}")
        
        if results.get('platforms'):
            for platform, platform_result in results['platforms'].items():
                status = platform_result.get('status', 'unknown')
                records = platform_result.get('records_written', 0)
                logger.info(f"  {platform.title()}: {status} - {records} records")
                
                if platform_result.get('error'):
                    logger.error(f"    Error: {platform_result['error']}")
        
        if results.get('errors'):
            logger.error("❌ Errors encountered:")
            for error in results['errors']:
                logger.error(f"  {error}")
        
        # Verify data in BigQuery
        logger.info("🔍 Verifying data in BigQuery...")
        
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if bq_service.is_available():
            # Check updated KPI summary
            kpi_data = await bq_service.get_kpi_summary(30)
            
            if kpi_data:
                logger.info("📊 Updated BigQuery KPI Summary:")
                logger.info(f"  Total Spend: ${kpi_data['total_spend']:,.2f}")
                logger.info(f"  Total Clicks: {kpi_data['total_clicks']:,}")
                logger.info(f"  Total Conversions: {kpi_data['total_conversions']:,}")
            
            # Check platform breakdown
            platform_data = await bq_service.get_platform_performance(30)
            
            if platform_data:
                logger.info("📊 Platform Performance:")
                for platform in platform_data:
                    logger.info(f"  {platform['name']}: ${platform['spend']:,.2f} spend, {platform['conversions']} conversions")
        
        return results.get('success', False)
        
    except Exception as e:
        logger.error(f"❌ Multi-platform sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_individual_syncs():
    """Run individual platform syncs in parallel."""
    logger.info("🚀 Running individual platform syncs...")
    
    # Configure environment
    os.environ["MICROSOFT_ADS_DEVELOPER_TOKEN"] = "11085M29YT845526"
    os.environ["MOCK_MICROSOFT"] = "true"
    os.environ["MOCK_LINKEDIN"] = "true"
    os.environ["MOCK_REDDIT"] = "true"
    
    from src.integrations.microsoft_ads import MicrosoftAdsClient
    from src.integrations.linkedin_ads import LinkedInAdsClient
    from src.ads.bigquery_client import create_bigquery_client_from_env
    
    bq_client = create_bigquery_client_from_env()
    
    # Run Microsoft sync
    logger.info("📊 Syncing Microsoft Ads...")
    try:
        async with MicrosoftAdsClient() as ms_client:
            campaigns = await ms_client.get_campaigns()
            logger.info(f"✅ Microsoft: {len(campaigns)} campaigns retrieved")
    except Exception as e:
        logger.error(f"❌ Microsoft sync failed: {e}")
    
    # Run LinkedIn sync
    logger.info("📊 Syncing LinkedIn Ads...")
    try:
        async with LinkedInAdsClient() as linkedin_client:
            campaigns = await linkedin_client.get_campaigns()
            logger.info(f"✅ LinkedIn: {len(campaigns)} campaigns retrieved")
    except Exception as e:
        logger.error(f"❌ LinkedIn sync failed: {e}")
    
    logger.info("✅ Individual syncs completed")

if __name__ == "__main__":
    print("🚀 Multi-Platform Data Sync to BigQuery")
    print("=" * 60)
    print("📊 Platforms: Google Ads, Microsoft Ads, LinkedIn Ads")
    print("=" * 60)
    
    # First try the unified pipeline
    success = asyncio.run(run_all_platform_sync())
    
    if not success:
        print("\n🔄 Trying individual platform syncs...")
        asyncio.run(run_individual_syncs())
    
    print("=" * 60)
    if success:
        print("✅ Multi-platform sync completed successfully!")
    else:
        print("⚠️  Multi-platform sync completed with some issues")
    print("💡 Check BigQuery ad_metrics table for updated data")
