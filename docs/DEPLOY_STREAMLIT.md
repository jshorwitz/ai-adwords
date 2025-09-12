# Deploy the Streamlit Dashboard

This repo includes a Streamlit app at `src/dashboard/app.py` that visualizes Google Ads performance from BigQuery.

Follow these steps to deploy on Streamlit Community Cloud (recommended):

## 1) Prerequisites
- A Google Cloud project with BigQuery enabled
- A BigQuery dataset (default name `google_ads_data`) and the tables referenced by the app
- A service account with BigQuery Data Viewer (read) on the dataset
- The service account JSON credentials

## 2) Push this repo to GitHub
Streamlit Cloud deploys from GitHub. Push your fork of this repository.

## 3) Configure Streamlit app
1. Go to https://share.streamlit.io → New app
2. Select the GitHub repo and branch
3. Set the main file path to: `src/dashboard/app.py`
4. Advanced settings:
   - Python version: 3.11
   - Dependencies: use `requirements.txt`

## 4) Add Secrets
In the app settings → Secrets, paste values in TOML format. Recommended layout:

```toml
[bigquery]
GOOGLE_CLOUD_PROJECT = "your-gcp-project-id"
BIGQUERY_DATASET_ID = "google_ads_data"

[gcp_service_account]
# Paste the full JSON of your service account here, for example:
# type = "service_account"
# project_id = "your-gcp-project-id"
# private_key_id = "..."
# private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
# client_email = "streamlit@your-gcp-project-id.iam.gserviceaccount.com"
# client_id = "..."
# token_uri = "https://oauth2.googleapis.com/token"
```

The app auto-detects this structure and builds credentials in-memory. No files are written.

Alternatively, for local dev you can set env vars in `.env`:

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
BIGQUERY_DATASET_ID=google_ads_data
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service_account.json
```

## 5) Deploy
Click Deploy. First build takes a few minutes while Streamlit installs dependencies. When running, the app reads from BigQuery and renders the dashboard.

## 6) Troubleshooting
- "GOOGLE_CLOUD_PROJECT required": ensure it is set in Secrets ([bigquery] section) or env
- Authentication errors: ensure the `[gcp_service_account]` keys are correct and that the service account has BigQuery read access on your dataset
- Empty dashboard: verify tables exist and contain rows for the selected date range

## Local run (optional)
Install Poetry and then run:

```bash
make install
make dashboard
```

This starts the app on http://localhost:8501. Ensure your `.env` has the same GCP settings as above.
