# Google Ads API Setup Guide

This guide will help you configure Google Ads API credentials to connect to the Sourcegraph account.

## Prerequisites

1. **Google Ads Account Access**: You need admin access to the Sourcegraph Google Ads account
2. **Google Cloud Console Access**: You need access to create API credentials
3. **Google Ads API Access**: The account must have Google Ads API access approved

## Step 1: Google Cloud Console Setup

### 1.1 Create/Select Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project for Sourcegraph ads
3. Note the **Project ID**

### 1.2 Enable Google Ads API
1. Go to **APIs & Services** > **Library**
2. Search for "Google Ads API"
3. Click **Enable**

### 1.3 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client IDs**
3. Configure OAuth consent screen if prompted:
   - Application type: **Internal** (if using Google Workspace) or **External**
   - App name: "Sourcegraph Ads Manager"
   - Support email: your email
   - Scopes: Add `https://www.googleapis.com/auth/adwords`
4. Create OAuth client:
   - Application type: **Desktop application** or **Web application**
   - Name: "Sourcegraph Ads API Client"
   - Authorized redirect URIs: `http://localhost:8080` (for web application)
5. Download the credentials JSON or copy:
   - **Client ID** (looks like: `123456789-abcdef.apps.googleusercontent.com`)
   - **Client Secret** (looks like: `ABCDEF-1234567890abcdef`)

## Step 2: Google Ads API Developer Token

### 2.1 Get Developer Token
1. Log into [Google Ads](https://ads.google.com/)
2. Go to **Tools & Settings** > **Setup** > **API Center**
3. Apply for **Basic Access** or **Standard Access**
4. Copy your **Developer Token** (looks like: `1234567890ABCDEfghij`)

### 2.2 Link Manager Account (if using MCC)
If managing multiple accounts through an MCC:
1. Note your **Manager Customer ID** (10 digits, no dashes)
2. Ensure the target Sourcegraph account is linked to this MCC

## Step 3: Update Environment File

Add these credentials to your `.env` file:

```bash
# Google Ads API Configuration
GOOGLE_ADS_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=ABCDEF-1234567890abcdef
GOOGLE_ADS_DEVELOPER_TOKEN=1234567890ABCDEfghij
GOOGLE_ADS_CUSTOMER_ID=9639990200
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_mcc_id_if_applicable
```

## Step 4: Generate Refresh Token

Once your credentials are configured, run:

```bash
poetry run python generate_refresh_token.py
```

This will:
1. Open your browser for Google OAuth
2. Redirect to a localhost URL with an authorization code
3. Exchange the code for a refresh token
4. Display the token to add to your `.env` file

## Step 5: Test Connection

After adding the refresh token, test the connection:

```bash
poetry run python check_account_access.py
```

## Troubleshooting

### Common Issues

**"CLIENT_ID looks too short"**
- Ensure you copied the full Client ID (usually 70+ characters)
- Format: `123456789-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com`

**"AUTHENTICATION_ERROR"**
- Check that all credentials are correct
- Ensure the OAuth consent screen is configured
- Verify the developer token is active

**"Account not accessible"**
- Verify the Customer ID is correct (10 digits, no dashes)
- Ensure your OAuth account has access to the Google Ads account
- Check if using MCC, that LOGIN_CUSTOMER_ID is set

**"QUOTA_EXCEEDED"**
- Google Ads API has rate limits
- Wait and retry
- Consider applying for Standard Access for higher limits

### Customer IDs for Reference
- **Sourcegraph**: `9639990200`
- **SingleStore**: `4174586061`

## Security Notes

- Keep all credentials secure
- Never commit the `.env` file to version control
- Use environment-specific credentials for development vs production
- Consider using Google Cloud Secret Manager for production deployments

## Next Steps

Once connected, you can:
1. Pull campaign data and metrics
2. Run performance reports
3. Set up automated optimizations
4. Configure alerting for account changes
