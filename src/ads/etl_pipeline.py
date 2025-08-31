"""ETL pipeline for Google Ads data to BigQuery."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd

from src.ads.reporting import ReportingManager
from src.ads.bigquery_client import create_bigquery_client_from_env

logger = logging.getLogger(__name__)


class GoogleAdsETLPipeline:
    """ETL Pipeline for Google Ads to BigQuery."""
    
    def __init__(self):
        """Initialize ETL pipeline."""
        self.bq_client = create_bigquery_client_from_env()
    
    def sync_campaign_data(
        self, 
        customer_ids: List[str], 
        days_back: int = 7
    ) -> None:
        """Sync campaign performance data for multiple customers."""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Syncing campaign data for {len(customer_ids)} customers")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        all_campaign_data = []
        
        for customer_id in customer_ids:
            try:
                logger.info(f"Processing customer: {customer_id}")
                
                # Get campaign performance data
                reporting_mgr = ReportingManager(customer_id)
                campaign_df = reporting_mgr.export_campaign_performance(start_date, end_date)
                
                if not campaign_df.empty:
                    # Transform data for BigQuery
                    campaign_df = self._transform_campaign_data(campaign_df)
                    all_campaign_data.append(campaign_df)
                    logger.info(f"Retrieved {len(campaign_df)} campaign records for {customer_id}")
                else:
                    logger.warning(f"No campaign data found for customer {customer_id}")
                    
            except Exception as ex:
                logger.error(f"Failed to sync campaign data for {customer_id}: {ex}")
        
        # Combine and load all data
        if all_campaign_data:
            combined_df = pd.concat(all_campaign_data, ignore_index=True)
            self._load_to_bigquery(combined_df, "campaigns_performance")
            logger.info(f"Loaded {len(combined_df)} campaign records to BigQuery")
        else:
            logger.warning("No campaign data to load")
    
    def sync_keyword_data(
        self, 
        customer_ids: List[str], 
        days_back: int = 7
    ) -> None:
        """Sync keyword performance data for multiple customers."""
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Syncing keyword data for {len(customer_ids)} customers")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        all_keyword_data = []
        
        for customer_id in customer_ids:
            try:
                logger.info(f"Processing customer: {customer_id}")
                
                # Get keyword performance data
                reporting_mgr = ReportingManager(customer_id)
                keyword_df = reporting_mgr.export_keyword_performance(start_date, end_date)
                
                if not keyword_df.empty:
                    # Transform data for BigQuery
                    keyword_df = self._transform_keyword_data(keyword_df)
                    all_keyword_data.append(keyword_df)
                    logger.info(f"Retrieved {len(keyword_df)} keyword records for {customer_id}")
                else:
                    logger.warning(f"No keyword data found for customer {customer_id}")
                    
            except Exception as ex:
                logger.error(f"Failed to sync keyword data for {customer_id}: {ex}")
        
        # Combine and load all data
        if all_keyword_data:
            combined_df = pd.concat(all_keyword_data, ignore_index=True)
            self._load_to_bigquery(combined_df, "keywords_performance")
            logger.info(f"Loaded {len(combined_df)} keyword records to BigQuery")
        else:
            logger.warning("No keyword data to load")
    
    def _transform_campaign_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform campaign data for BigQuery."""
        # Convert date column to proper format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Add updated_at timestamp
        df['updated_at'] = datetime.now()
        
        # Convert micros to actual currency values for some columns
        if 'cost_micros' in df.columns:
            df['cost'] = df['cost_micros'] / 1_000_000
        if 'average_cpc' in df.columns:
            df['average_cpc_dollars'] = df['average_cpc'] / 1_000_000
        
        # Ensure required columns are present
        required_columns = [
            'date', 'customer_id', 'campaign_id', 'campaign_name',
            'impressions', 'clicks', 'cost_micros', 'conversions'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                if col in ['impressions', 'clicks', 'cost_micros']:
                    df[col] = 0
                elif col == 'conversions':
                    df[col] = 0.0
                else:
                    df[col] = ''
        
        return df
    
    def _transform_keyword_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform keyword data for BigQuery."""
        # Convert date column to proper format
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Add updated_at timestamp
        df['updated_at'] = datetime.now()
        
        # Convert micros to actual currency values
        if 'cost_micros' in df.columns:
            df['cost'] = df['cost_micros'] / 1_000_000
        if 'average_cpc' in df.columns:
            df['average_cpc_dollars'] = df['average_cpc'] / 1_000_000
        
        # Ensure required columns are present
        required_columns = [
            'date', 'customer_id', 'campaign_id', 'ad_group_id',
            'criterion_id', 'keyword_text', 'impressions', 'clicks', 'cost_micros'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                if col in ['impressions', 'clicks', 'cost_micros', 'quality_score']:
                    df[col] = 0
                elif col == 'conversions':
                    df[col] = 0.0
                else:
                    df[col] = ''
        
        return df
    
    def _load_to_bigquery(self, df: pd.DataFrame, table_name: str) -> None:
        """Load DataFrame to BigQuery table."""
        try:
            self.bq_client.insert_dataframe(table_name, df)
            logger.info(f"Successfully loaded {len(df)} rows to {table_name}")
        except Exception as ex:
            logger.error(f"Failed to load data to {table_name}: {ex}")
            raise
    
    def full_sync(self, customer_ids: List[str], days_back: int = 7) -> None:
        """Perform full data sync for all data types."""
        logger.info("Starting full data sync...")
        
        try:
            # Sync campaign data
            self.sync_campaign_data(customer_ids, days_back)
            
            # Sync keyword data
            self.sync_keyword_data(customer_ids, days_back)
            
            logger.info("Full data sync completed successfully")
            
        except Exception as ex:
            logger.error(f"Full data sync failed: {ex}")
            raise


def run_daily_sync(customer_ids: List[str]) -> None:
    """Run daily data sync - typically called by scheduler."""
    pipeline = GoogleAdsETLPipeline()
    pipeline.full_sync(customer_ids, days_back=2)  # Get last 2 days to handle delays


def backfill_data(customer_ids: List[str], days_back: int = 30) -> None:
    """Backfill historical data."""
    pipeline = GoogleAdsETLPipeline()
    pipeline.full_sync(customer_ids, days_back=days_back)
