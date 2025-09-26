"""Check synter_analytics dataset and configure transfers."""

import logging
from google.cloud import bigquery

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_synter_analytics():
    """Check synter_analytics dataset and compare with google_ads_data."""
    try:
        project_id = "ai-adwords-470622"
        
        logger.info("🔍 Checking synter_analytics dataset...")
        logger.info(f"📊 Project: {project_id}")
        logger.info("")
        
        bq_client = bigquery.Client(project=project_id)
        
        # Check if synter_analytics dataset exists
        datasets = list(bq_client.list_datasets())
        dataset_names = [d.dataset_id for d in datasets]
        
        logger.info(f"📚 Available datasets: {dataset_names}")
        logger.info("")
        
        # Check synter_analytics dataset
        if "synter_analytics" in dataset_names:
            logger.info("✅ synter_analytics dataset exists")
            
            synter_dataset = bq_client.get_dataset("synter_analytics")
            synter_tables = list(bq_client.list_tables(synter_dataset))
            
            logger.info(f"📊 Tables in synter_analytics: {len(synter_tables)}")
            
            if synter_tables:
                total_rows = 0
                for table in synter_tables:
                    table_obj = bq_client.get_table(synter_dataset.table(table.table_id))
                    total_rows += table_obj.num_rows
                    logger.info(f"  📊 {table.table_id}: {table_obj.num_rows:,} rows")
                    
                    # Check if this is ad_metrics and get platform breakdown
                    if table.table_id == 'ad_metrics' and table_obj.num_rows > 0:
                        platform_query = f"""
                        SELECT 
                            platform,
                            COUNT(*) as records,
                            SUM(spend) as total_spend,
                            MIN(date) as earliest_date,
                            MAX(date) as latest_date
                        FROM `{project_id}.synter_analytics.ad_metrics`
                        GROUP BY platform
                        ORDER BY total_spend DESC
                        """
                        
                        try:
                            platform_df = bq_client.query(platform_query).to_dataframe()
                            logger.info("    Platform breakdown:")
                            for _, row in platform_df.iterrows():
                                logger.info(f"      {row['platform'].title()}: {int(row['records'])} records, ${row['total_spend']:,.2f} spend ({row['earliest_date']} to {row['latest_date']})")
                        except Exception as e:
                            logger.warning(f"    Could not get platform breakdown: {e}")
                
                logger.info(f"  Total rows in synter_analytics: {total_rows:,}")
            else:
                logger.info("  📝 synter_analytics dataset is empty")
                
        else:
            logger.warning("⚠️  synter_analytics dataset does not exist")
            logger.info("💡 Creating synter_analytics dataset...")
            
            # Create synter_analytics dataset
            dataset = bigquery.Dataset(f"{project_id}.synter_analytics")
            dataset.location = "US"
            dataset.description = "Unified advertising analytics data warehouse"
            
            dataset = bq_client.create_dataset(dataset, exists_ok=True)
            logger.info("✅ Created synter_analytics dataset")
        
        # Compare with google_ads_data dataset
        logger.info("\n🔍 Comparing with google_ads_data dataset...")
        
        if "google_ads_data" in dataset_names:
            google_dataset = bq_client.get_dataset("google_ads_data")
            google_tables = list(bq_client.list_tables(google_dataset))
            
            logger.info(f"📊 Tables in google_ads_data: {len(google_tables)}")
            
            total_google_rows = 0
            for table in google_tables:
                table_obj = bq_client.get_table(google_dataset.table(table.table_id))
                total_google_rows += table_obj.num_rows
                logger.info(f"  📊 {table.table_id}: {table_obj.num_rows:,} rows")
            
            logger.info(f"  Total rows in google_ads_data: {total_google_rows:,}")
        
        # Check Data Transfer Service destination
        logger.info("\n📡 Checking Data Transfer Service configuration...")
        
        from google.cloud import bigquery_datatransfer_v1
        transfer_client = bigquery_datatransfer_v1.DataTransferServiceClient()
        
        parent = f"projects/{project_id}/locations/US"
        transfers = transfer_client.list_transfer_configs(parent=parent)
        
        for transfer in transfers:
            logger.info(f"🔄 Transfer: {transfer.display_name}")
            logger.info(f"   Data Source: {transfer.data_source_id}")
            logger.info(f"   Destination: {transfer.destination_dataset_id}")
            logger.info(f"   State: {transfer.state.name}")
            
            if transfer.destination_dataset_id != "synter_analytics":
                logger.warning(f"⚠️  Transfer is sending to '{transfer.destination_dataset_id}' instead of 'synter_analytics'")
                logger.info("💡 Consider updating the transfer destination to synter_analytics")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Dataset check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_synter_analytics_tables():
    """Create necessary tables in synter_analytics dataset."""
    try:
        project_id = "ai-adwords-470622"
        dataset_id = "synter_analytics"
        
        logger.info(f"\n🛠️  Setting up tables in {dataset_id} dataset...")
        
        from src.ads.bigquery_client import BigQueryClient
        
        # Create BigQuery client pointing to synter_analytics
        bq_client = BigQueryClient(
            project_id=project_id,
            dataset_id=dataset_id
        )
        
        # Create dataset if it doesn't exist
        bq_client.create_dataset()
        
        # Create ad_metrics table with proper schema
        bq_client.create_ad_metrics_table()
        
        # Create other necessary tables
        bq_client.create_campaigns_table()
        bq_client.create_keywords_table()
        
        logger.info("✅ Tables created in synter_analytics dataset")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Table setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Synter Analytics Dataset Check")
    print("=" * 60)
    
    success = check_synter_analytics()
    
    if success:
        print("\n" + "=" * 60)
        print("Setting up synter_analytics tables...")
        setup_success = setup_synter_analytics_tables()
        
        print("=" * 60)
        if setup_success:
            print("✅ synter_analytics dataset check and setup completed!")
            print("💡 Next steps:")
            print("  1. Update Data Transfer Service to use synter_analytics dataset")
            print("  2. Configure Microsoft/LinkedIn transfers to synter_analytics")
            print("  3. Update application config to use synter_analytics by default")
        else:
            print("⚠️  Dataset check completed, but table setup had issues")
    else:
        print("=" * 60)
        print("❌ Dataset check failed")
