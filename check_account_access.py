#!/usr/bin/env python3
"""Check specific account access and pull real data."""

import os
from src.ads.ads_client import create_client_from_env
from src.ads.accounts import list_accessible_clients, get_customer_info
from src.ads.reporting import ReportingManager

def check_account_access():
    """Check access to specific accounts."""
    print('🔍 CHECKING ACCOUNT ACCESS')
    print('=' * 50)
    
    # Force REST transport
    os.environ["GOOGLE_ADS_USE_GRPC"] = "false"
    
    try:
        service = create_client_from_env()
        print('✅ Google Ads client connected')
        
        # Get all accessible customers
        customers = list_accessible_clients()
        print(f'📋 Accessible customer accounts: {len(customers)}')
        
        for customer_id in customers:
            print(f'   - {customer_id}')
            
            # Try to get customer info
            try:
                info = get_customer_info(customer_id)
                name = info.get('name', 'Unknown') if info else 'Unknown'
                print(f'     Name: {name}')
                
                # Test data pull
                reporting = ReportingManager(customer_id)
                df = reporting.get_campaign_performance()
                
                if not df.empty:
                    print(f'     ✅ Data available: {len(df)} campaign records')
                    print(f'     Date range: {df["date"].min()} to {df["date"].max()}')
                    
                    # Show some metrics
                    total_impressions = df['impressions'].sum()
                    total_clicks = df['clicks'].sum()
                    total_cost = df['cost_micros'].sum() / 1_000_000
                    
                    print(f'     Impressions: {total_impressions:,}')
                    print(f'     Clicks: {total_clicks:,}') 
                    print(f'     Cost: ${total_cost:,.2f}')
                else:
                    print(f'     ⚠️ No campaign data found')
                    
            except Exception as e:
                print(f'     ❌ Error accessing {customer_id}: {e}')
            
            print()
            
        # Check specific target accounts
        target_accounts = {
            '9639990200': 'Sourcegraph',
            '4174586061': 'SingleStore'
        }
        
        print('🎯 TARGET ACCOUNTS STATUS:')
        for account_id, name in target_accounts.items():
            if account_id in customers:
                print(f'   ✅ {name} ({account_id}) - ACCESSIBLE')
            else:
                print(f'   ❌ {name} ({account_id}) - NOT ACCESSIBLE')
                print(f'      Account may not be linked to your MCC or have wrong permissions')
        
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        
        print('\n💡 Possible solutions:')
        print('   1. Check .env file has correct Google Ads API credentials')
        print('   2. Ensure accounts are linked to your MCC account')
        print('   3. Verify account permissions in Google Ads interface')
        print('   4. Check if account IDs are correct (10 digits, no dashes)')

if __name__ == "__main__":
    check_account_access()
