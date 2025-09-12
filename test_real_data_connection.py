#!/usr/bin/env python3
"""Test real Google Ads API connection and BigQuery data pipeline."""

import os
import logging
from src.ads.ads_client import create_client_from_env
from src.ads.accounts import list_accessible_clients, get_customer_info
from src.ads.reporting import ReportingManager
from src.ads.etl_pipeline import GoogleAdsETLPipeline
from src.ads.bigquery_client import create_bigquery_client_from_env

logging.basicConfig(level=logging.INFO)

def test_google_ads_connection():
    """Test Google Ads API connection."""
    print('🔍 TESTING GOOGLE ADS API CONNECTION')
    print('=' * 60)
    
    try:
        # Test basic client creation
        service = create_client_from_env()
        print('✅ Google Ads client created successfully')
        
        # Test listing accessible customers
        customers = list_accessible_clients()
        print(f'✅ Found {len(customers)} accessible customer accounts:')
        
        for customer_id in customers:
            info = get_customer_info(customer_id)
            name = info.get('name', 'Unknown') if info else 'Unknown'
            print(f'   - {customer_id}: {name}')
            
        return customers
        
    except Exception as e:
        print(f'❌ Google Ads API connection failed: {e}')
        print('\n💡 To enable real data connection:')
        print('   1. Set up Google Ads API credentials in .env file:')
        print('      - GOOGLE_ADS_DEVELOPER_TOKEN')
        print('      - GOOGLE_ADS_REFRESH_TOKEN')
        print('      - GOOGLE_ADS_CLIENT_ID')
        print('      - GOOGLE_ADS_CLIENT_SECRET')
        print('      - GOOGLE_ADS_LOGIN_CUSTOMER_ID (MCC account)')
        print('   2. Remove ADS_USE_DEMO=1 and ADS_USE_MOCK=1')
        return []

def test_bigquery_connection():
    """Test BigQuery connection."""
    print('\n🗄️  TESTING BIGQUERY CONNECTION')
    print('=' * 60)
    
    try:
        bq_client = create_bigquery_client_from_env()
        print('✅ BigQuery client created successfully')
        print(f'   Project: {bq_client.project_id}')
        print(f'   Dataset: {bq_client.dataset_id}')
        
        # Test dataset creation
        bq_client.create_dataset()
        print('✅ Dataset verified/created')
        
        # Test table creation
        bq_client.create_campaigns_table()
        bq_client.create_keywords_table()
        print('✅ Tables verified/created')
        
        return True
        
    except Exception as e:
        print(f'❌ BigQuery connection failed: {e}')
        print('\n💡 To enable BigQuery connection:')
        print('   1. Set up BigQuery credentials:')
        print('      - GOOGLE_CLOUD_PROJECT (your GCP project ID)')
        print('      - BIGQUERY_DATASET_ID (optional, defaults to google_ads_data)')
        print('      - GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)')
        print('   2. Ensure BigQuery API is enabled in your GCP project')
        return False

def test_data_pull(customer_ids):
    """Test pulling real data from specific accounts."""
    print('\n📊 TESTING DATA PULLS')
    print('=' * 60)
    
    target_accounts = ['9639990200', '4174586061']  # Sourcegraph, SingleStore
    
    for customer_id in target_accounts:
        if customer_id in customer_ids:
            try:
                print(f'\n🔄 Testing data pull for {customer_id}...')
                
                # Test campaign data
                reporting = ReportingManager(customer_id)
                campaign_df = reporting.get_campaign_performance()
                
                if not campaign_df.empty:
                    print(f'✅ Campaign data: {len(campaign_df)} rows')
                    print(f'   Date range: {campaign_df["date"].min()} to {campaign_df["date"].max()}')
                    print(f'   Campaigns: {campaign_df["campaign_name"].nunique()}')
                    
                    # Show sample data
                    total_impressions = campaign_df['impressions'].sum()
                    total_clicks = campaign_df['clicks'].sum() 
                    total_cost = campaign_df['cost_micros'].sum() / 1_000_000
                    
                    print(f'   Impressions: {total_impressions:,}')
                    print(f'   Clicks: {total_clicks:,}')
                    print(f'   Cost: ${total_cost:,.2f}')
                else:
                    print('⚠️ No campaign data found')
                    
            except Exception as e:
                print(f'❌ Data pull failed for {customer_id}: {e}')
        else:
            print(f'⚠️ Account {customer_id} not found in accessible customers')

def run_etl_pipeline(customer_ids):
    """Run full ETL pipeline to BigQuery."""
    print('\n🔄 RUNNING ETL PIPELINE')
    print('=' * 60)
    
    target_accounts = [cid for cid in ['9639990200', '4174586061'] if cid in customer_ids]
    
    if not target_accounts:
        print('⚠️ No target accounts found in accessible customers')
        return
        
    try:
        pipeline = GoogleAdsETLPipeline()
        
        print(f'🚀 Starting ETL for accounts: {target_accounts}')
        pipeline.full_sync(target_accounts, days_back=30)
        
        print('✅ ETL pipeline completed successfully')
        print('   - Campaign performance data loaded to BigQuery')
        print('   - Keyword performance data loaded to BigQuery')
        print('   - Dashboard will now show real data')
        
    except Exception as e:
        print(f'❌ ETL pipeline failed: {e}')

def main():
    """Main test function."""
    print('🧪 GOOGLE ADS REAL DATA CONNECTION TEST')
    print('=' * 60)
    
    # Check if we're in demo mode
    if os.getenv("ADS_USE_DEMO") == "1" or os.getenv("ADS_USE_MOCK") == "1":
        print('⚠️ Currently in demo/mock mode')
        print('   Set ENABLE_REAL_API=1 and configure credentials to test real data')
        
        if os.getenv("ENABLE_REAL_API") != "1":
            print('\n💡 To test with real data, run:')
            print('   ENABLE_REAL_API=1 poetry run python test_real_data_connection.py')
            return
        else:
            # Temporarily disable demo mode for testing
            os.environ.pop("ADS_USE_DEMO", None)
            os.environ.pop("ADS_USE_MOCK", None)
    
    # Test Google Ads connection
    customers = test_google_ads_connection()
    
    # Test BigQuery connection
    bq_success = test_bigquery_connection()
    
    # If both connections work, test data pulls
    if customers and bq_success:
        test_data_pull(customers)
        
        # Ask user if they want to run full ETL
        print(f'\n🚀 READY TO SYNC REAL DATA')
        print('   This will pull real Google Ads data and load it into BigQuery')
        print('   The dashboard will then show actual performance data')
        
        if os.getenv("RUN_ETL") == "1":
            run_etl_pipeline(customers)
        else:
            print('\n💡 To run the full ETL pipeline:')
            print('   RUN_ETL=1 poetry run python test_real_data_connection.py')
    
    print('\n' + '=' * 60)
    print('✅ Connection test completed')

if __name__ == "__main__":
    main()
