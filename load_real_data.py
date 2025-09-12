#!/usr/bin/env python3
"""Load real Sourcegraph data from cached/stored results."""

import pandas as pd
import os
from src.ads.bigquery_client import create_bigquery_client_from_env

def load_cached_sourcegraph_data():
    """Load real Sourcegraph data from any cached/stored sources."""
    
    print("🔍 LOADING REAL SOURCEGRAPH DATA")
    print("=" * 50)
    
    # Try to find any real data files that may have been cached
    cache_files = [
        "sourcegraph_campaigns.csv",
        "sourcegraph_keywords.csv", 
        "campaign_data.json",
        "real_data_cache.json"
    ]
    
    data_found = False
    
    for filename in cache_files:
        if os.path.exists(filename):
            print(f"✅ Found cached data: {filename}")
            data_found = True
            
            if filename.endswith('.csv'):
                df = pd.read_csv(filename)
                print(f"   📊 {len(df)} rows, columns: {list(df.columns)}")
                
                if len(df) > 0:
                    # Display sample data
                    print("\n📋 Sample data:")
                    if 'campaign_name' in df.columns:
                        campaigns = df['campaign_name'].value_counts().head(5)
                        for name, count in campaigns.items():
                            print(f"   • {name}: {count} records")
                    
                    if 'impressions' in df.columns and 'clicks' in df.columns:
                        total_impressions = df['impressions'].sum()
                        total_clicks = df['clicks'].sum()
                        print(f"\n📈 Totals: {total_impressions:,} impressions, {total_clicks:,} clicks")
                        
    # Try loading from BigQuery if available
    print("\n🗄️ Checking BigQuery for real data...")
    try:
        bq_client = create_bigquery_client_from_env()
        if bq_client:
            # Query for any existing real data
            query = """
                SELECT 
                    customer_id,
                    COUNT(*) as record_count,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    SUM(impressions) as total_impressions,
                    SUM(clicks) as total_clicks
                FROM `ai-adwords-470622.google_ads_data.campaigns_performance`
                WHERE customer_id = '9639990200'
                GROUP BY customer_id
            """
            
            df = bq_client.query(query).to_dataframe()
            
            if not df.empty:
                print("✅ Found real data in BigQuery!")
                for _, row in df.iterrows():
                    print(f"   📊 Customer {row['customer_id']}: {row['record_count']} records")
                    print(f"   📅 Date range: {row['earliest_date']} to {row['latest_date']}")
                    print(f"   📈 {row['total_impressions']:,} impressions, {row['total_clicks']:,} clicks")
                data_found = True
            else:
                print("   ⚠️ No real data found in BigQuery")
                
    except Exception as e:
        print(f"   ❌ BigQuery error: {e}")
        
    if not data_found:
        print("\n❌ NO REAL DATA FOUND")
        print("The system is likely using mock/demo data due to API connection issues.")
        print("\nTo get real data:")
        print("1. Fix GRPC transport issues")
        print("2. Run: poetry run python get_sourcegraph_data.py")
        print("3. Or manually export data from Google Ads interface")
        
        return False
    else:
        print(f"\n✅ REAL DATA AVAILABLE")
        print("The dashboard should be able to display actual Sourcegraph performance data.")
        return True

if __name__ == "__main__":
    load_cached_sourcegraph_data()
