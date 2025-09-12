#!/usr/bin/env python3
"""Pull keyword performance data for Sourcegraph account analysis."""

from src.ads.keywords import list_keywords
import json
import pandas as pd

def main():
    print('🔍 Pulling Sourcegraph keyword performance data...')
    keywords = list_keywords('9639990200', limit=50)
    print(f'✅ Found {len(keywords)} keywords')

    if keywords:
        # Sort by impressions and show top performers
        sorted_keywords = sorted(keywords, key=lambda x: x['impressions'], reverse=True)
        
        print('\n🚀 Top 10 Keywords by Impressions:')
        for i, kw in enumerate(sorted_keywords[:10], 1):
            ctr = (kw['clicks'] / kw['impressions'] * 100) if kw['impressions'] > 0 else 0
            cost = kw.get('cost', 0)
            print(f'{i:2}. {kw["keyword"]:30} | {kw["impressions"]:8,} imp | {kw["clicks"]:6,} clicks | ${cost:.2f} | CTR: {ctr:.2f}%')
        
        # Performance analysis
        total_impressions = sum(kw['impressions'] for kw in keywords)
        total_clicks = sum(kw['clicks'] for kw in keywords) 
        total_cost = sum(kw.get('cost', 0) for kw in keywords)
        
        print(f'\n📊 Keywords Performance Summary:')
        print(f'   Total Keywords: {len(keywords)}')
        print(f'   Total Impressions: {total_impressions:,}')
        print(f'   Total Clicks: {total_clicks:,}')
        print(f'   Total Cost: ${total_cost:.2f}')
        if total_impressions > 0:
            print(f'   Average CTR: {(total_clicks/total_impressions)*100:.2f}%')
        
        # Identify performance issues
        print(f'\n🚨 Performance Analysis:')
        low_ctr = [kw for kw in keywords if kw['impressions'] > 100 and (kw['clicks']/kw['impressions'])*100 < 1.0]
        high_cost = [kw for kw in keywords if kw.get('avg_cpc', 0) > 5.0]
        zero_clicks = [kw for kw in keywords if kw['impressions'] > 50 and kw['clicks'] == 0]
        
        if low_ctr:
            print(f'   ⚠️ {len(low_ctr)} keywords with CTR < 1.0% (100+ impressions)')
        if high_cost:
            print(f'   ⚠️ {len(high_cost)} keywords with CPC > $5.00')
        if zero_clicks:
            print(f'   ⚠️ {len(zero_clicks)} keywords with 0 clicks (50+ impressions)')
        
        # Save data for dashboard
        with open('/tmp/sourcegraph_keywords.json', 'w') as f:
            json.dump(keywords, f, indent=2)
        
        # Create CSV for analysis
        df = pd.DataFrame(keywords)
        if 'cost' not in df.columns:
            df['cost'] = df.get('cost_micros', 0) / 1_000_000
        df['ctr'] = (df['clicks'] / df['impressions'] * 100).round(2)
        df.to_csv('/tmp/sourcegraph_keywords.csv', index=False)
        
        print(f'\n💾 Keywords data saved:')
        print(f'   JSON: /tmp/sourcegraph_keywords.json')
        print(f'   CSV: /tmp/sourcegraph_keywords.csv')
        
        return df
    else:
        print('❌ No keyword data found')
        return None

if __name__ == "__main__":
    main()
