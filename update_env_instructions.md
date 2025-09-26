# Environment Configuration Update Instructions

## Required Changes to .env File

Please manually update your `.env` file with the following changes:

### 1. Update BigQuery Dataset Configuration

**Change this:**
```bash
BIGQUERY_DATASET_ID=google_ads_data
```

**To this:**
```bash
BIGQUERY_DATASET_ID=synter_analytics
```

### 2. Confirm Project ID (should already be correct)
```bash
BIGQUERY_PROJECT_ID=ai-adwords-470622
```

### 3. Add Microsoft Ads Configuration (if not already present)
```bash
MICROSOFT_ADS_DEVELOPER_TOKEN=11085M29YT845526
MOCK_MICROSOFT=true
```

### 4. Confirm Mock Settings for Development
```bash
MOCK_LINKEDIN=true
MOCK_REDDIT=true
```

## Complete .env Configuration Template

Here's what your BigQuery section should look like:

```bash
# =================================================================
# BIGQUERY CONFIGURATION
# =================================================================
BIGQUERY_PROJECT_ID=ai-adwords-470622
BIGQUERY_DATASET_ID=synter_analytics
BIGQUERY_CREDENTIALS_PATH=/path/to/your/service-account.json

# =================================================================
# MICROSOFT ADS API CONFIGURATION
# =================================================================
MICROSOFT_ADS_DEVELOPER_TOKEN=11085M29YT845526
MICROSOFT_ADS_CLIENT_ID=your_microsoft_ads_client_id
MICROSOFT_ADS_CLIENT_SECRET=your_microsoft_ads_client_secret
MICROSOFT_ADS_CUSTOMER_ID=your_microsoft_ads_customer_id
MOCK_MICROSOFT=true

# =================================================================
# MOCK DATA SETTINGS (for development)
# =================================================================
MOCK_LINKEDIN=true
MOCK_REDDIT=true
```

## After Making Changes

1. **Save the .env file**
2. **Restart any running services** (dashboard, API server, etc.)
3. **Test the configuration** with the verification script below

## Verification Script

Run this to verify the changes took effect:

```bash
source venv/bin/activate && python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Current BigQuery Dataset:', os.getenv('BIGQUERY_DATASET_ID'))
print('Current BigQuery Project:', os.getenv('BIGQUERY_PROJECT_ID'))
print('Microsoft Token:', 'SET' if os.getenv('MICROSOFT_ADS_DEVELOPER_TOKEN') else 'NOT SET')
"
```

## Expected Output
```
Current BigQuery Dataset: synter_analytics
Current BigQuery Project: ai-adwords-470622
Microsoft Token: SET
```

## Next Steps After Update

1. **Test BigQuery connection:**
   ```bash
   source venv/bin/activate && python test_bigquery_synter.py
   ```

2. **Verify data access:**
   ```bash
   source venv/bin/activate && python verify_all_platform_data.py
   ```

3. **Start your services** and confirm they're reading from synter_analytics

## Troubleshooting

If you encounter issues after the update:

1. **Check for typos** in the dataset name
2. **Verify the service account** has access to synter_analytics dataset
3. **Restart all services** completely
4. **Check logs** for any dataset-related errors

## Benefits of This Change

✅ **Unified Data Location:** All platform data in one dataset  
✅ **Google Ads Data Transfer:** Already configured for synter_analytics  
✅ **Consistent Naming:** Follows the original architecture plan  
✅ **Better Organization:** Clear separation from legacy google_ads_data
