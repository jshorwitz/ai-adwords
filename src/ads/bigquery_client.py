"""BigQuery client for Google Ads data warehouse."""

import logging
import os

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class BigQueryClient:
    """BigQuery client for storing Google Ads data."""

    def __init__(
        self,
        project_id: str,
        credentials_path: str | None = None,
        dataset_id: str = "google_ads_data",
    ):
        """Initialize BigQuery client.

        Args:
            project_id: Google Cloud Project ID
            credentials_path: Path to service account JSON file
            dataset_id: BigQuery dataset name
        """
        self.project_id = project_id
        self.dataset_id = dataset_id

        # Initialize credentials
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            self.client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS)
            self.client = bigquery.Client(project=project_id)

        self.dataset_ref = self.client.dataset(dataset_id)

    def create_dataset(self) -> None:
        """Create the dataset if it doesn't exist."""
        try:
            dataset = bigquery.Dataset(self.dataset_ref)
            dataset.location = "US"  # Change if you need different location
            dataset.description = "Google Ads reporting data warehouse"

            dataset = self.client.create_dataset(dataset, exists_ok=True)
            logger.info(f"Created dataset {self.project_id}.{self.dataset_id}")

        except Exception as ex:
            logger.error(f"Failed to create dataset: {ex}")
            raise

    def create_campaigns_table(self) -> None:
        """Create campaigns performance table."""
        schema = [
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("customer_name", "STRING"),
            bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("campaign_name", "STRING"),
            bigquery.SchemaField("campaign_status", "STRING"),
            bigquery.SchemaField("impressions", "INTEGER"),
            bigquery.SchemaField("clicks", "INTEGER"),
            bigquery.SchemaField("cost_micros", "INTEGER"),
            bigquery.SchemaField("cost", "FLOAT"),
            bigquery.SchemaField("conversions", "FLOAT"),
            bigquery.SchemaField("ctr", "FLOAT"),
            bigquery.SchemaField("average_cpc", "FLOAT"),
            bigquery.SchemaField("average_cpc_dollars", "FLOAT"),
            bigquery.SchemaField("cost_per_conversion", "FLOAT"),
            bigquery.SchemaField("conversion_rate", "FLOAT"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]

        self._create_table("campaigns_performance", schema)

    def create_keywords_table(self) -> None:
        """Create keywords performance table."""
        schema = [
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("ad_group_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("criterion_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("keyword_text", "STRING"),
            bigquery.SchemaField("match_type", "STRING"),
            bigquery.SchemaField("quality_score", "INTEGER"),
            bigquery.SchemaField("impressions", "INTEGER"),
            bigquery.SchemaField("clicks", "INTEGER"),
            bigquery.SchemaField("cost_micros", "INTEGER"),
            bigquery.SchemaField("cost", "FLOAT"),
            bigquery.SchemaField("conversions", "FLOAT"),
            bigquery.SchemaField("ctr", "FLOAT"),
            bigquery.SchemaField("average_cpc", "FLOAT"),
            bigquery.SchemaField("average_cpc_dollars", "FLOAT"),
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]

        self._create_table("keywords_performance", schema)

    def create_ad_metrics_table(self) -> None:
        """Create multi-platform ad metrics table for Reddit, Microsoft, LinkedIn, etc."""
        schema = [
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("platform", "STRING", mode="REQUIRED"),  # reddit, microsoft, linkedin, etc
            bigquery.SchemaField("account_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("account_name", "STRING"),
            bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("campaign_name", "STRING"),
            bigquery.SchemaField("adgroup_id", "STRING"),
            bigquery.SchemaField("adgroup_name", "STRING"),
            bigquery.SchemaField("ad_id", "STRING"),
            bigquery.SchemaField("ad_name", "STRING"),
            bigquery.SchemaField("impressions", "INTEGER"),
            bigquery.SchemaField("clicks", "INTEGER"),
            bigquery.SchemaField("spend", "FLOAT"),  # Already in USD
            bigquery.SchemaField("conversions", "FLOAT"),
            bigquery.SchemaField("ctr", "FLOAT"),
            bigquery.SchemaField("cpc", "FLOAT"),  # Cost per click in USD
            bigquery.SchemaField("cpm", "FLOAT"),  # Cost per thousand impressions in USD
            bigquery.SchemaField("conversion_rate", "FLOAT"),
            bigquery.SchemaField("cost_per_conversion", "FLOAT"),
            bigquery.SchemaField("revenue", "FLOAT"),  # Revenue from conversions
            bigquery.SchemaField("roas", "FLOAT"),  # Return on ad spend
            bigquery.SchemaField("raw", "JSON"),  # Store original API response
            bigquery.SchemaField("updated_at", "TIMESTAMP"),
        ]

        self._create_table("ad_metrics", schema)

    def _create_table(
        self, table_name: str, schema: list[bigquery.SchemaField]
    ) -> None:
        """Create a table with the given schema."""
        try:
            table_ref = self.dataset_ref.table(table_name)
            table = bigquery.Table(table_ref, schema=schema)

            # Add partitioning by date for better performance
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field="date"
            )

            table = self.client.create_table(table, exists_ok=True)
            logger.info(
                f"Created table {self.project_id}.{self.dataset_id}.{table_name}"
            )

        except Exception as ex:
            logger.error(f"Failed to create table {table_name}: {ex}")
            raise

    def insert_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Insert a pandas DataFrame into a BigQuery table."""
        try:
            table_ref = self.dataset_ref.table(table_name)

            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=False,
            )

            job = self.client.load_table_from_dataframe(
                df, table_ref, job_config=job_config
            )

            job.result()  # Wait for job to complete
            logger.info(f"Inserted {len(df)} rows into {table_name}")

        except Exception as ex:
            logger.error(f"Failed to insert data into {table_name}: {ex}")
            raise

    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame."""
        try:
            return self.client.query(sql).to_dataframe()
        except Exception as ex:
            logger.error(f"Query failed: {ex}")
            raise

    def get_campaign_performance(
        self, customer_id: str, days: int = 30
    ) -> pd.DataFrame:
        """Get campaign performance for the last N days."""
        sql = f"""
        SELECT
            date,
            campaign_name,
            impressions,
            clicks,
            cost_micros / 1000000 as cost,
            conversions,
            ctr,
            average_cpc
        FROM `{self.project_id}.{self.dataset_id}.campaigns_performance`
        WHERE customer_id = @customer_id
        AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
        ORDER BY date DESC, impressions DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                bigquery.ScalarQueryParameter("days", "INT64", days),
            ]
        )

        return self.client.query(sql, job_config=job_config).to_dataframe()


def create_bigquery_client_from_env() -> BigQueryClient:
    """Create BigQuery client from environment variables or Streamlit secrets.

    Priority order:
    1) Streamlit Cloud secrets with a service account dict under "gcp_service_account"
       and project/dataset under either root or the "bigquery" section
    2) Streamlit Cloud secrets with only project/dataset (use ADC if present)
    3) Local env vars (.env) with optional GOOGLE_APPLICATION_CREDENTIALS path
    """
    import streamlit as st
    from dotenv import load_dotenv
    from google.oauth2 import service_account as _sa

    # Load environment variables from .env file (for local dev)
    load_dotenv()

    def _mk_client(
        project_id: str, dataset_id: str, credentials=None
    ) -> BigQueryClient:
        client = bigquery.Client(credentials=credentials, project=project_id)
        # Create custom BigQuery client wrapper without re-running __init__
        bq_client = BigQueryClient.__new__(BigQueryClient)
        bq_client.project_id = project_id
        bq_client.dataset_id = dataset_id
        bq_client.client = client
        bq_client.dataset_ref = client.dataset(dataset_id)
        return bq_client

    # Streamlit Cloud (secrets) — support both nested and root keys
    if hasattr(st, "secrets") and st.secrets:
        # Prefer nested section first
        project_id = None
        dataset_id = None
        credentials = None

        if "bigquery" in st.secrets:
            section = st.secrets["bigquery"]
            project_id = section.get("GOOGLE_CLOUD_PROJECT") or section.get(
                "project_id"
            )
            dataset_id = section.get("BIGQUERY_DATASET_ID", "google_ads_data")
        else:
            project_id = st.secrets.get("GOOGLE_CLOUD_PROJECT") or st.secrets.get(
                "project_id"
            )
            dataset_id = st.secrets.get("BIGQUERY_DATASET_ID", "google_ads_data")

        # Service account JSON embedded as a dict in secrets (recommended)
        # Streamlit convention: [gcp_service_account] ...
        if "gcp_service_account" in st.secrets:
            sa_info = dict(st.secrets["gcp_service_account"])  # Copy to plain dict
            # Only use if required fields exist (avoid empty table in local dev)
            required_keys = {"client_email", "private_key", "token_uri"}
            if sa_info and required_keys.issubset(sa_info.keys()):
                credentials = _sa.Credentials.from_service_account_info(
                    sa_info,
                    scopes=[
                        "https://www.googleapis.com/auth/bigquery",
                    ],
                )
                if not project_id:
                    project_id = sa_info.get("project_id")

        if project_id:
            return _mk_client(
                project_id=project_id,
                dataset_id=dataset_id or "google_ads_data",
                credentials=credentials,
            )
        # If no project_id found in secrets, fall through to env handling

    # Local development fallback (env vars)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("project_id")
    dataset_id = os.getenv("BIGQUERY_DATASET_ID", "google_ads_data")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Prefer file-based service account if provided and exists
    if credentials_path and os.path.exists(credentials_path):
        credentials = _sa.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/bigquery"],
        )
        return _mk_client(
            project_id=project_id or credentials.project_id,
            dataset_id=dataset_id,
            credentials=credentials,
        )

    if not project_id:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT (or project_id) is required via secrets or env"
        )

    # Use ADC (e.g., `gcloud auth application-default login`) or metadata when available
    return _mk_client(project_id=project_id, dataset_id=dataset_id)
