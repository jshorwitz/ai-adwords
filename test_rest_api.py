#!/usr/bin/env python3
"""Test REST API connection to Google Ads."""

import os
from src.ads.rest_client import create_rest_client_from_env

def main():
    """Test REST API connection."""
    print("🔍 TESTING REST API CONNECTION")
    print("=" * 50)
    
    client = create_rest_client_from_env()
    if not client:
        print("❌ Failed to create REST client")
        return
    
    # Test accessible customers
    print("📋 Testing accessible customers...")
    customers = client.list_accessible_customers()
    print(f"   Found {len(customers)} accessible customers: {customers}")
    
    # Test Sourcegraph account
    sourcegraph_id = "9639990200"
    print(f"\n🎯 Testing Sourcegraph account ({sourcegraph_id})...")
    
    customer_info = client.get_customer_info(sourcegraph_id)
    if customer_info:
        print(f"   ✅ Customer info retrieved: {customer_info.get('customer', {}).get('descriptive_name', 'Unknown')}")
    else:
        print("   ❌ No customer info found")
    
    campaigns = client.get_campaigns(sourcegraph_id, limit=10)
    print(f"   📊 Found {len(campaigns)} campaigns")
    
    for i, campaign in enumerate(campaigns[:3], 1):
        camp = campaign.get('campaign', {})
        metrics = campaign.get('metrics', {})
        print(f"      {i}. {camp.get('name', 'Unknown')}: {metrics.get('impressions', 0):,} impressions")

if __name__ == "__main__":
    main()
