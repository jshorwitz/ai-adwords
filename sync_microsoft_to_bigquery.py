"""Sync Microsoft Ads data to BigQuery synter_analytics table."""

import os
import logging
import asyncio
from datetime import datetime, timedelta, timezone

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_microsoft_ads_data():
    """Sync Microsoft Ads data to BigQuery."""
    try:
        # Set Microsoft Ads developer token
        os.environ["MICROSOFT_ADS_DEVELOPER_TOKEN"] = "11085M29YT845526"
        os.environ["MOCK_MICROSOFT"] = "true"  # Enable mock mode for testing
        
        logger.info("🚀 Starting Microsoft Ads to BigQuery sync...")
        
        # Initialize Microsoft Ads client
        from src.integrations.microsoft_ads import MicrosoftAdsClient
        
        async with MicrosoftAdsClient() as ms_client:
            # Test connection first
            connection_result = await ms_client.test_connection()
            logger.info(f"📊 Connection Status: {connection_result['status']}")
            
            if not connection_result['connected']:
                logger.error(f"❌ Connection failed: {connection_result.get('error', 'Unknown error')}")
                return False
            
            # Get campaign data for last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            campaigns = await ms_client.get_campaigns(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            if not campaigns:
                logger.warning("⚠️  No Microsoft Ads campaign data found")
                return False
            
            logger.info(f"✅ Retrieved {len(campaigns)} Microsoft campaigns")
            
            # Initialize BigQuery client
            from src.ads.bigquery_client import create_bigquery_client_from_env
            
            bq_client = create_bigquery_client_from_env()
            
            logger.info(f"📊 BigQuery Project: {bq_client.project_id}")
            logger.info(f"📚 BigQuery Dataset: {bq_client.dataset_id}")
            
            # Convert campaigns to ad_metrics format for BigQuery
            ad_metrics_data = []
            
            for campaign in campaigns:
                ad_metrics_row = {
                    'platform': 'microsoft',
                    'date': campaign.date,
                    'account_id': 'microsoft_account_1',
                    'account_name': 'Microsoft Ads Account',
                    'campaign_id': campaign.campaign_id,
                    'campaign_name': campaign.campaign_name,
                    'adgroup_id': f"{campaign.campaign_id}_adgroup_1",
                    'adgroup_name': f"{campaign.campaign_name} - AdGroup 1",
                    'ad_id': f"{campaign.campaign_id}_ad_1",
                    'impressions': campaign.impressions,
                    'clicks': campaign.clicks,
                    'spend': campaign.spend,
                    'conversions': campaign.conversions,
                    'ctr': campaign.ctr,
                    'cpc': campaign.cpc,
                    'conversion_rate': campaign.conversion_rate,
                    'updated_at': datetime.now(timezone.utc)
                }
                ad_metrics_data.append(ad_metrics_row)
            
            # Load data to BigQuery
            logger.info(f"📤 Loading {len(ad_metrics_data)} records to BigQuery ad_metrics table...")
            
            table_name = "ad_metrics"
            
            # Create DataFrame for BigQuery upload
            import pandas as pd
            df = pd.DataFrame(ad_metrics_data)
            
            # Convert date column to proper format for BigQuery
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Upload to BigQuery using insert_dataframe method
            bq_client.insert_dataframe(table_name, df)
            result = True  # Success if no exception thrown
            
            if result:
                logger.info("✅ Microsoft Ads data successfully loaded to BigQuery!")
                
                # Verify the data
                verify_query = f"""
                SELECT 
                    platform,
                    COUNT(*) as records,
                    SUM(spend) as total_spend,
                    SUM(clicks) as total_clicks,
                    SUM(conversions) as total_conversions,
                    MAX(date) as latest_date
                FROM `{bq_client.project_id}.{bq_client.dataset_id}.{table_name}`
                WHERE platform = 'microsoft'
                GROUP BY platform
                """
                
                verify_df = bq_client.query(verify_query)
                
                if not verify_df.empty:
                    row = verify_df.iloc[0]
                    logger.info("📊 Microsoft Ads Data Verification:")
                    logger.info(f"  Records: {int(row['records'])}")
                    logger.info(f"  Total Spend: ${row['total_spend']:,.2f}")
                    logger.info(f"  Total Clicks: {int(row['total_clicks']):,}")
                    logger.info(f"  Total Conversions: {int(row['total_conversions'])}")
                    logger.info(f"  Latest Date: {row['latest_date']}")
                else:
                    logger.warning("⚠️  No Microsoft data found after upload verification")
                    
                return True
            else:
                logger.error("❌ Failed to load Microsoft Ads data to BigQuery")
                return False
                
    except Exception as e:
        logger.error(f"❌ Microsoft Ads sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Microsoft Ads to BigQuery Sync")
    print("=" * 50)
    
    success = asyncio.run(sync_microsoft_ads_data())
    
    if success:
        print("=" * 50)
        print("✅ Microsoft Ads sync completed successfully!")
        print("💡 Check the BigQuery ad_metrics table for the new Microsoft data")
    else:
        print("=" * 50)
        print("❌ Microsoft Ads sync failed")
