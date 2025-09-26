# 🚀 Multi-Platform BigQuery Integration Guide

Connect **Reddit Ads**, **Microsoft Ads**, and **LinkedIn Ads** to Google BigQuery `synter_analytics` dataset for unified cross-platform advertising analysis.

## 📋 Overview

This guide sets up automated ETL pipelines that:
- Pull data from Reddit, Microsoft, and LinkedIn advertising APIs  
- Transform data to a unified schema
- Load into BigQuery `synter_analytics.ad_metrics` table
- Enable cross-platform analysis and reporting

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Reddit Ads    │    │ Microsoft Ads   │    │  LinkedIn Ads   │
│      API        │    │      API        │    │      API        │
└─────┬───────────┘    └─────┬───────────┘    └─────┬───────────┘
      │                      │                      │
      ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Multi-Platform ETL Pipeline                  │
│  • Data extraction & transformation                        │
│  • Unified schema mapping                                  │
│  • Error handling & retry logic                           │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           Google BigQuery: synter_analytics                 │
│                                                            │
│  📊 campaigns_performance (Google Ads)                     │
│  📊 keywords_performance (Google Keywords)                 │
│  📊 ad_metrics (Multi-platform unified)                    │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Dashboard & Analysis                     │
│  • Unified KPIs across all platforms                      │
│  • Cross-platform performance comparison                   │
│  • D3.js visualizations with live data                    │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Step 1: BigQuery Setup

### Create the unified ad_metrics table:

```bash
# Setup BigQuery tables (includes new ad_metrics table)
python -m src.cli setup-bigquery
```

This creates the `ad_metrics` table with unified schema:
```sql
CREATE TABLE synter_analytics.ad_metrics (
  date DATE,
  platform STRING,              -- 'reddit', 'microsoft', 'linkedin'
  account_id STRING,
  campaign_id STRING,
  impressions INT64,
  clicks INT64,
  spend FLOAT64,               -- Normalized to USD
  conversions FLOAT64,
  ctr FLOAT64,
  cpc FLOAT64,
  roas FLOAT64,
  raw JSON,                    -- Original API response
  updated_at TIMESTAMP
);
```

## 🔧 Step 2: Reddit Ads Integration

### API Credentials Setup:

1. **Create Reddit App**: https://www.reddit.com/prefs/apps
   - Choose "installed app" type
   - Note Client ID and Secret

2. **Environment Variables**:
```bash
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
MOCK_REDDIT=false                    # Enable real API calls
```

### Test Reddit Connection:
```bash
python -m src.cli test-platform-apis
```

### Manual Sync:
```bash
# Sync Reddit data for last 7 days
python -m src.cli sync-multi-platform --platform=reddit --days-back=7

# Dry run first to test
python -m src.cli sync-multi-platform --platform=reddit --days-back=7 --dry-run
```

## 🔧 Step 3: Microsoft Ads Integration

### API Credentials Setup:

1. **Microsoft Ads Developer Account**: https://developers.ads.microsoft.com/
   - Get Developer Token
   - Create Azure AD application

2. **Environment Variables**:
```bash
MICROSOFT_ADS_DEVELOPER_TOKEN=your_developer_token
MICROSOFT_ADS_CLIENT_ID=your_azure_app_client_id
MICROSOFT_ADS_CLIENT_SECRET=your_azure_app_client_secret
MICROSOFT_ADS_CUSTOMER_ID=your_customer_id
MICROSOFT_ADS_TENANT_ID=your_azure_tenant_id
MOCK_MICROSOFT=false                # Enable real API calls
```

### OAuth Setup:
```bash
# Visit Microsoft OAuth endpoint to get access token
https://web-production-97620.up.railway.app/auth/microsoft/connect
```

### Manual Sync:
```bash
# Sync Microsoft data for last 7 days  
python -m src.cli sync-multi-platform --platform=microsoft --days-back=7
```

## 🔧 Step 4: LinkedIn Ads Integration

### API Credentials Setup:

1. **LinkedIn Developer Application**: https://www.linkedin.com/developers/
   - Create app with Marketing Developer Platform access
   - Request advertiser API permissions

2. **Environment Variables**:
```bash
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token        # OAuth token
MOCK_LINKEDIN=false                           # Enable real API calls
```

### Manual Sync:
```bash
# Sync LinkedIn data for last 7 days
python -m src.cli sync-multi-platform --platform=linkedin --days-back=7
```

## 🔧 Step 5: Automated Scheduling

### Setup Automatic ETL Agents:

The system includes automated agents that run on schedules:

```python
# Multi-platform sync every 2 hours
MultiPlatformIngestorAgent: "0 */2 * * *"

# Individual platform syncs (staggered)
RedditAdsIngestorAgent:    "0 1,13 * * *"  # 1 AM, 1 PM
MicrosoftAdsIngestorAgent: "0 2,14 * * *"  # 2 AM, 2 PM  
LinkedInAdsIngestorAgent:  "0 3,15 * * *"  # 3 AM, 3 PM
```

### Manual Agent Execution:
```bash
# Sync all platforms
python -m src.cli sync-multi-platform --platform=all --days-back=1

# Test with dry run
python -m src.cli sync-multi-platform --platform=all --days-back=7 --dry-run
```

## 📊 Step 6: Dashboard Integration

The dashboard automatically displays unified data from all platforms:

### KPI Cards:
- **Total Spend**: Combined across Google, Reddit, Microsoft, LinkedIn
- **Impressions**: Unified impression volume
- **Conversions**: Cross-platform conversion tracking
- **ROAS**: Blended return on ad spend

### D3.js Charts:
- **Platform Spend Distribution**: Donut chart showing spend by platform
- **ROAS Comparison**: Bar chart comparing platform performance  
- **Multi-platform Time Series**: 30-day trends across all platforms

## 🔍 Step 7: Data Analysis & Queries

### Query Examples:

```sql
-- Cross-platform daily performance
SELECT 
  date,
  platform,
  SUM(spend) as spend,
  SUM(impressions) as impressions,
  SUM(conversions) as conversions,
  ROUND(SUM(conversions * 100) / SUM(spend), 2) as roas
FROM `synter_analytics.ad_metrics`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY date, platform
ORDER BY date DESC, spend DESC;

-- Platform performance comparison (last 30 days)
SELECT 
  platform,
  COUNT(DISTINCT date) as active_days,
  SUM(spend) as total_spend,
  SUM(impressions) as total_impressions, 
  SUM(conversions) as total_conversions,
  ROUND(AVG(ctr), 2) as avg_ctr,
  ROUND(SUM(conversions * 100) / SUM(spend), 2) as blended_roas
FROM `synter_analytics.ad_metrics`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY platform
ORDER BY total_spend DESC;

-- Best performing campaigns across platforms
SELECT 
  platform,
  campaign_name,
  SUM(spend) as spend,
  SUM(conversions) as conversions,
  ROUND(SUM(conversions * 100) / SUM(spend), 2) as roas,
  ROUND(AVG(ctr), 2) as avg_ctr
FROM `synter_analytics.ad_metrics`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND spend > 100  -- Minimum spend threshold
GROUP BY platform, campaign_name
HAVING conversions > 0
ORDER BY roas DESC
LIMIT 20;
```

## ⚡ Step 8: Monitoring & Alerts

### Health Checks:
```bash
# Test all platform connections
python -m src.cli test-platform-apis

# Check agent status
curl https://web-production-97620.up.railway.app/agents/health

# View recent ETL runs
curl https://web-production-97620.up.railway.app/agents/status
```

### ETL Monitoring:
- **Success Rate**: Track ETL job success/failure rates
- **Data Freshness**: Monitor when data was last updated
- **Error Alerting**: Slack/email notifications for failed syncs

## 🚨 Troubleshooting

### Common Issues:

**❌ "Platform not configured"**
```bash
# Check environment variables are set
echo $REDDIT_CLIENT_ID
echo $MICROSOFT_ADS_DEVELOPER_TOKEN  
echo $LINKEDIN_CLIENT_ID

# Verify mock mode is disabled
echo $MOCK_REDDIT      # Should be "false"
echo $MOCK_MICROSOFT   # Should be "false" 
echo $MOCK_LINKEDIN    # Should be "false"
```

**❌ "BigQuery permission denied"** 
```bash
# Verify service account has BigQuery Data Editor role
# Check GOOGLE_CLOUD_PROJECT and BIGQUERY_DATASET_ID are set
gcloud auth application-default login  # For local testing
```

**❌ "OAuth token expired"**
```bash
# Microsoft/LinkedIn tokens need periodic renewal
# Visit OAuth endpoints to refresh tokens:
# Microsoft: /auth/microsoft/connect  
# LinkedIn: Set up token refresh workflow
```

### Debug Mode:
```bash
# Run with detailed logging
LOG_LEVEL=debug python -m src.cli sync-multi-platform --platform=all --dry-run
```

## 🎯 Success Metrics

After setup, you should see:

✅ **BigQuery Tables**: Data flowing into `synter_analytics.ad_metrics`  
✅ **Dashboard**: All platform data visible in unified charts  
✅ **Cross-Platform KPIs**: Blended metrics across Reddit, Microsoft, LinkedIn  
✅ **Automated ETL**: Scheduled agents running every 2 hours  
✅ **Historical Analysis**: 30+ days of multi-platform data for trending  

## 📈 Next Steps

1. **Enhanced Attribution**: Cross-platform customer journey mapping
2. **Automated Optimization**: Budget reallocation based on cross-platform ROAS
3. **Advanced Analytics**: Cohort analysis and LTV calculation across platforms
4. **Real-time Alerts**: Performance threshold monitoring and automated responses

---

**🔥 You now have a complete multi-platform advertising data warehouse!** 

All Reddit, Microsoft, and LinkedIn advertising data flows into BigQuery `synter_analytics` for unified analysis and optimization across your entire advertising portfolio.
