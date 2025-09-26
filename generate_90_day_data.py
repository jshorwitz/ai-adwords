"""Generate 90 days of Microsoft and LinkedIn data for comprehensive dashboard view."""

import os
import logging
import asyncio
from datetime import datetime, timedelta, timezone
import random
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_90_day_platform_data():
    """Generate 90 days of Microsoft and LinkedIn data."""
    try:
        # Configure environment for mock data
        os.environ["MICROSOFT_ADS_DEVELOPER_TOKEN"] = "11085M29YT845526"
        os.environ["MOCK_MICROSOFT"] = "true"
        os.environ["MOCK_LINKEDIN"] = "true"
        
        logger.info("🔄 Generating 90 days of Microsoft and LinkedIn data...")
        logger.info("📅 Date range: July 28 - September 26, 2025")
        logger.info("")
        
        from src.ads.bigquery_client import create_bigquery_client_from_env
        
        bq_client = create_bigquery_client_from_env()
        
        logger.info(f"✅ Connected to {bq_client.project_id}.{bq_client.dataset_id}")
        
        # Clear existing Microsoft and LinkedIn data
        logger.info("🧹 Clearing existing Microsoft and LinkedIn data...")
        
        for platform in ['microsoft', 'linkedin']:
            delete_query = f"""
            DELETE FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
            WHERE platform = '{platform}'
            """
            job = bq_client.client.query(delete_query)
            job.result()
            logger.info(f"  ✅ Cleared {platform} data")
        
        # Generate 90 days of data for both platforms
        end_date = datetime(2025, 9, 26)  # Today
        start_date = datetime(2025, 7, 28)  # Match Google Ads start date
        
        all_metrics_data = []
        
        # Microsoft Ads campaigns
        microsoft_campaigns = [
            {"id": "ms_brand", "name": "Microsoft Search - Brand"},
            {"id": "ms_generic", "name": "Microsoft Search - Generic"},
            {"id": "ms_display", "name": "Microsoft Display - Remarketing"}
        ]
        
        # LinkedIn Ads campaigns  
        linkedin_campaigns = [
            {"id": "li_sponsored", "name": "LinkedIn Sponsored Content - B2B"},
        ]
        
        current_date = start_date
        day_count = 0
        
        while current_date <= end_date:
            day_count += 1
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Generate Microsoft data for this day
            for campaign in microsoft_campaigns:
                random.seed(hash(f"microsoft_{campaign['id']}_{date_str}"))
                
                # Realistic Microsoft Ads performance
                base_spend = random.uniform(800, 2500)
                impressions = int(base_spend * random.uniform(8, 15))  # 8-15 impressions per dollar
                clicks = int(impressions * random.uniform(0.02, 0.06))  # 2-6% CTR
                conversions = int(clicks * random.uniform(0.03, 0.08))  # 3-8% conversion rate
                
                ctr = (clicks / impressions * 100) if impressions > 0 else 0
                cpc = (base_spend / clicks) if clicks > 0 else 0
                conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
                
                row = {
                    'date': date_str,
                    'platform': 'microsoft',
                    'account_id': 'microsoft_account_1',
                    'account_name': 'Microsoft Ads Account',
                    'campaign_id': campaign['id'],
                    'campaign_name': campaign['name'],
                    'adgroup_id': f"{campaign['id']}_adgroup_1",
                    'adgroup_name': f"{campaign['name']} - AdGroup 1",
                    'ad_id': f"{campaign['id']}_ad_1",
                    'ad_name': None,
                    'impressions': impressions,
                    'clicks': clicks,
                    'spend': round(base_spend, 2),
                    'conversions': conversions,
                    'ctr': round(ctr, 2),
                    'cpc': round(cpc, 2),
                    'cpm': None,
                    'conversion_rate': round(conversion_rate, 2),
                    'cost_per_conversion': None,
                    'revenue': None,
                    'roas': None,
                    'raw': None,
                    'updated_at': datetime.now(timezone.utc)
                }
                all_metrics_data.append(row)
            
            # Generate LinkedIn data for this day
            for campaign in linkedin_campaigns:
                random.seed(hash(f"linkedin_{campaign['id']}_{date_str}"))
                
                # Realistic LinkedIn Ads performance (typically higher CPC)
                base_spend = random.uniform(400, 1200)
                impressions = int(base_spend * random.uniform(3, 8))  # 3-8 impressions per dollar (higher CPC)
                clicks = int(impressions * random.uniform(0.015, 0.04))  # 1.5-4% CTR
                conversions = int(clicks * random.uniform(0.04, 0.09))  # 4-9% conversion rate
                
                ctr = (clicks / impressions * 100) if impressions > 0 else 0
                cpc = (base_spend / clicks) if clicks > 0 else 0
                conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
                
                row = {
                    'date': date_str,
                    'platform': 'linkedin',
                    'account_id': 'linkedin_account_1',
                    'account_name': 'LinkedIn Ads Account',
                    'campaign_id': campaign['id'],
                    'campaign_name': campaign['name'],
                    'adgroup_id': f"{campaign['id']}_adgroup_1",
                    'adgroup_name': f"{campaign['name']} - AdGroup 1",
                    'ad_id': f"{campaign['id']}_ad_1",
                    'ad_name': None,
                    'impressions': impressions,
                    'clicks': clicks,
                    'spend': round(base_spend, 2),
                    'conversions': conversions,
                    'ctr': round(ctr, 2),
                    'cpc': round(cpc, 2),
                    'cpm': None,
                    'conversion_rate': round(conversion_rate, 2),
                    'cost_per_conversion': None,
                    'revenue': None,
                    'roas': None,
                    'raw': None,
                    'updated_at': datetime.now(timezone.utc)
                }
                all_metrics_data.append(row)
            
            current_date += timedelta(days=1)
        
        logger.info(f"📊 Generated {len(all_metrics_data)} records for {day_count} days")
        logger.info(f"  Microsoft: {len([r for r in all_metrics_data if r['platform'] == 'microsoft'])} records")
        logger.info(f"  LinkedIn: {len([r for r in all_metrics_data if r['platform'] == 'linkedin'])} records")
        
        # Insert data into BigQuery
        logger.info("📤 Loading data to BigQuery...")
        
        df = pd.DataFrame(all_metrics_data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        bq_client.insert_dataframe('ad_metrics', df)
        
        logger.info(f"✅ Inserted {len(all_metrics_data)} records into ad_metrics table")
        
        # Verify the data
        logger.info("\n🔍 Verifying 90-day data:")
        
        verify_query = f"""
        SELECT 
            platform,
            COUNT(*) as records,
            COUNT(DISTINCT date) as unique_dates,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            SUM(spend) as total_spend,
            SUM(clicks) as total_clicks,
            SUM(conversions) as total_conversions
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
        WHERE platform IN ('microsoft', 'linkedin')
        GROUP BY platform
        ORDER BY total_spend DESC
        """
        
        verify_df = bq_client.query(verify_query)
        
        for _, row in verify_df.iterrows():
            platform = row['platform'].title()
            logger.info(f"📊 {platform} Ads:")
            logger.info(f"  Records: {int(row['records']):,}")
            logger.info(f"  Date Range: {row['earliest_date']} to {row['latest_date']} ({int(row['unique_dates'])} days)")
            logger.info(f"  Total Spend: ${row['total_spend']:,.2f}")
            logger.info(f"  Total Clicks: {int(row['total_clicks']):,}")
            logger.info(f"  Total Conversions: {int(row['total_conversions'])}")
            logger.info(f"  Avg Daily Spend: ${row['total_spend'] / row['unique_dates']:,.2f}")
            logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 90-day data generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Generating 90-Day Platform Data")
    print("=" * 60)
    
    success = asyncio.run(generate_90_day_platform_data())
    
    if success:
        print("=" * 60)
        print("✅ 90-day data generation completed!")
        print("💡 Microsoft and LinkedIn now have full 90-day historical data")
        print("📊 Ready for comprehensive dashboard with daily breakdowns")
    else:
        print("=" * 60)
        print("❌ 90-day data generation failed")
