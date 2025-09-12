#!/usr/bin/env python3
"""Comprehensive keyword performance analysis for Sourcegraph account."""

import pandas as pd
import json
from datetime import datetime
from src.ads.keywords import list_keywords

def analyze_keyword_performance():
    """Perform detailed keyword performance analysis."""
    print('🔍 SOURCEGRAPH KEYWORD PERFORMANCE ANALYSIS')
    print('=' * 60)
    
    # Pull keyword data
    keywords = list_keywords('9639990200', limit=100)
    
    if not keywords:
        print('❌ No keyword data available')
        return
    
    df = pd.DataFrame(keywords)
    
    # Add calculated metrics
    df['cost'] = df.get('cost_micros', df.get('cost', 0)) / 1_000_000 if 'cost_micros' in df.columns else df.get('cost', 0)
    df['ctr'] = (df['clicks'] / df['impressions'] * 100).round(2)
    df['cost_per_click'] = (df['cost'] / df['clicks']).round(2)
    df['cost_per_click'] = df['cost_per_click'].replace([float('inf'), -float('inf')], 0)
    
    print(f'📊 KEYWORD PERFORMANCE OVERVIEW')
    print(f'   Total Keywords Analyzed: {len(df)}')
    print(f'   Total Impressions: {df["impressions"].sum():,}')
    print(f'   Total Clicks: {df["clicks"].sum():,}')
    print(f'   Total Cost: ${df["cost"].sum():,.2f}')
    print(f'   Average CTR: {df["ctr"].mean():.2f}%')
    print(f'   Average CPC: ${df["cost_per_click"].mean():.2f}')
    
    # Top performers by different metrics
    print(f'\n🚀 TOP PERFORMING KEYWORDS:')
    
    # By impressions
    print(f'\n   By Impressions (Top 5):')
    top_impressions = df.nlargest(5, 'impressions')
    for idx, row in top_impressions.iterrows():
        print(f'     • {row["keyword"][:30]:30} | {row["impressions"]:6,} imp | CTR: {row["ctr"]:5.2f}%')
    
    # By clicks  
    print(f'\n   By Clicks (Top 5):')
    top_clicks = df.nlargest(5, 'clicks')
    for idx, row in top_clicks.iterrows():
        print(f'     • {row["keyword"][:30]:30} | {row["clicks"]:5,} clicks | CPC: ${row["cost_per_click"]:5.2f}')
    
    # By CTR (min 100 impressions)
    high_volume = df[df['impressions'] >= 100]
    if not high_volume.empty:
        print(f'\n   By CTR (100+ impressions, Top 5):')
        top_ctr = high_volume.nlargest(5, 'ctr')
        for idx, row in top_ctr.iterrows():
            print(f'     • {row["keyword"][:30]:30} | CTR: {row["ctr"]:5.2f}% | {row["impressions"]:5,} imp')
    
    # Performance issues analysis
    print(f'\n🚨 PERFORMANCE ISSUES IDENTIFIED:')
    
    # Low CTR keywords (with significant impressions)
    low_ctr = df[(df['impressions'] >= 100) & (df['ctr'] < 2.0)]
    if not low_ctr.empty:
        print(f'\n   ⚠️  LOW CTR KEYWORDS ({len(low_ctr)} keywords with <2% CTR, 100+ impressions):')
        for idx, row in low_ctr.head(5).iterrows():
            print(f'     • {row["keyword"][:30]:30} | CTR: {row["ctr"]:5.2f}% | {row["impressions"]:5,} imp')
        if len(low_ctr) > 5:
            print(f'     ... and {len(low_ctr) - 5} more')
    
    # High CPC keywords
    high_cpc = df[(df['cost_per_click'] > 8.0) & (df['clicks'] > 0)]
    if not high_cpc.empty:
        print(f'\n   ⚠️  HIGH CPC KEYWORDS ({len(high_cpc)} keywords with >$8 CPC):')
        for idx, row in high_cpc.head(5).iterrows():
            print(f'     • {row["keyword"][:30]:30} | CPC: ${row["cost_per_click"]:6.2f} | {row["clicks"]:4} clicks')
    
    # Zero click keywords with impressions
    zero_clicks = df[(df['impressions'] >= 50) & (df['clicks'] == 0)]
    if not zero_clicks.empty:
        print(f'\n   ⚠️  ZERO CLICK KEYWORDS ({len(zero_clicks)} keywords with 0 clicks, 50+ impressions):')
        for idx, row in zero_clicks.head(5).iterrows():
            print(f'     • {row["keyword"][:30]:30} | {row["impressions"]:5,} impressions')
    
    # Keyword analysis by match type
    print(f'\n🎯 MATCH TYPE ANALYSIS:')
    if 'match_type' in df.columns:
        match_analysis = df.groupby('match_type').agg({
            'impressions': 'sum',
            'clicks': 'sum', 
            'cost': 'sum',
            'ctr': 'mean'
        }).round(2)
        
        for match_type, stats in match_analysis.iterrows():
            print(f'   {match_type:15} | {stats["impressions"]:7,} imp | {stats["clicks"]:5,} clicks | ${stats["cost"]:8,.2f} | CTR: {stats["ctr"]:.2f}%')
    
    # Recommendations
    print(f'\n💡 OPTIMIZATION RECOMMENDATIONS:')
    
    if not low_ctr.empty:
        print(f'   1. Review ad copy for {len(low_ctr)} low CTR keywords')
        print(f'      - Consider improving headline relevance')
        print(f'      - Test emotional triggers and benefits')
    
    if not high_cpc.empty:
        print(f'   2. Optimize bidding for {len(high_cpc)} high CPC keywords')
        print(f'      - Review competitor landscape')
        print(f'      - Consider long-tail alternatives')
    
    if not zero_clicks.empty:
        print(f'   3. Investigate {len(zero_clicks)} keywords getting impressions but no clicks')
        print(f'      - Check ad relevance and landing page alignment')
        print(f'      - Consider negative keywords to improve targeting')
    
    # Budget optimization
    total_waste = low_ctr['cost'].sum() if not low_ctr.empty else 0
    if total_waste > 100:
        print(f'   4. Potential monthly savings: ${total_waste:.2f} by optimizing low CTR keywords')
    
    # Save analysis results
    analysis_data = {
        'analysis_date': datetime.now().isoformat(),
        'summary': {
            'total_keywords': len(df),
            'total_impressions': int(df['impressions'].sum()),
            'total_clicks': int(df['clicks'].sum()),
            'total_cost': float(df['cost'].sum()),
            'average_ctr': float(df['ctr'].mean()),
            'average_cpc': float(df['cost_per_click'].mean())
        },
        'issues': {
            'low_ctr_keywords': len(low_ctr),
            'high_cpc_keywords': len(high_cpc), 
            'zero_click_keywords': len(zero_clicks)
        },
        'top_performers': {
            'by_impressions': top_impressions[['keyword', 'impressions', 'ctr']].to_dict('records'),
            'by_clicks': top_clicks[['keyword', 'clicks', 'cost_per_click']].to_dict('records')
        }
    }
    
    # Save files
    with open('/tmp/sourcegraph_keyword_analysis.json', 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    df.to_csv('/tmp/sourcegraph_keyword_detailed.csv', index=False)
    
    print(f'\n💾 Analysis saved to:')
    print(f'   /tmp/sourcegraph_keyword_analysis.json')
    print(f'   /tmp/sourcegraph_keyword_detailed.csv')
    
    return analysis_data

if __name__ == "__main__":
    analyze_keyword_performance()
