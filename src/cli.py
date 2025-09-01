"""CLI interface using Typer for Google Ads operations."""

import typer

from src.ads.accounts import list_accessible_clients

app = typer.Typer(help="AI AdWords - Google Ads management CLI")


@app.command("accounts")
def accounts() -> None:
    """List accessible Google Ads accounts under the MCC."""
    results = list_accessible_clients()
    for r in results:
        print(r)


@app.command("account-info")
def account_info(
    customer_id: str = typer.Option(..., help="Customer ID to get info for")
) -> None:
    """Get detailed information for a specific customer account."""
    from src.ads.accounts import get_customer_info
    
    info = get_customer_info(customer_id)
    if info:
        print(f"Account ID: {info.get('id', 'N/A')}")
        print(f"Name: {info.get('name', 'N/A')}")
        print(f"Currency: {info.get('currency', 'N/A')}")
        print(f"Timezone: {info.get('timezone', 'N/A')}")
        print(f"Status: {info.get('status', 'N/A')}")
    else:
        print(f"Could not retrieve information for customer {customer_id}")


@app.command("setup-bigquery")
def setup_bigquery() -> None:
    """Setup BigQuery dataset and tables for Google Ads data."""
    from src.ads.bigquery_client import create_bigquery_client_from_env
    
    try:
        print("Setting up BigQuery...")
        client = create_bigquery_client_from_env()
        
        print("Creating dataset...")
        client.create_dataset()
        
        print("Creating campaigns table...")
        client.create_campaigns_table()
        
        print("Creating keywords table...")
        client.create_keywords_table()
        
        print("✅ BigQuery setup complete!")
        print(f"Dataset: {client.project_id}.{client.dataset_id}")
        
    except Exception as ex:
        print(f"❌ BigQuery setup failed: {ex}")


@app.command("bq-test")
def bigquery_test() -> None:
    """Test BigQuery connection."""
    from src.ads.bigquery_client import create_bigquery_client_from_env
    
    try:
        client = create_bigquery_client_from_env()
        
        # Test query
        result = client.query("SELECT 1 as test_value")
        print(f"✅ BigQuery connection successful!")
        print(f"Project: {client.project_id}")
        print(f"Dataset: {client.dataset_id}")
        
    except Exception as ex:
        print(f"❌ BigQuery connection failed: {ex}")


@app.command("sync-data")
def sync_data(
    customer_ids: str = typer.Option(..., help="Comma-separated customer IDs"),
    days_back: int = typer.Option(7, help="Number of days to sync"),
    data_type: str = typer.Option("all", help="Data type: all, campaigns, keywords")
) -> None:
    """Sync Google Ads data to BigQuery."""
    from src.ads.etl_pipeline import GoogleAdsETLPipeline
    
    try:
        customer_list = [cid.strip() for cid in customer_ids.split(",")]
        pipeline = GoogleAdsETLPipeline()
        
        print(f"Starting sync for {len(customer_list)} customers...")
        print(f"Date range: Last {days_back} days")
        print(f"Data type: {data_type}")
        
        if data_type == "all":
            pipeline.full_sync(customer_list, days_back)
        elif data_type == "campaigns":
            pipeline.sync_campaign_data(customer_list, days_back)
        elif data_type == "keywords":
            pipeline.sync_keyword_data(customer_list, days_back)
        else:
            print(f"Unknown data type: {data_type}")
            return
            
        print("✅ Data sync completed successfully!")
        
    except Exception as ex:
        print(f"❌ Data sync failed: {ex}")


@app.command("backfill")
def backfill(
    customer_ids: str = typer.Option(..., help="Comma-separated customer IDs"),
    days_back: int = typer.Option(30, help="Number of days to backfill")
) -> None:
    """Backfill historical Google Ads data to BigQuery."""
    from src.ads.etl_pipeline import backfill_data
    
    try:
        customer_list = [cid.strip() for cid in customer_ids.split(",")]
        
        print(f"Starting backfill for {len(customer_list)} customers...")
        print(f"Backfilling last {days_back} days...")
        
        backfill_data(customer_list, days_back)
        
        print("✅ Backfill completed successfully!")
        
    except Exception as ex:
        print(f"❌ Backfill failed: {ex}")


@app.command("test-report")
def test_report(
    customer_id: str = typer.Option(..., help="Customer ID to test")
) -> None:
    """Test Google Ads reporting for a specific customer."""
    from src.ads.reporting import ReportingManager
    
    try:
        print(f"Testing reporting for customer: {customer_id}")
        
        reporting_mgr = ReportingManager(customer_id)
        
        # Test campaign data
        print("Fetching campaign performance...")
        campaign_df = reporting_mgr.export_campaign_performance()
        print(f"Retrieved {len(campaign_df)} campaign records")
        
        # Test keyword data
        print("Fetching keyword performance...")
        keyword_df = reporting_mgr.export_keyword_performance()
        print(f"Retrieved {len(keyword_df)} keyword records")
        
        print("✅ Reporting test completed!")
        
        # Show sample data
        if not campaign_df.empty:
            print("\nSample campaign data:")
            print(campaign_df.head())
            
    except Exception as ex:
        print(f"❌ Reporting test failed: {ex}")


@app.command()
def campaigns(
    customer_id: str = typer.Option(..., help="Google Ads customer ID"),
    action: str = typer.Option("list", help="Action: list, create, update"),
) -> None:
    """Manage campaigns."""
    if action == "list":
        from src.ads.campaigns import list_campaigns
        rows = list_campaigns(customer_id)
        if not rows:
            print("No campaigns found or unable to fetch campaigns.")
            return
        # Simple table output
        print(f"Found {len(rows)} campaigns:\n")
        print(f"{'ID':<15} {'STATUS':<12} NAME")
        print("-" * 60)
        for r in rows:
            print(f"{r['id']:<15} {r['status']:<12} {r['name']}")
        return

    print(f"Unsupported action: {action}")


@app.command()
def reports(
    customer_id: str = typer.Option(..., help="Google Ads customer ID"),
    report_type: str = typer.Option("campaign", help="Report type"),
) -> None:
    """Generate reports."""
    pass


@app.command()
def optimize(
    customer_id: str = typer.Option(..., help="Google Ads customer ID"),
    dry_run: bool = typer.Option(True, help="Run in validation mode"),
) -> None:
    """Run optimization tasks."""
    pass


if __name__ == "__main__":
    app()
