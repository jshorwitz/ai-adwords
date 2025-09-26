# Google Cloud Data Transfer Service Setup for Google Ads

## Overview
The Google Cloud Data Transfer Service automatically transfers Google Ads data to BigQuery on a scheduled basis, providing a more reliable and managed solution than custom API calls.

## Current Project Details
- **Project ID:** `ai-adwords-470622`
- **Dataset:** `google_ads_data` (will be renamed to `synter_analytics`)
- **Location:** US

## Step-by-Step Activation Process

### 1. Access Google Cloud Console
Navigate to: https://console.cloud.google.com/bigquery/transfers

### 2. Enable Data Transfer API
If not already enabled:
- Go to: https://console.cloud.google.com/apis/library/bigquerydatatransfer.googleapis.com
- Click "Enable"

### 3. Create Google Ads Transfer
1. In BigQuery Data Transfers, click **"Create Transfer"**
2. Select **"Google Ads"** as the data source
3. Configure the transfer:

#### Transfer Configuration
```
Transfer Name: Google Ads to BigQuery Transfer
Data Source: Google Ads
Destination Type: BigQuery dataset
Project: ai-adwords-470622
Dataset: google_ads_data (or synter_analytics)
Location: US
```

#### Google Ads Configuration
```
Customer ID: 9639990200 (Sourcegraph account)
Refresh Window Days: 1
```

#### Tables to Transfer
Select the following tables:
- ✅ `p_Campaign_9639990200` (Campaign performance)
- ✅ `p_Keyword_9639990200` (Keyword performance)  
- ✅ `p_Ad_9639990200` (Ad performance)
- ✅ `p_SearchQueryStats_9639990200` (Search query performance)

#### Schedule Configuration
```
Repeat Frequency: Daily
Time: 02:00 UTC (after Google Ads data is finalized)
Start Date: Today
```

### 4. Authentication
1. Click **"Authorize"** to connect your Google Ads account
2. Grant necessary permissions:
   - View Google Ads data
   - Write to BigQuery

### 5. Advanced Options
```
Write Preference: Write to table (WRITE_TRUNCATE daily)
Data Location: US
Notification Settings: Enable for failures
```

## Expected BigQuery Tables

After activation, these tables will be created automatically:

### Campaign Performance (`p_Campaign_9639990200`)
- `date` - Report date
- `customer_id` - Google Ads customer ID  
- `campaign_id` - Campaign ID
- `campaign_name` - Campaign name
- `impressions` - Ad impressions
- `clicks` - Ad clicks
- `cost_micros` - Cost in micros (divide by 1M for USD)
- `conversions` - Conversion count

### Keyword Performance (`p_Keyword_9639990200`)
- All campaign fields plus:
- `ad_group_id` - Ad group ID
- `criterion_id` - Keyword criterion ID  
- `keyword` - Keyword text
- `match_type` - Keyword match type
- `quality_score` - Keyword quality score

### Search Query Performance (`p_SearchQueryStats_9639990200`)
- Campaign and keyword fields plus:
- `search_term` - Actual search query
- `search_term_match_type` - How keyword matched search

## Data Refresh Schedule
- **Daily at 02:00 UTC** - Transfers previous day's data
- **Refresh Window:** 1 day (can be increased if needed)
- **Backfill:** Available for historical data (up to 90 days)

## Verification Commands

After setup, verify the transfer with these commands:

```bash
# Check transfer status
bq ls -j --max_results=10 --project_id=ai-adwords-470622

# Query campaign data
bq query --project_id=ai-adwords-470622 --use_legacy_sql=false '
SELECT 
  date,
  campaign_name,
  impressions,
  clicks,
  cost_micros/1000000 as cost_usd,
  conversions
FROM `ai-adwords-470622.google_ads_data.p_Campaign_9639990200`
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY date DESC
LIMIT 10'
```

## Integration with Current System

Once the Data Transfer Service is active, update the ETL pipeline to use the managed tables:

```python
# Update BigQuery queries to use new table names
GOOGLE_ADS_TABLES = {
    'campaigns': 'p_Campaign_9639990200',
    'keywords': 'p_Keyword_9639990200', 
    'ads': 'p_Ad_9639990200',
    'search_queries': 'p_SearchQueryStats_9639990200'
}
```

## Monitoring & Alerts

Set up monitoring for the transfer:
1. **Transfer History:** Check in BigQuery Data Transfers console
2. **Email Notifications:** Configure for transfer failures
3. **Data Freshness:** Monitor last successful run time

## Cost Considerations
- **Data Transfer Service:** Free for Google Ads data
- **BigQuery Storage:** ~$0.02 per GB per month
- **BigQuery Queries:** $5 per TB processed

## Benefits Over Custom API
- ✅ **Managed Service:** No API rate limits or authentication issues
- ✅ **Reliable:** Google manages the data pipeline  
- ✅ **Scheduled:** Automatic daily updates
- ✅ **Complete Data:** Access to all Google Ads reporting dimensions
- ✅ **Historical Backfill:** Easy to load historical data

## Next Steps
1. Activate the transfer in Google Cloud Console
2. Wait 24 hours for first data load
3. Verify data in BigQuery
4. Update application queries to use new table structure
5. Test dashboard with live Google Ads data

## Troubleshooting
- **Transfer Fails:** Check Google Ads account permissions
- **No Data:** Verify customer ID and date ranges
- **Authentication Issues:** Re-authorize the connection
- **Schema Changes:** Check for Google Ads API updates
