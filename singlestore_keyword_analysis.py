#!/usr/bin/env python3
"""Comprehensive keyword performance analysis for SingleStore account."""

import pandas as pd
import json
from datetime import datetime
from src.ads.keywords import list_keywords

def analyze_keyword_performance():
    """Perform detailed keyword performance analysis for SingleStore."""
    print('🔍 SINGLESTORE KEYWORD PERFORMANCE ANALYSIS')
    print('=' * 60)
    
    # Pull keyword data for SingleStore
    keywords = list_keywords('4174586061', limit=100)
    
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
    
    # SingleStore-specific recommendations
    print(f'\n💡 SINGLESTORE OPTIMIZATION RECOMMENDATIONS:')
    
    if not low_ctr.empty:
        print(f'   1. Review ad copy for {len(low_ctr)} low CTR keywords')
        print(f'      - Focus on database performance benefits')
        print(f'      - Highlight real-time analytics capabilities')
    
    if not high_cpc.empty:
        print(f'   2. Optimize bidding for {len(high_cpc)} high CPC keywords')
        print(f'      - Consider database-specific long-tail keywords')
        print(f'      - Target developer personas more precisely')
    
    if not zero_clicks.empty:
        print(f'   3. Investigate {len(zero_clicks)} keywords getting impressions but no clicks')
        print(f'      - Ensure ads highlight SingleStore\'s unique advantages')
        print(f'      - Consider technical vs business-focused messaging')
    
    # Database-specific insights
    db_keywords = df[df['keyword'].str.contains('database|db|sql|analytics|real.*time', case=False, na=False)]
    if not db_keywords.empty:
        print(f'   4. Database-focused keywords performing {"well" if db_keywords["ctr"].mean() > df["ctr"].mean() else "below average"}')
        print(f'      - Average CTR for DB keywords: {db_keywords["ctr"].mean():.2f}% vs overall {df["ctr"].mean():.2f}%')
    
    # Budget optimization
    total_waste = low_ctr['cost'].sum() if not low_ctr.empty else 0
    if total_waste > 100:
        print(f'   5. Potential monthly savings: ${total_waste:.2f} by optimizing low CTR keywords')
    
    # Save analysis results
    analysis_data = {
        'analysis_date': datetime.now().isoformat(),
        'account': 'SingleStore',
        'customer_id': '4174586061',
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
    with open('/tmp/singlestore_keyword_analysis.json', 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    df.to_csv('/tmp/singlestore_keyword_detailed.csv', index=False)
    
    print(f'\n💾 SingleStore analysis saved to:')
    print(f'   /tmp/singlestore_keyword_analysis.json')
    print(f'   /tmp/singlestore_keyword_detailed.csv')
    
    return analysis_data

if __name__ == "__main__":
    analyze_keyword_performance()
