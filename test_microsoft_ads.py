"""Test Microsoft Ads API configuration and connection."""

import os
import logging
import asyncio
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_microsoft_ads_config():
    """Test Microsoft Ads API configuration."""
    logger.info("🔍 Testing Microsoft Ads API configuration...")
    
    # Check environment variables
    developer_token = os.getenv("MICROSOFT_ADS_DEVELOPER_TOKEN")
    client_id = os.getenv("MICROSOFT_ADS_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_ADS_CLIENT_SECRET")
    customer_id = os.getenv("MICROSOFT_ADS_CUSTOMER_ID")
    access_token = os.getenv("MICROSOFT_ADS_ACCESS_TOKEN")
    mock_mode = os.getenv("MOCK_MICROSOFT", "true").lower() == "true"
    
    logger.info(f"📊 Configuration Status:")
    logger.info(f"  Developer Token: {'✅ Set' if developer_token else '❌ Missing'}")
    logger.info(f"  Client ID: {'✅ Set' if client_id else '❌ Missing'}")
    logger.info(f"  Client Secret: {'✅ Set' if client_secret else '❌ Missing'}")
    logger.info(f"  Customer ID: {'✅ Set' if customer_id else '❌ Missing'}")
    logger.info(f"  Access Token: {'✅ Set' if access_token else '❌ Missing'}")
    logger.info(f"  Mock Mode: {'✅ Enabled' if mock_mode else '❌ Disabled'}")
    
    if developer_token:
        logger.info(f"  Developer Token Value: {developer_token}")
    
    # Test Microsoft Ads client
    try:
        from src.integrations.microsoft_ads import MicrosoftAdsClient
        
        logger.info("🔍 Testing Microsoft Ads client initialization...")
        
        async with MicrosoftAdsClient() as ms_client:
            # Test connection
            connection_result = await ms_client.test_connection()
            
            logger.info(f"📊 Connection Test Results:")
            logger.info(f"  Status: {connection_result.get('status', 'Unknown')}")
            logger.info(f"  Connected: {'✅ Yes' if connection_result.get('connected') else '❌ No'}")
            logger.info(f"  Mode: {connection_result.get('mode', 'Unknown')}")
            
            if connection_result.get('error'):
                logger.error(f"  Error: {connection_result['error']}")
            
            # Test data retrieval
            if mock_mode:
                logger.info("🔍 Testing mock data retrieval...")
                
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)
                
                campaigns = await ms_client.get_campaigns(
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                
                logger.info(f"📊 Mock Campaign Data:")
                logger.info(f"  Campaigns Retrieved: {len(campaigns)}")
                
                if campaigns:
                    for campaign in campaigns[:3]:  # Show first 3
                        logger.info(f"    Campaign: {campaign.campaign_name}")
                        logger.info(f"      Spend: ${campaign.spend:.2f}")
                        logger.info(f"      Clicks: {campaign.clicks}")
                        logger.info(f"      Conversions: {campaign.conversions}")
            else:
                logger.info("⚠️  Live mode - skipping data retrieval test")
                
    except Exception as e:
        logger.error(f"❌ Microsoft Ads client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test ETL pipeline integration
    try:
        logger.info("🔍 Testing ETL pipeline integration...")
        from src.etl.multi_platform_pipeline import MultiPlatformETLPipeline
        
        pipeline = MultiPlatformETLPipeline()
        microsoft_enabled = pipeline.platforms_enabled.get('microsoft', False)
        
        logger.info(f"📊 ETL Pipeline Status:")
        logger.info(f"  Microsoft Enabled: {'✅ Yes' if microsoft_enabled else '❌ No'}")
        
        if not microsoft_enabled and not mock_mode:
            logger.warning("⚠️  Microsoft platform not enabled in ETL pipeline")
            logger.info("💡 To enable: Set MOCK_MICROSOFT=false and provide all credentials")
            
    except Exception as e:
        logger.error(f"❌ ETL pipeline test failed: {e}")
        
    return True

if __name__ == "__main__":
    print("🚀 Testing Microsoft Ads API Configuration")
    print("=" * 60)
    
    # Set the developer token from the provided API key
    os.environ["MICROSOFT_ADS_DEVELOPER_TOKEN"] = "11085M29YT845526"
    
    success = asyncio.run(test_microsoft_ads_config())
    
    if success:
        print("=" * 60)
        print("✅ Microsoft Ads configuration test completed!")
    else:
        print("=" * 60)
        print("❌ Microsoft Ads configuration test failed")
