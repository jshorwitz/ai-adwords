# Conversion Validation Setup

## Required Environment Variables

Add these to your `.env` file to enable conversion validation across platforms:

### Google Analytics 4
```bash
# GA4 Property ID (numeric, e.g., "123456789")
GA4_PROPERTY_ID=your_ga4_property_id

# Optional: Path to GA4 service account JSON file
# If not provided, will use default Google Cloud credentials
GA4_CREDENTIALS_PATH=/path/to/ga4-service-account.json
```

### PostHog  
```bash
# PostHog API Key (starts with 'phc_')
POSTHOG_API_KEY=your_posthog_api_key

# Optional: PostHog instance host (defaults to app.posthog.com)
POSTHOG_HOST=https://app.posthog.com
```

## Setup Instructions

### 1. Google Analytics 4 Setup

1. **Enable GA4 Reporting API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable the "Google Analytics Reporting API"

2. **Create Service Account (Recommended):**
   - Create a new service account 
   - Download the JSON key file
   - Add service account email to your GA4 property with "Viewer" permissions

3. **Get GA4 Property ID:**
   - In GA4 → Admin → Property Settings
   - Copy the Property ID (numeric value)

### 2. PostHog Setup

1. **Get API Key:**
   - Go to PostHog → Project Settings → API Keys
   - Copy your Project API Key (starts with `phc_`)

2. **Self-Hosted PostHog:**
   - If using self-hosted, set `POSTHOG_HOST` to your instance URL

### 3. Attribution Setup

**Ensure consistent UTM parameters:**
- Google Ads should use `utm_source=google` and `utm_medium=cpc`
- Enable auto-tagging in Google Ads (adds `gclid` parameter)

**Configure conversion events:**
- GA4: Set up conversion events (purchase, sign_up, etc.)
- PostHog: Track the same events with consistent naming

## Usage

1. **Select Account:** Choose a specific Google Ads account in the dashboard
2. **Run Validation:** Click "Run Conversion Validation" button
3. **Review Results:** Compare conversions across all three platforms

## Expected Results

The validation will show:
- **Total conversions** from each platform
- **Daily comparison charts** showing trends
- **Variance analysis** highlighting discrepancies
- **Attribution insights** to help optimize tracking

## Troubleshooting

### Common Issues:
- **"No GA4 data found"**: Check property ID and credentials
- **"PostHog API error"**: Verify API key and host URL  
- **"Attribution mismatch"**: Review UTM parameter consistency
- **"Service account error"**: Ensure GA4 permissions are granted

### Debug Mode:
Set `DEBUG=1` in environment to see detailed logging.
