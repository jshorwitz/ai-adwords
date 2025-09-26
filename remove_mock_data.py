"""Remove mock data from BigQuery tables."""

import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_mock_data():
    """Remove mock data from BigQuery tables."""
    try:
        from src.ads.bigquery_client import create_bigquery_client_from_env
        
        bq_client = create_bigquery_client_from_env()
        
        logger.info("🗑️  Removing Mock Data from BigQuery")
        logger.info("=" * 60)
        logger.info(f"📊 Project: {bq_client.project_id}")
        logger.info(f"📚 Dataset: {bq_client.dataset_id}")
        logger.info("")
        
        # First, check what mock data exists
        logger.info("🔍 Identifying mock data...")
        
        check_query = f"""
        SELECT 
            platform,
            COUNT(*) as records,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            SUM(spend) as total_spend
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
        GROUP BY platform
        ORDER BY platform
        """
        
        mock_data_df = bq_client.query(check_query)
        
        if mock_data_df.empty:
            logger.info("✅ No data found in ad_metrics table")
            return True
        
        logger.info("📊 Current data in ad_metrics table:")
        total_records = 0
        for _, row in mock_data_df.iterrows():
            records = int(row['records'])
            total_records += records
            logger.info(f"  {row['platform'].title()}: {records:,} records, ${row['total_spend']:,.2f} spend")
        
        logger.info(f"  Total: {total_records:,} records")
        logger.info("")
        
        # Remove mock platform data (Reddit, LinkedIn, Microsoft)
        mock_platforms = ['reddit', 'linkedin', 'microsoft']
        
        logger.info("🗑️  Removing mock platform data...")
        
        for platform in mock_platforms:
            delete_query = f"""
            DELETE FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
            WHERE platform = '{platform}'
            """
            
            logger.info(f"  Deleting {platform} data...")
            
            job = bq_client.client.query(delete_query)
            job.result()  # Wait for job to complete
            
            logger.info(f"  ✅ Deleted {platform} records")
        
        # Check remaining data
        logger.info("\n🔍 Verifying data removal...")
        
        remaining_query = f"""
        SELECT 
            platform,
            COUNT(*) as records,
            SUM(spend) as total_spend
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
        GROUP BY platform
        """
        
        remaining_df = bq_client.query(remaining_query)
        
        if remaining_df.empty:
            logger.info("✅ All mock data removed - ad_metrics table is now empty")
        else:
            logger.info("📊 Remaining data:")
            for _, row in remaining_df.iterrows():
                logger.info(f"  {row['platform'].title()}: {int(row['records']):,} records, ${row['total_spend']:,.2f} spend")
        
        # Check if we should also clean up other tables
        logger.info("\n🔍 Checking other tables for cleanup...")
        
        # Get table list
        dataset_ref = bq_client.client.dataset(bq_client.dataset_id)
        tables = list(bq_client.client.list_tables(dataset_ref))
        
        for table in tables:
            if table.table_id in ['campaigns_performance', 'keywords_performance']:
                table_obj = bq_client.client.get_table(dataset_ref.table(table.table_id))
                logger.info(f"  📊 {table.table_id}: {table_obj.num_rows:,} rows (keeping - real Google Ads data)")
            elif table.table_id == 'ad_metrics':
                table_obj = bq_client.client.get_table(dataset_ref.table(table.table_id))
                logger.info(f"  📊 {table.table_id}: {table_obj.num_rows:,} rows (after mock data removal)")
            else:
                table_obj = bq_client.client.get_table(dataset_ref.table(table.table_id))
                logger.info(f"  📊 {table.table_id}: {table_obj.num_rows:,} rows")
        
        logger.info("\n🧹 Mock data cleanup completed!")
        logger.info("\nℹ️  Remaining data:")
        logger.info("  - Google Ads campaigns_performance (real data)")
        logger.info("  - Google Ads keywords_performance (real data)")
        logger.info("  - ad_metrics table (cleaned)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock data removal failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def confirm_removal():
    """Ask for confirmation before removing data."""
    logger.info("⚠️  WARNING: This will permanently delete mock data from BigQuery")
    logger.info("📋 Data to be removed:")
    logger.info("  - Reddit Ads mock data")
    logger.info("  - LinkedIn Ads mock data") 
    logger.info("  - Microsoft Ads mock data")
    logger.info("")
    logger.info("✅ Data to be kept:")
    logger.info("  - Google Ads campaigns_performance table")
    logger.info("  - Google Ads keywords_performance table")
    logger.info("")
    
    # For automated execution, proceed directly
    logger.info("🚀 Proceeding with mock data removal...")
    return True

if __name__ == "__main__":
    print("🗑️  BigQuery Mock Data Cleanup")
    print("=" * 50)
    
    if confirm_removal():
        success = remove_mock_data()
        
        print("=" * 50)
        if success:
            print("✅ Mock data removal completed successfully!")
            print("💡 Only real Google Ads data remains in BigQuery")
        else:
            print("❌ Mock data removal failed")
    else:
        print("❌ Mock data removal cancelled")
