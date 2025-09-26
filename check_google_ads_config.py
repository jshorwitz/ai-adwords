#!/usr/bin/env python3
"""Check Google Ads credentials configuration."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_google_ads_config():
    """Check Google Ads credential configuration."""
    print("🔍 GOOGLE ADS CREDENTIALS CHECK")
    print("=" * 50)
    
    google_ads_vars = {
        'GOOGLE_ADS_CLIENT_ID': 'OAuth Client ID',
        'GOOGLE_ADS_CLIENT_SECRET': 'OAuth Client Secret', 
        'GOOGLE_ADS_DEVELOPER_TOKEN': 'Developer Token',
        'GOOGLE_ADS_CUSTOMER_ID': 'Customer ID',
        'GOOGLE_ADS_LOGIN_CUSTOMER_ID': 'MCC Customer ID',
        'GOOGLE_ADS_REFRESH_TOKEN': 'Refresh Token'
    }
    
    configured_count = 0
    missing_vars = []
    
    for var, description in google_ads_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}")
            print(f"   {description}: Set (length: {len(value)} chars)")
            if var == 'GOOGLE_ADS_CLIENT_ID':
                print(f"   Preview: {value[:20]}...")
            elif var == 'GOOGLE_ADS_CUSTOMER_ID':
                print(f"   Value: {value}")
            configured_count += 1
        else:
            print(f"❌ {var}")
            print(f"   {description}: NOT SET")
            missing_vars.append(var)
    
    print(f"\n📊 CONFIGURATION SUMMARY")
    print("=" * 30)
    print(f"✅ Configured: {configured_count}/6 variables")
    print(f"❌ Missing: {len(missing_vars)}/6 variables")
    
    if missing_vars:
        print(f"\n⚠️ Missing Variables:")
        for var in missing_vars:
            print(f"   - {var}")
    
    if configured_count == 6:
        print(f"\n🎉 Google Ads fully configured!")
        test_google_ads_client()
    elif configured_count > 0:
        print(f"\n⚠️ Partially configured - need remaining {len(missing_vars)} variables")
    else:
        print(f"\n❌ Google Ads not configured - need all 6 variables")
        print(f"\n📋 Setup Options:")
        print(f"1. Follow: google_ads_setup_guide.md")
        print(f"2. Run: python generate_refresh_token.py")
        print(f"3. Use existing credentials if available")
    
    return configured_count

def test_google_ads_client():
    """Test Google Ads client if credentials are available."""
    print(f"\n🧪 TESTING GOOGLE ADS CLIENT")
    print("=" * 40)
    
    try:
        from src.ads.ads_client import create_client_from_env
        
        print("📡 Testing Google Ads client creation...")
        client = create_client_from_env()
        
        if client:
            print("✅ Google Ads client created successfully")
            
            # Test basic functionality
            from src.ads.accounts import list_accessible_clients
            print("📊 Testing account access...")
            
            customers = list_accessible_clients(client)
            print(f"✅ Found {len(customers)} accessible customers")
            
            for customer in customers[:3]:  # Show first 3
                print(f"   🎯 {customer.descriptive_name} (ID: {customer.id})")
        else:
            print("❌ Failed to create Google Ads client")
            
    except Exception as e:
        print(f"❌ Google Ads client test failed: {e}")
        print(f"   This might be due to missing credentials or API access")

def check_bigquery_google_data():
    """Check if there's existing Google Ads data in BigQuery."""
    print(f"\n🗄️ CHECKING EXISTING GOOGLE ADS DATA")
    print("=" * 40)
    
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            print("❌ BigQuery service not available")
            return
        
        # Check campaigns_performance table for existing Google data
        query = f"""
        SELECT 
          COUNT(*) as total_records,
          MIN(date) as earliest_date,
          MAX(date) as latest_date,
          SUM(COALESCE(cost, cost_micros/1000000)) as total_spend,
          COUNT(DISTINCT customer_id) as customers
        FROM `{bq_service.bq_client.project_id}.{bq_service.bq_client.dataset_id}.campaigns_performance`
        """
        
        df = bq_service.bq_client.query(query)
        
        if not df.empty and df.iloc[0]['total_records'] > 0:
            row = df.iloc[0]
            records = int(row['total_records'])
            spend = float(row['total_spend']) if row['total_spend'] else 0
            customers = int(row['customers'])
            
            print(f"✅ Found existing Google Ads data:")
            print(f"   📊 Records: {records:,}")
            print(f"   💰 Total spend: ${spend:,.2f}")
            print(f"   👥 Customers: {customers}")
            print(f"   📅 Date range: {row['earliest_date']} to {row['latest_date']}")
            print(f"\n💡 This suggests Google Ads was previously configured")
            print(f"   You may need to restore previous credentials")
        else:
            print("⚠️ No existing Google Ads data found")
            print("   Either never configured or data was cleared")
            
    except Exception as e:
        print(f"❌ Error checking BigQuery: {e}")

if __name__ == "__main__":
    configured = check_google_ads_config()
    check_bigquery_google_data()
    
    print(f"\n📋 NEXT STEPS")
    print("=" * 20)
    
    if configured == 0:
        print("🔧 Need to set up Google Ads credentials:")
        print("   1. Follow google_ads_setup_guide.md")
        print("   2. Add 6 environment variables")
        print("   3. Google Ads data will flow to BigQuery")
    elif configured < 6:
        print("⚠️ Complete the Google Ads configuration:")
        print("   Add remaining environment variables")
    else:
        print("🎉 Google Ads should be working!")
        print("   Check logs if data isn't flowing")
