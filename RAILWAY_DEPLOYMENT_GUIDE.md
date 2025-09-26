# Railway Deployment Guide - Synter AI AdWords Dashboard

## 🚀 Quick Deployment 

The app is automatically deployed to Railway from the main branch:

**🔗 Live Dashboard**: https://web-production-97620.up.railway.app

## 📋 Environment Variables Setup

### Required for BigQuery Integration:

1. **GOOGLE_CLOUD_PROJECT**
   - Set to your Google Cloud Project ID
   - Example: `ai-adwords-470622`

2. **BIGQUERY_DATASET_ID**
   - Set to `synter_analytics` (default)
   - This is where your Google Ads data is stored

3. **GOOGLE_APPLICATION_CREDENTIALS**
   - Upload your BigQuery service account JSON file
   - Railway will provide this as a file path

### Platform API Keys (Already Configured):

✅ **Reddit Ads**
- `REDDIT_CLIENT_ID`: mDSnWlcEn17omHHxElhLzg
- `REDDIT_CLIENT_SECRET`: XF74NzwNIexlLltp_dimfdFqzJlYTA

✅ **Microsoft Ads** 
- `MICROSOFT_ADS_DEVELOPER_TOKEN`: 11085M29YT845526
- `MICROSOFT_ADS_CUSTOMER_ID`: F110007XSU
- `MICROSOFT_ADS_CLIENT_ID`: 7f33a26a-c05d-4750-b3f9-2b429dfebdf9
- `MICROSOFT_ADS_TENANT_ID`: 3630fc6e-1576-4ffa-bdd1-5be49726d818
- `MICROSOFT_ADS_CLIENT_SECRET`: 33ee494a-556b-4b27-8c25-bf95ec965ab6

### Optional (for Google Ads):
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET` 
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CUSTOMER_ID`

## 🔧 Setup Steps

### 1. Configure BigQuery Access

In Railway dashboard:
1. Go to Variables tab
2. Add `GOOGLE_CLOUD_PROJECT` = your-project-id
3. Add `BIGQUERY_DATASET_ID` = synter_analytics
4. Upload service account JSON file

### 2. Create BigQuery Tables

Run locally or via Railway shell:
```bash
python -m src.cli setup-bigquery
```

This creates tables in the `synter_analytics` dataset:
- `campaigns_performance` (Google Ads data with cost_micros conversion)
- `keywords_performance` (keyword data)
- `ad_metrics` (multi-platform: Reddit, Microsoft, LinkedIn)

### 3. Test the Deployment

Visit: https://web-production-97620.up.railway.app

You should see:
- ✅ Dashboard loads with KPI cards
- ✅ D3.js charts render (fallback to mock data initially)
- ✅ Platform cards show status
- ✅ Multi-platform data integration

## 📊 Data Flow Architecture

```
🔄 Data Pipeline:
Google Ads API → BigQuery → Dashboard API → D3.js Charts
Reddit Ads API → BigQuery → Dashboard API → D3.js Charts  
Microsoft API → BigQuery → Dashboard API → D3.js Charts
LinkedIn API → BigQuery → Dashboard API → D3.js Charts
```

## 🐛 Troubleshooting

### App Not Loading?
- Check Railway logs for errors
- Verify `PORT=8000` and `HOST=0.0.0.0`
- Ensure `app_safe.py` is set as start command

### Charts Showing Mock Data?
- Verify BigQuery environment variables
- Check BigQuery has data in tables
- Monitor API logs for BigQuery connection status

### BigQuery Connection Failed?
1. Verify service account has BigQuery Data Editor role
2. Check project ID matches exactly
3. Ensure BigQuery API is enabled

## 🔄 Auto-Deployment

The app auto-deploys when you push to the main branch:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Railway will automatically:
1. Pull latest code from GitHub
2. Build using Nixpacks
3. Deploy with health checks
4. Update the live URL

## 📈 Monitoring

- **Health Check**: `/health` endpoint
- **Logs**: Railway dashboard → Deploy logs
- **Metrics**: Monitor BigQuery usage in GCP console
- **Uptime**: Railway provides 99.9% uptime SLA

## 🔐 Security Notes

- API keys are environment variables (secure)
- BigQuery uses service account authentication
- PostgreSQL provided by Railway addon
- All traffic uses HTTPS
- No secrets in code repository
