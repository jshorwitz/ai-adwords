#!/usr/bin/env python3
"""Analyze Sourcegraph Google Ads account performance."""

from src.ads.reporting import ReportingManager
from src.ads.keywords import list_keywords
import pandas as pd

def main():
    print('🔍 Analyzing Sourcegraph Google Ads Account (9639990200)')
    print('=' * 60)

    # Get campaign performance data
    print('\n📊 Campaign Performance Analysis (Last 30 days)')
    reporting = ReportingManager('9639990200')
    df = reporting.get_campaign_performance()

    if not df.empty:
        # Convert cost from micros to dollars
        df['cost_dollars'] = df['cost_micros'] / 1_000_000
        df['cpc_dollars'] = df['average_cpc'] / 1_000_000
        
        # Campaign summary
        campaign_summary = df.groupby(['campaign_id', 'campaign_name']).agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'cost_dollars': 'sum',
            'conversions': 'sum',
            'ctr': 'mean',
            'cpc_dollars': 'mean'
        }).round(2)
        
        # Calculate additional metrics
        campaign_summary['conversion_rate'] = (campaign_summary['conversions'] / campaign_summary['clicks'] * 100).round(2)
        campaign_summary['cost_per_conversion'] = (campaign_summary['cost_dollars'] / campaign_summary['conversions']).round(2)
        
        # Sort by spend
        campaign_summary = campaign_summary.sort_values('cost_dollars', ascending=False)
        
        print(f'Found {len(campaign_summary)} active campaigns with data')
        print('\nTop 10 Campaigns by Spend:')
        top_campaigns = campaign_summary.head(10)[['impressions', 'clicks', 'cost_dollars', 'conversions', 'ctr', 'conversion_rate', 'cost_per_conversion']]
        print(top_campaigns.to_string())
        
        # Performance insights
        total_impressions = int(campaign_summary['impressions'].sum())
        total_clicks = int(campaign_summary['clicks'].sum())
        total_cost = campaign_summary['cost_dollars'].sum()
        total_conversions = campaign_summary['conversions'].sum()
        
        avg_ctr = (total_clicks / total_impressions * 100)
        avg_conversion_rate = (total_conversions / total_clicks * 100)
        avg_cpc = (total_cost / total_clicks)
        avg_cost_per_conversion = (total_cost / total_conversions)
        
        print(f'\n📈 Account Summary:')
        print(f'   Total Impressions: {total_impressions:,}')
        print(f'   Total Clicks: {total_clicks:,}')
        print(f'   Total Spend: ${total_cost:.2f}')
        print(f'   Total Conversions: {total_conversions:.2f}')
        print(f'   Account CTR: {avg_ctr:.2f}%')
        print(f'   Account Conv Rate: {avg_conversion_rate:.2f}%')
        print(f'   Account Avg CPC: ${avg_cpc:.2f}')
        print(f'   Account Cost/Conv: ${avg_cost_per_conversion:.2f}')
        
        # Performance flags
        print(f'\n🚨 Performance Flags:')
        poor_ctr = campaign_summary[campaign_summary['ctr'] < 1.0]
        poor_conv_rate = campaign_summary[campaign_summary['conversion_rate'] < 2.0]
        high_cpc = campaign_summary[campaign_summary['cpc_dollars'] > 5.0]
        high_cost_per_conv = campaign_summary[campaign_summary['cost_per_conversion'] > 200]
        
        if not poor_ctr.empty:
            print(f'   ⚠️ {len(poor_ctr)} campaigns with CTR < 1.0%')
            print(f'      Low CTR campaigns: {list(poor_ctr.index.get_level_values(1))}')
        if not poor_conv_rate.empty:
            print(f'   ⚠️ {len(poor_conv_rate)} campaigns with conversion rate < 2.0%')
            print(f'      Low conv rate campaigns: {list(poor_conv_rate.index.get_level_values(1))}')
        if not high_cpc.empty:
            print(f'   ⚠️ {len(high_cpc)} campaigns with CPC > $5.00')
            print(f'      High CPC campaigns: {list(high_cpc.index.get_level_values(1))}')
        if not high_cost_per_conv.empty:
            print(f'   ⚠️ {len(high_cost_per_conv)} campaigns with cost/conversion > $200')
        
        # Campaign type analysis
        print(f'\n🎯 Campaign Type Analysis:')
        campaign_names = campaign_summary.index.get_level_values(1).tolist()
        
        brand_campaigns = [name for name in campaign_names if 'Brand' in name]
        competitor_campaigns = [name for name in campaign_names if 'Competitor' in name]
        search_campaigns = [name for name in campaign_names if 'Search' in name]
        retargeting_campaigns = [name for name in campaign_names if 'retargeting' in name]
        pmax_campaigns = [name for name in campaign_names if 'Pmax' in name or 'Max' in name]
        
        print(f'   📛 Brand campaigns: {len(brand_campaigns)}')
        print(f'   🏆 Competitor campaigns: {len(competitor_campaigns)}')
        print(f'   🔍 Search campaigns: {len(search_campaigns)}')
        print(f'   🎯 Retargeting campaigns: {len(retargeting_campaigns)}')
        print(f'   🚀 Performance Max campaigns: {len(pmax_campaigns)}')
        
        # Save detailed data
        campaign_summary.to_csv('/tmp/sourcegraph_campaign_analysis.csv')
        print(f'\n💾 Detailed analysis saved to /tmp/sourcegraph_campaign_analysis.csv')
        
        return campaign_summary
        
    else:
        print('No campaign data found')
        return pd.DataFrame()

if __name__ == "__main__":
    main()
