# Railway Deployment Guide - BigQuery Configuration

## Current Deployment Status
✅ **App Deployed:** https://web-production-97620.up.railway.app  
⚠️ **BigQuery:** Showing mock data (credentials need fixing)

## Issue: Service Account Configuration

Railway deployments typically don't use file paths for credentials. Instead, you need to set the **entire JSON content** as an environment variable.

## Steps to Fix BigQuery Connection

### Option 1: Environment Variable (Recommended)

1. **Copy your service-account.json content**
2. **Go to Railway Dashboard:** https://railway.app/dashboard
3. **Select your project:** `ai-adwords`
4. **Go to Variables tab**
5. **Remove:** `GOOGLE_APPLICATION_CREDENTIALS=service-account.json`
6. **Add new variable:** `GOOGLE_APPLICATION_CREDENTIALS` with the **full JSON content** as the value

### Option 2: Using Railway CLI

```bash
# Set the entire JSON content as an environment variable
railway variables set GOOGLE_APPLICATION_CREDENTIALS="$(cat service-account.json)"
```

### Option 3: Base64 Encoded (Alternative)

```bash
# Encode the JSON and set as variable
railway variables set GOOGLE_APPLICATION_CREDENTIALS_BASE64="$(base64 -i service-account.json)"
```

## Test Deployment After Fix

After updating the credentials, test these endpoints:

1. **Health Check:** https://web-production-97620.up.railway.app/health
2. **BigQuery Test:** https://web-production-97620.up.railway.app/debug/bigquery-test  
3. **Dashboard Data:** https://web-production-97620.up.railway.app/dashboard/demo/kpis
4. **Main Dashboard:** https://web-production-97620.up.railway.app/dashboard

## Expected Results After Fix

### BigQuery Test Endpoint Should Show:
```json
{
  "status": "success",
  "bigquery_available": true,
  "project": "ai-adwords-470622",
  "dataset": "synter_analytics",
  "kpi_summary": {
    "total_spend": 715720.62,
    "total_conversions": 14347,
    "total_clicks": 219448
  },
  "platforms": ["Google Ads", "Microsoft Ads", "LinkedIn Ads"]
}
```

### Dashboard KPIs Should Show Real Data:
```json
{
  "total_spend": 715720.62,
  "total_clicks": 219448,
  "total_conversions": 14347,
  "platforms": 3
}
```

## Current Railway Configuration

Your Railway deployment is configured with:
- ✅ **Project:** `ai-adwords-470622`
- ✅ **Dataset:** `synter_analytics`  
- ✅ **Microsoft API:** `11085M29YT845526`
- ⚠️ **Service Account:** Needs JSON content as environment variable

## Alternative: Railway Database Variables

If you prefer to keep credentials secure, you can also use Railway's built-in secret management:

1. **Railway Dashboard** → **Variables** → **Raw Editor**
2. **Paste the JSON content** directly into a secure variable
3. **Reference it** in your application code

## Verification Commands

Once fixed, these should return real data:

```bash
# Test BigQuery connection
curl "https://web-production-97620.up.railway.app/debug/bigquery-test"

# Test real platform data  
curl "https://web-production-97620.up.railway.app/debug/platform-data-real"

# Test dashboard KPIs
curl "https://web-production-97620.up.railway.app/dashboard/demo/kpis"
```

## Expected Platform Data

After the fix, your dashboard should show:
- **Google Ads:** $368,296.90 spend (real historical data)
- **Microsoft Ads:** $300,738.77 spend (90-day mock data)
- **LinkedIn Ads:** $46,684.95 spend (90-day mock data)

Total: **$715,720.62** across all platforms with 14,347 conversions.
