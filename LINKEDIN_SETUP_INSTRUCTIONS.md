# 🔗 LinkedIn Ads Setup Instructions

## 📋 LinkedIn Developer App Configuration

Your LinkedIn Marketing API credentials:
- **Client ID**: `[PROVIDED_SEPARATELY]`
- **Client Secret**: `[PROVIDED_SEPARATELY]`

## 🔧 Step 1: Configure LinkedIn Developer App

1. **Go to LinkedIn Developer Console**: https://www.linkedin.com/developers/apps
2. **Select your LinkedIn app** (or create a new one)
3. **Go to Auth tab**
4. **Add Authorized Redirect URLs**:
   ```
   https://web-production-97620.up.railway.app/auth/linkedin/callback
   http://localhost:8000/auth/linkedin/callback
   ```

5. **Verify Scopes** (Products tab):
   - ✅ **Marketing Developer Platform** 
   - Required scopes: `r_ads`, `r_ads_reporting`, `r_organization_social`

## 🚀 Step 2: Set Railway Environment Variables

In your Railway dashboard (Variables tab), add:

```bash
LINKEDIN_CLIENT_ID=[your_linkedin_client_id]
LINKEDIN_CLIENT_SECRET=[your_linkedin_client_secret]
LINKEDIN_REDIRECT_URI=https://web-production-97620.up.railway.app/auth/linkedin/callback
MOCK_LINKEDIN=false
```

## 🔗 Step 3: Test LinkedIn Connection

Once deployed, test the LinkedIn integration:

1. **Visit Dashboard**: https://web-production-97620.up.railway.app/dashboard
2. **Click "Connect Account"** on LinkedIn Ads card
3. **Complete OAuth flow** on LinkedIn
4. **Return to dashboard** - should show "Active" status

## 📊 Step 4: Enable LinkedIn Data Sync

Once connected, sync LinkedIn Ads data to BigQuery:

```bash
# Test API connection
python -m src.cli test-platform-apis

# Sync LinkedIn data (dry run first)
python -m src.cli sync-multi-platform --platform=linkedin --days-back=7 --dry-run

# Real sync to BigQuery
python -m src.cli sync-multi-platform --platform=linkedin --days-back=30
```

## 🎯 Expected Results

After setup, you'll see:
- ✅ **LinkedIn platform card** shows "Active" status instead of "Mock Mode"
- ✅ **Real LinkedIn Ads data** in dashboard charts and KPIs
- ✅ **BigQuery synter_analytics.ad_metrics** table populated with LinkedIn data
- ✅ **Cross-platform analysis** including LinkedIn performance

## 🐛 Troubleshooting

### OAuth Flow Issues:
- Verify redirect URI exactly matches in LinkedIn Developer App
- Check that Marketing Developer Platform product is approved
- Ensure app has proper permissions

### API Connection Issues:
- Verify environment variables are set in Railway
- Check that access token hasn't expired
- Review Railway deployment logs for errors

### BigQuery Issues:
- Ensure `ad_metrics` table exists in `synter_analytics` dataset
- Verify BigQuery API permissions for service account
- Check that data is being written (may take up to 2 hours for scheduling)

## 🔄 Automated ETL Schedule

Once configured, LinkedIn data will automatically sync:
- **LinkedIn Ads Ingestor Agent**: Every day at 3 AM and 3 PM
- **Multi-Platform Ingestor**: Every 2 hours (includes LinkedIn)

Your LinkedIn Ads data will flow continuously into BigQuery for unified cross-platform analysis! 🚀
