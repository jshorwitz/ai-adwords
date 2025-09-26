"""Check when BigQuery tables were last updated."""

import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_table_last_updated():
    """Check when BigQuery tables were last updated."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        
        logger.info("🔍 Checking BigQuery table update times...")
        
        # Get BigQuery service
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            logger.error("❌ BigQuery service not available")
            return False
        
        project_id = bq_service.bq_client.project_id
        dataset_id = bq_service.bq_client.dataset_id
        
        logger.info(f"📊 Project: {project_id}")
        logger.info(f"📚 Dataset: {dataset_id}")
        
        # Query table metadata for last modified time
        metadata_query = f"""
        SELECT 
            table_id as table_name,
            creation_time,
            last_modified_time,
            row_count,
            size_bytes
        FROM `{project_id}.{dataset_id}.__TABLES__`
        ORDER BY last_modified_time DESC
        """
        
        logger.info("🔍 Getting table metadata...")
        metadata_df = bq_service.bq_client.query(metadata_query)
        
        if metadata_df.empty:
            logger.warning("⚠️  No table metadata found")
        else:
            logger.info("✅ Table metadata retrieved:")
            for _, row in metadata_df.iterrows():
                last_modified = datetime.fromtimestamp(row['last_modified_time'] / 1000)
                logger.info(f"  📊 {row['table_name']}: Last modified {last_modified.strftime('%Y-%m-%d %H:%M:%S')}, {row['row_count']:,} rows")
        
        # Check most recent data dates in key tables
        tables_to_check = ['campaigns_performance', 'keywords_performance', 'ad_metrics']
        
        for table_name in tables_to_check:
            try:
                date_query = f"""
                SELECT 
                    MAX(date) as latest_date,
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT date) as date_count
                FROM `{project_id}.{dataset_id}.{table_name}`
                """
                
                logger.info(f"🔍 Checking data dates in {table_name}...")
                date_df = bq_service.bq_client.query(date_query)
                
                if not date_df.empty and date_df.iloc[0]['latest_date'] is not None:
                    row = date_df.iloc[0]
                    logger.info(f"  ✅ {table_name}: Latest data from {row['latest_date']}, {row['total_rows']:,} total rows, {row['date_count']} unique dates")
                else:
                    logger.info(f"  ⚠️  {table_name}: No data found")
                    
            except Exception as e:
                if "Not found" in str(e):
                    logger.info(f"  ⚠️  {table_name}: Table does not exist")
                else:
                    logger.warning(f"  ❌ {table_name}: Error checking data - {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Table update check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Checking BigQuery table update times")
    print("=" * 60)
    
    success = asyncio.run(check_table_last_updated())
    
    if success:
        print("=" * 60)
        print("✅ Table update check completed!")
    else:
        print("=" * 60)
        print("❌ Table update check failed")
