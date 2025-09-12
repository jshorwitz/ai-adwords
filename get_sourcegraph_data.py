#!/usr/bin/env python3
"""Quick script to fetch and display Sourcegraph campaign data."""

from src.ads.reporting import ReportingManager
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("🚀 Fetching Sourcegraph campaign data...")
    
    # Initialize reporting for Sourcegraph account
    reporting = ReportingManager('9639990200')
    
    # Get last 30 days of campaign data
    df = reporting.get_campaign_performance()
    
    if not df.empty:
        print(f"✅ Found {len(df)} rows of data")
        print(f"📅 Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"📈 Active campaigns: {df['campaign_name'].nunique()}")
        
        # Convert cost from micros to dollars
        df['cost_dollars'] = df['cost_micros'] / 1_000_000
        df['average_cpc_dollars'] = df['average_cpc'] / 1_000_000
        
        # Summary stats
        total_impressions = df['impressions'].sum()
        total_clicks = df['clicks'].sum() 
        total_cost = df['cost_dollars'].sum()
        total_conversions = df['conversions'].sum()
        
        print(f"\n📊 Campaign Performance Summary:")
        print(f"   Impressions: {total_impressions:,}")
        print(f"   Clicks: {total_clicks:,}")
        print(f"   Cost: ${total_cost:,.2f}")
        print(f"   Conversions: {total_conversions:.2f}")
        print(f"   CTR: {(total_clicks/total_impressions)*100:.2f}%")
        print(f"   Avg CPC: ${(total_cost/total_clicks):.2f}")
        print(f"   Conversion Rate: {(total_conversions/total_clicks)*100:.2f}%")
        
        print(f"\n🎯 Top Performing Campaigns:")
        campaign_summary = df.groupby('campaign_name').agg({
            'impressions': 'sum',
            'clicks': 'sum', 
            'cost_dollars': 'sum',
            'conversions': 'sum'
        }).round(2).sort_values('clicks', ascending=False).head(5)
        print(campaign_summary)
        
        # Save for dashboard
        df.to_csv('/tmp/sourcegraph_data.csv', index=False)
        print(f"\n💾 Data saved to /tmp/sourcegraph_data.csv")
        
        return df
        
    else:
        print("❌ No campaign data found")
        return None

if __name__ == "__main__":
    main()
