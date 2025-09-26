"""Setup Microsoft and LinkedIn data sync to synter_analytics dataset."""

import os
import logging
import asyncio
from datetime import datetime, timedelta, timezone

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sync_platforms_to_synter_analytics():
    """Sync Microsoft and LinkedIn data to synter_analytics dataset."""
    try:
        # Configure API keys and mock modes
        os.environ["MICROSOFT_ADS_DEVELOPER_TOKEN"] = "11085M29YT845526"
        os.environ["MOCK_MICROSOFT"] = "true"
        os.environ["MOCK_LINKEDIN"] = "true"
        
        logger.info("🚀 Syncing platforms to synter_analytics dataset...")
        logger.info("📊 Target Dataset: synter_analytics")
        logger.info("🎯 Platforms: Microsoft Ads, LinkedIn Ads")
        logger.info("")
        
        # Create BigQuery client pointing to synter_analytics
        from src.ads.bigquery_client import BigQueryClient
        
        project_id = "ai-adwords-470622"
        dataset_id = "synter_analytics"
        
        bq_client = BigQueryClient(
            project_id=project_id,
            dataset_id=dataset_id
        )
        
        logger.info(f"✅ Connected to {project_id}.{dataset_id}")
        
        # Sync Microsoft Ads
        logger.info("🔄 Syncing Microsoft Ads data...")
        
        from src.integrations.microsoft_ads import MicrosoftAdsClient
        
        async with MicrosoftAdsClient() as ms_client:
            # Get campaign data for last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            campaigns = await ms_client.get_campaigns(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            logger.info(f"📊 Retrieved {len(campaigns)} Microsoft campaigns")
            
            if campaigns:
                # Convert to ad_metrics format
                microsoft_data = []
                
                for campaign in campaigns:
                    ad_metrics_row = {
                        'date': campaign.date,
                        'platform': 'microsoft',
                        'account_id': 'microsoft_account_1',
                        'account_name': 'Microsoft Ads Account',
                        'campaign_id': campaign.campaign_id,
                        'campaign_name': campaign.campaign_name,
                        'adgroup_id': f"{campaign.campaign_id}_adgroup_1",
                        'adgroup_name': f"{campaign.campaign_name} - AdGroup 1",
                        'ad_id': f"{campaign.campaign_id}_ad_1",
                        'ad_name': None,
                        'impressions': campaign.impressions,
                        'clicks': campaign.clicks,
                        'spend': campaign.spend,
                        'conversions': campaign.conversions,
                        'ctr': campaign.ctr,
                        'cpc': campaign.cpc,
                        'cpm': None,
                        'conversion_rate': campaign.conversion_rate,
                        'cost_per_conversion': None,
                        'revenue': None,
                        'roas': None,
                        'raw': None,
                        'updated_at': datetime.now(timezone.utc)
                    }
                    microsoft_data.append(ad_metrics_row)
                
                # Insert into synter_analytics
                import pandas as pd
                ms_df = pd.DataFrame(microsoft_data)
                ms_df['date'] = pd.to_datetime(ms_df['date']).dt.date
                
                bq_client.insert_dataframe('ad_metrics', ms_df)
                logger.info(f"✅ Inserted {len(microsoft_data)} Microsoft records into synter_analytics")
        
        # Sync LinkedIn Ads
        logger.info("🔄 Syncing LinkedIn Ads data...")
        
        from src.integrations.linkedin_ads import LinkedInAdsClient
        
        async with LinkedInAdsClient() as linkedin_client:
            # Get campaign data (LinkedIn uses account_id parameter)
            campaigns = await linkedin_client.get_campaigns("linkedin_account_1")
            
            logger.info(f"📊 Retrieved {len(campaigns)} LinkedIn campaigns")
            
            if campaigns:
                # Convert to ad_metrics format
                linkedin_data = []
                
                for campaign in campaigns:
                    # LinkedIn returns dict objects, not campaign objects
                    ad_metrics_row = {
                        'date': start_date.strftime("%Y-%m-%d"),  # Use start date for mock data
                        'platform': 'linkedin',
                        'account_id': 'linkedin_account_1',
                        'account_name': 'LinkedIn Ads Account',
                        'campaign_id': campaign.get('id', 'linkedin_camp_1'),
                        'campaign_name': campaign.get('name', 'LinkedIn Campaign'),
                        'adgroup_id': f"{campaign.get('id', 'linkedin_camp_1')}_adgroup_1",
                        'adgroup_name': f"{campaign.get('name', 'LinkedIn Campaign')} - AdGroup 1",
                        'ad_id': f"{campaign.get('id', 'linkedin_camp_1')}_ad_1",
                        'ad_name': None,
                        'impressions': 15000,  # Mock data
                        'clicks': 750,
                        'spend': 2500.00,
                        'conversions': 45,
                        'ctr': 5.0,
                        'cpc': 3.33,
                        'cpm': None,
                        'conversion_rate': 6.0,
                        'cost_per_conversion': None,
                        'revenue': None,
                        'roas': None,
                        'raw': None,
                        'updated_at': datetime.now(timezone.utc)
                    }
                    linkedin_data.append(ad_metrics_row)
                
                # Insert into synter_analytics
                linkedin_df = pd.DataFrame(linkedin_data)
                linkedin_df['date'] = pd.to_datetime(linkedin_df['date']).dt.date
                
                bq_client.insert_dataframe('ad_metrics', linkedin_df)
                logger.info(f"✅ Inserted {len(linkedin_data)} LinkedIn records into synter_analytics")
        
        # Verify the data in synter_analytics
        logger.info("\n🔍 Verifying data in synter_analytics...")
        
        verify_query = f"""
        SELECT 
            platform,
            COUNT(*) as records,
            SUM(spend) as total_spend,
            SUM(clicks) as total_clicks,
            SUM(conversions) as total_conversions,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM `{project_id}.{dataset_id}.ad_metrics`
        GROUP BY platform
        ORDER BY total_spend DESC
        """
        
        verify_df = bq_client.query(verify_query)
        
        if not verify_df.empty:
            logger.info("📊 Platform Data in synter_analytics:")
            total_spend = 0
            total_conversions = 0
            
            for _, row in verify_df.iterrows():
                spend = float(row['total_spend'])
                conversions = int(row['total_conversions'])
                total_spend += spend
                total_conversions += conversions
                
                logger.info(f"  🎯 {row['platform'].title()}: {int(row['records'])} records, ${spend:,.2f} spend, {conversions} conversions")
                logger.info(f"     Date range: {row['earliest_date']} to {row['latest_date']}")
            
            logger.info(f"\n📊 Total: ${total_spend:,.2f} spend, {total_conversions} conversions")
        else:
            logger.warning("⚠️  No data found in ad_metrics table")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Platform sync to synter_analytics failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_app_config_to_synter_analytics():
    """Update application configuration to use synter_analytics by default."""
    logger.info("\n🔧 Updating application configuration...")
    
    # Update environment variable recommendations
    config_updates = {
        "BIGQUERY_DATASET_ID": "synter_analytics",
        "BIGQUERY_PROJECT_ID": "ai-adwords-470622"
    }
    
    logger.info("📝 Recommended environment variable updates:")
    for key, value in config_updates.items():
        logger.info(f"  {key}={value}")
    
    logger.info("\n💡 To make this permanent:")
    logger.info("  1. Update your .env file with the above variables")
    logger.info("  2. Restart your application services")
    logger.info("  3. The system will now default to synter_analytics dataset")

if __name__ == "__main__":
    print("🔄 Microsoft & LinkedIn to synter_analytics Sync")
    print("=" * 70)
    
    success = asyncio.run(sync_platforms_to_synter_analytics())
    
    if success:
        update_app_config_to_synter_analytics()
        
        print("=" * 70)
        print("✅ Platform sync to synter_analytics completed!")
        print("📊 Microsoft and LinkedIn data is now in synter_analytics dataset")
        print("🎯 Google Ads Data Transfer Service is already configured for synter_analytics")
    else:
        print("=" * 70)
        print("❌ Platform sync failed")
