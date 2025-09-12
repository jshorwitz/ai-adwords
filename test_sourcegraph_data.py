#!/usr/bin/env python3
"""Test Sourcegraph data loading in dashboard."""

import sys
sys.path.append('src')
from dashboard.app import GoogleAdsDashboard

def main():
    print('🔍 Testing Sourcegraph data loading with cache fallback...')
    
    dashboard = GoogleAdsDashboard()
    df = dashboard.load_campaign_data(days_back=30, customer_id='9639990200')
    
    if not df.empty:
        print(f'✅ Successfully loaded {len(df)} rows of Sourcegraph data')
        print(f'📅 Date range: {df["date"].min()} to {df["date"].max()}')
        print(f'📊 Unique campaigns: {df["campaign_name"].nunique()}')
        
        # Summary stats
        total_impressions = int(df['impressions'].sum())
        total_clicks = int(df['clicks'].sum()) 
        total_cost = df['cost'].sum()
        total_conversions = df['conversions'].sum()
        
        print(f'\n📈 Performance Totals:')
        print(f'   Impressions: {total_impressions:,}')
        print(f'   Clicks: {total_clicks:,}')
        print(f'   Cost: ${total_cost:.2f}')
        print(f'   Conversions: {total_conversions:.1f}')
        
        print(f'\n🎯 Top Campaigns:')
        campaign_summary = df.groupby('campaign_name').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost': 'sum',
            'conversions': 'sum'
        }).round(2).sort_values('cost', ascending=False).head(5)
        
        for campaign_name, row in campaign_summary.iterrows():
            print(f'   📈 {campaign_name}:')
            print(f'      {int(row["impressions"]):,} impressions, {int(row["clicks"]):,} clicks, ${row["cost"]:.2f} spend')
        
        return True
    else:
        print('❌ No data loaded')
        return False

if __name__ == "__main__":
    main()
