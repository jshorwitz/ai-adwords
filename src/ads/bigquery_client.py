"""BigQuery client for Google Ads data warehouse."""

import logging
import os
from typing import Dict, Any, List, Optional

from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

logger = logging.getLogger(__name__)


class BigQueryClient:
    """BigQuery client for storing Google Ads data."""
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        dataset_id: str = "google_ads_data"
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
                credentials_path,
                scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            self.client = bigquery.Client(
                credentials=credentials, 
                project=project_id
            )
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
    
    def _create_table(self, table_name: str, schema: List[bigquery.SchemaField]) -> None:
        """Create a table with the given schema."""
        try:
            table_ref = self.dataset_ref.table(table_name)
            table = bigquery.Table(table_ref, schema=schema)
            
            # Add partitioning by date for better performance
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="date"
            )
            
            table = self.client.create_table(table, exists_ok=True)
            logger.info(f"Created table {self.project_id}.{self.dataset_id}.{table_name}")
            
        except Exception as ex:
            logger.error(f"Failed to create table {table_name}: {ex}")
            raise
    
    def insert_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """Insert a pandas DataFrame into a BigQuery table."""
        try:
            table_ref = self.dataset_ref.table(table_name)
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=False
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
        self, 
        customer_id: str, 
        days: int = 30
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
    """Create BigQuery client from environment variables."""
    import streamlit as st
    from dotenv import load_dotenv
    
    # Load environment variables from .env file (for local dev)
    load_dotenv()
    
    # Try Streamlit secrets first (for cloud deployment)
    try:
        project_id = st.secrets["GOOGLE_CLOUD_PROJECT"]
        dataset_id = st.secrets.get("BIGQUERY_DATASET_ID", "google_ads_data")
        credentials_path = None  # Use default credentials in cloud
    except:
        # Fall back to environment variables (for local dev)
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        dataset_id = os.getenv("BIGQUERY_DATASET_ID", "google_ads_data")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Don't use credentials file if it doesn't exist
        if credentials_path and not os.path.exists(credentials_path):
            credentials_path = None
    
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable required")
    
    return BigQueryClient(
        project_id=project_id,
        credentials_path=credentials_path,
        dataset_id=dataset_id
    )
