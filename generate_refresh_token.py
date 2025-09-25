#!/usr/bin/env python3
"""
Generate Google Ads API refresh token through OAuth 2.0 flow.

This script will:
1. Open a web browser for Google OAuth consent
2. Exchange the authorization code for a refresh token
3. Display the refresh token to add to your .env file

Prerequisites:
- GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET in your .env file
- Google Ads API access enabled in Google Cloud Console
- OAuth consent screen configured
"""

import os
import webbrowser
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_refresh_token():
    """Generate Google Ads API refresh token through OAuth flow."""
    
    # Get credentials from environment
    client_id = os.getenv('GOOGLE_ADS_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing GOOGLE_ADS_CLIENT_ID or GOOGLE_ADS_CLIENT_SECRET in .env file")
        print("Please add these credentials first.")
        return None
    
    print("🔑 GOOGLE ADS API - REFRESH TOKEN GENERATOR")
    print("=" * 50)
    print(f"Using Client ID: {client_id[:20]}...")
    
    # Step 1: Build authorization URL
    scope = 'https://www.googleapis.com/auth/adwords'
    redirect_uri = 'http://localhost:8080'  # This should match your OAuth config
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    print(f"\n📱 Opening browser for Google OAuth...")
    print(f"If browser doesn't open automatically, visit:")
    print(f"{auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    print(f"\n⚡ After authorizing, you'll be redirected to:")
    print(f"{redirect_uri}/?code=AUTHORIZATION_CODE&scope=...")
    print(f"\n📋 Copy the 'code' parameter value from the URL and paste it below:")
    
    # Get authorization code from user
    auth_code = input("Authorization Code: ").strip()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return None
    
    print(f"\n🔄 Exchanging authorization code for refresh token...")
    
    # Step 2: Exchange authorization code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        
        token_info = response.json()
        refresh_token = token_info.get('refresh_token')
        
        if refresh_token:
            print("✅ SUCCESS! Refresh token generated:")
            print("=" * 60)
            print(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")
            print("=" * 60)
            print("\n📝 Next steps:")
            print("1. Add the above line to your .env file")
            print("2. Run 'python check_account_access.py' to test the connection")
            
            return refresh_token
        else:
            print("❌ No refresh token in response")
            print("Response:", token_info)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Token exchange failed: {e}")
        if hasattr(e, 'response') and e.response:
            print("Response:", e.response.text)
        return None

def validate_oauth_setup():
    """Validate OAuth 2.0 setup requirements."""
    
    print("🔍 VALIDATING OAUTH SETUP")
    print("=" * 40)
    
    client_id = os.getenv('GOOGLE_ADS_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET')
    developer_token = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')
    
    issues = []
    
    if not client_id:
        issues.append("Missing GOOGLE_ADS_CLIENT_ID")
    elif len(client_id) < 50:
        issues.append("GOOGLE_ADS_CLIENT_ID looks too short")
    
    if not client_secret:
        issues.append("Missing GOOGLE_ADS_CLIENT_SECRET")
    elif len(client_secret) < 20:
        issues.append("GOOGLE_ADS_CLIENT_SECRET looks too short")
        
    if not developer_token:
        issues.append("Missing GOOGLE_ADS_DEVELOPER_TOKEN")
    elif len(developer_token) < 15:
        issues.append("GOOGLE_ADS_DEVELOPER_TOKEN looks too short")
    
    if issues:
        print("❌ Setup Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 How to fix:")
        print("   1. Go to Google Cloud Console")
        print("   2. Enable Google Ads API")
        print("   3. Create OAuth 2.0 credentials")
        print("   4. Get developer token from Google Ads interface")
        print("   5. Add credentials to .env file")
        return False
    else:
        print("✅ OAuth credentials present")
        print(f"   Client ID: {client_id[:20]}...")
        print(f"   Client Secret: {client_secret[:10]}...")
        print(f"   Developer Token: {developer_token[:10]}...")
        return True

if __name__ == "__main__":
    print("🚀 GOOGLE ADS API REFRESH TOKEN GENERATOR")
    print("=" * 60)
    
    if not validate_oauth_setup():
        print("\n❌ Please fix the setup issues above before continuing.")
        exit(1)
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("   • Make sure your OAuth consent screen is configured")
    print("   • Add http://localhost:8080 as a redirect URI")
    print("   • This will open your default web browser")
    print("   • You may need to verify your identity with Google")
    
    confirm = input("\nReady to proceed? (y/N): ").lower().strip()
    if confirm != 'y':
        print("Cancelled.")
        exit(0)
    
    refresh_token = get_refresh_token()
    
    if refresh_token:
        print("\n🎉 Token generation completed successfully!")
    else:
        print("\n❌ Token generation failed. Please check the error messages above.")
