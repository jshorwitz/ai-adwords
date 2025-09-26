"""Check Google Cloud Data Transfer Service status and existing transfers."""

import logging
from google.cloud import bigquery_datatransfer_v1
from google.cloud import bigquery
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_data_transfer_service():
    """Check existing data transfer configurations."""
    try:
        project_id = "ai-adwords-470622"
        location = "US"
        
        logger.info("🔍 Checking Google Cloud Data Transfer Service...")
        logger.info(f"📊 Project: {project_id}")
        logger.info(f"🌍 Location: {location}")
        
        # Initialize Data Transfer client
        transfer_client = bigquery_datatransfer_v1.DataTransferServiceClient()
        
        # List existing transfers
        parent = f"projects/{project_id}/locations/{location}"
        
        logger.info("📋 Existing Data Transfer Configurations:")
        logger.info("-" * 60)
        
        transfers = transfer_client.list_transfer_configs(parent=parent)
        transfer_count = 0
        
        for transfer in transfers:
            transfer_count += 1
            logger.info(f"🔄 Transfer #{transfer_count}:")
            logger.info(f"   Name: {transfer.display_name}")
            logger.info(f"   Data Source: {transfer.data_source_id}")
            logger.info(f"   Destination: {transfer.destination_dataset_id}")
            logger.info(f"   Schedule: {transfer.schedule}")
            logger.info(f"   State: {transfer.state.name}")
            logger.info(f"   Next Run: {transfer.next_run_time}")
            logger.info("")
            
            # Check recent runs for this transfer
            logger.info(f"📈 Recent Runs for {transfer.display_name}:")
            runs_parent = transfer.name
            runs = transfer_client.list_transfer_runs(parent=runs_parent)
            
            run_count = 0
            for run in runs:
                if run_count >= 3:  # Show only last 3 runs
                    break
                run_count += 1
                logger.info(f"     Run {run_count}: {run.state.name} - {run.start_time}")
                if run.error_status and run.error_status.message:
                    logger.info(f"       Error: {run.error_status.message}")
            
            if run_count == 0:
                logger.info("     No recent runs found")
            logger.info("")
        
        if transfer_count == 0:
            logger.warning("⚠️  No Data Transfer configurations found")
            logger.info("💡 To create a Google Ads transfer:")
            logger.info("   1. Go to: https://console.cloud.google.com/bigquery/transfers")
            logger.info("   2. Click 'Create Transfer'")
            logger.info("   3. Select 'Google Ads' as data source")
            logger.info("   4. Configure with customer ID: 9639990200")
        else:
            logger.info(f"✅ Found {transfer_count} data transfer configuration(s)")
        
        # Check if Google Ads tables exist in BigQuery
        logger.info("🔍 Checking for Google Ads tables in BigQuery...")
        bq_client = bigquery.Client(project=project_id)
        dataset_id = "google_ads_data"
        
        try:
            dataset = bq_client.get_dataset(f"{project_id}.{dataset_id}")
            tables = list(bq_client.list_tables(dataset))
            
            google_ads_tables = [t for t in tables if t.table_id.startswith('p_')]
            
            if google_ads_tables:
                logger.info(f"✅ Found {len(google_ads_tables)} Google Ads tables:")
                for table in google_ads_tables[:5]:  # Show first 5
                    logger.info(f"   📊 {table.table_id}")
                    # Get row count
                    try:
                        query = f"SELECT COUNT(*) as row_count FROM `{project_id}.{dataset_id}.{table.table_id}`"
                        result = bq_client.query(query).result()
                        row_count = list(result)[0].row_count
                        logger.info(f"       Rows: {row_count:,}")
                    except:
                        pass
                        
                if len(google_ads_tables) > 5:
                    logger.info(f"   ... and {len(google_ads_tables) - 5} more tables")
            else:
                logger.warning("⚠️  No Google Ads tables found (no tables starting with 'p_')")
                
        except Exception as e:
            logger.error(f"❌ Error checking BigQuery dataset: {e}")
        
        return transfer_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error checking Data Transfer Service: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_data_transfer_api():
    """Check if BigQuery Data Transfer API is enabled."""
    try:
        from googleapiclient import discovery
        from google.auth import default
        
        credentials, project = default()
        service = discovery.build('serviceusage', 'v1', credentials=credentials)
        
        api_name = 'bigquerydatatransfer.googleapis.com'
        request = service.services().get(name=f'projects/{project}/services/{api_name}')
        response = request.execute()
        
        state = response.get('state', 'UNKNOWN')
        logger.info(f"📡 BigQuery Data Transfer API Status: {state}")
        
        if state == 'ENABLED':
            return True
        else:
            logger.warning("⚠️  BigQuery Data Transfer API is not enabled")
            logger.info("💡 Enable it at: https://console.cloud.google.com/apis/library/bigquerydatatransfer.googleapis.com")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  Could not check API status: {e}")
        return True  # Assume enabled and let the main check handle it

if __name__ == "__main__":
    print("🚀 Google Cloud Data Transfer Service Status Check")
    print("=" * 70)
    
    # Check if API is enabled
    api_enabled = check_data_transfer_api()
    print()
    
    # Check existing transfers
    if api_enabled:
        has_transfers = check_data_transfer_service()
        
        print("=" * 70)
        if has_transfers:
            print("✅ Data Transfer Service is configured!")
            print("💡 Check the transfers above for status and recent runs")
        else:
            print("⚠️  No Google Ads Data Transfer found")
            print("📋 Follow the setup guide in setup_google_data_transfer.md")
            print("🔗 Direct link: https://console.cloud.google.com/bigquery/transfers")
    else:
        print("=" * 70)
        print("❌ BigQuery Data Transfer API needs to be enabled first")
