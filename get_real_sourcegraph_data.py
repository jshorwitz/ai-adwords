#!/usr/bin/env python3
"""
Direct data pull for Sourcegraph using OAuth and REST API to bypass GRPC issues.
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_oauth_credentials():
    """Create OAuth credentials from environment variables."""
    return Credentials(
        token=None,  # Will be refreshed
        refresh_token=os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        id_token=None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_ADS_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/adwords"]
    )

def make_ads_api_request(credentials, customer_id, query):
    """Make direct REST API request to Google Ads."""
    # Ensure token is fresh
    if not credentials.token or credentials.expired:
        credentials.refresh(Request())
    
    url = f"https://googleads.googleapis.com/v17/customers/{customer_id}:search"
    
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "developer-token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "login-customer-id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "7431593382"),
        "Content-Type": "application/json",
    }
    
    data = {
        "query": query,
        "page_size": 10000,
    }
    
    print(f"Making request to: {url}")
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    return response.json()

def get_sourcegraph_campaigns():
    """Get real Sourcegraph campaign data."""
    print("🚀 Fetching real Sourcegraph campaign data...")
    
    credentials = create_oauth_credentials()
    customer_id = "9639990200"
    
    # Campaign performance query
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.conversion_rate
        FROM campaign 
        WHERE segments.date DURING LAST_30_DAYS
        AND campaign.status = 'ENABLED'
        ORDER BY metrics.impressions DESC
    """
    
    try:
        result = make_ads_api_request(credentials, customer_id, query)
        
        if "results" in result and result["results"]:
            # Convert to DataFrame
            campaigns = []
            for row in result["results"]:
                campaign = row.get("campaign", {})
                metrics = row.get("metrics", {})
                segments = row.get("segments", {})
                budget = row.get("campaignBudget", {})
                
                campaigns.append({
                    "customer_id": customer_id,
                    "campaign_id": campaign.get("id", ""),
                    "campaign_name": campaign.get("name", ""),
                    "campaign_status": campaign.get("status", ""),
                    "channel_type": campaign.get("advertisingChannelType", ""),
                    "date": segments.get("date", ""),
                    "budget_micros": budget.get("amountMicros", 0),
                    "impressions": int(metrics.get("impressions", 0)),
                    "clicks": int(metrics.get("clicks", 0)),
                    "cost_micros": int(metrics.get("costMicros", 0)),
                    "conversions": float(metrics.get("conversions", 0)),
                    "ctr": float(metrics.get("ctr", 0)),
                    "average_cpc": int(metrics.get("averageCpc", 0)),
                    "conversion_rate": float(metrics.get("conversionRate", 0))
                })
            
            df = pd.DataFrame(campaigns)
            
            # Save to CSV
            df.to_csv("sourcegraph_real_campaigns.csv", index=False)
            
            print(f"✅ SUCCESS! Fetched {len(df)} campaign records")
            print(f"📅 Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"📊 Active campaigns: {df['campaign_name'].nunique()}")
            
            # Summary stats
            total_impressions = df['impressions'].sum()
            total_clicks = df['clicks'].sum()
            total_cost = df['cost_micros'].sum() / 1_000_000
            total_conversions = df['conversions'].sum()
            
            print(f"📈 Totals: {total_impressions:,} impressions, {total_clicks:,} clicks")
            print(f"💰 Total spend: ${total_cost:,.2f}")
            print(f"🎯 Total conversions: {total_conversions:,.1f}")
            
            if total_clicks > 0:
                overall_ctr = (total_clicks / total_impressions) * 100
                avg_cpc = total_cost / total_clicks
                conv_rate = (total_conversions / total_clicks) * 100
                print(f"📊 Overall CTR: {overall_ctr:.2f}%, Avg CPC: ${avg_cpc:.2f}, Conv Rate: {conv_rate:.2f}%")
            
            # Top campaigns
            print("\n🏆 Top 5 campaigns by impressions:")
            top_campaigns = df.groupby('campaign_name').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost_micros': 'sum',
                'conversions': 'sum'
            }).sort_values('impressions', ascending=False).head(5)
            
            for name, row in top_campaigns.iterrows():
                cost_dollars = row['cost_micros'] / 1_000_000
                print(f"   • {name}: {row['impressions']:,} imp, {row['clicks']:,} clicks, ${cost_dollars:,.0f}")
            
            return df
            
        else:
            print("❌ No campaign data found in API response")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error fetching campaign data: {e}")
        return pd.DataFrame()

def get_sourcegraph_keywords():
    """Get real Sourcegraph keyword data."""
    print("\n🔍 Fetching real Sourcegraph keyword data...")
    
    credentials = create_oauth_credentials()
    customer_id = "9639990200"
    
    # Keywords performance query
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc,
            metrics.quality_score
        FROM keyword_view 
        WHERE segments.date DURING LAST_30_DAYS
        AND ad_group_criterion.status = 'ENABLED'
        AND campaign.status = 'ENABLED'
        ORDER BY metrics.impressions DESC
        LIMIT 500
    """
    
    try:
        result = make_ads_api_request(credentials, customer_id, query)
        
        if "results" in result and result["results"]:
            # Convert to DataFrame
            keywords = []
            for row in result["results"]:
                campaign = row.get("campaign", {})
                ad_group = row.get("adGroup", {})
                criterion = row.get("adGroupCriterion", {})
                keyword = criterion.get("keyword", {})
                metrics = row.get("metrics", {})
                segments = row.get("segments", {})
                
                keywords.append({
                    "customer_id": customer_id,
                    "campaign_id": campaign.get("id", ""),
                    "campaign_name": campaign.get("name", ""),
                    "ad_group_id": ad_group.get("id", ""),
                    "ad_group_name": ad_group.get("name", ""),
                    "criterion_id": criterion.get("criterionId", ""),
                    "keyword_text": keyword.get("text", ""),
                    "match_type": keyword.get("matchType", ""),
                    "date": segments.get("date", ""),
                    "impressions": int(metrics.get("impressions", 0)),
                    "clicks": int(metrics.get("clicks", 0)),
                    "cost_micros": int(metrics.get("costMicros", 0)),
                    "conversions": float(metrics.get("conversions", 0)),
                    "ctr": float(metrics.get("ctr", 0)),
                    "average_cpc": int(metrics.get("averageCpc", 0)),
                    "quality_score": float(metrics.get("qualityScore", 0))
                })
            
            df = pd.DataFrame(keywords)
            
            # Save to CSV
            df.to_csv("sourcegraph_real_keywords.csv", index=False)
            
            print(f"✅ SUCCESS! Fetched {len(df)} keyword records")
            print(f"🔑 Unique keywords: {df['keyword_text'].nunique()}")
            
            # Top keywords
            print("\n🎯 Top 5 keywords by impressions:")
            top_keywords = df.groupby('keyword_text').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost_micros': 'sum',
                'conversions': 'sum'
            }).sort_values('impressions', ascending=False).head(5)
            
            for keyword, row in top_keywords.iterrows():
                cost_dollars = row['cost_micros'] / 1_000_000
                ctr = (row['clicks'] / row['impressions']) * 100 if row['impressions'] > 0 else 0
                print(f"   • '{keyword}': {row['impressions']:,} imp, {ctr:.1f}% CTR, ${cost_dollars:,.0f}")
            
            return df
            
        else:
            print("❌ No keyword data found in API response")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error fetching keyword data: {e}")
        return pd.DataFrame()

def main():
    """Main execution function."""
    print("🔍 SOURCEGRAPH REAL DATA EXTRACTION")
    print("=" * 50)
    
    # Check credentials
    required_vars = [
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CLIENT_ID", 
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_DEVELOPER_TOKEN"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return
    
    print("✅ All credentials found")
    
    # Get campaign data
    campaign_df = get_sourcegraph_campaigns()
    
    # Get keyword data
    keyword_df = get_sourcegraph_keywords()
    
    if not campaign_df.empty or not keyword_df.empty:
        print("\n🎉 DATA EXTRACTION COMPLETE!")
        print("Files created:")
        if not campaign_df.empty:
            print(f"   ✅ sourcegraph_real_campaigns.csv ({len(campaign_df)} records)")
        if not keyword_df.empty:
            print(f"   ✅ sourcegraph_real_keywords.csv ({len(keyword_df)} records)")
        print("\nThese files can now be used by the dashboard for real data display.")
    else:
        print("\n❌ No data extracted. Check API connection and permissions.")

if __name__ == "__main__":
    main()
