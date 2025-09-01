"""CLI interface using Typer for Google Ads operations."""

from typing import Optional
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
    name: Optional[str] = typer.Option(None, help="Campaign name (for create)"),
    budget: Optional[float] = typer.Option(None, help="Daily budget in dollars (for create)"),
    channel: str = typer.Option("SEARCH", help="Channel for create: SEARCH|DISPLAY|VIDEO"),
    bidding: str = typer.Option("MAXIMIZE_CONVERSIONS", help="Bidding for create: MAXIMIZE_CONVERSIONS|MAXIMIZE_CONVERSION_VALUE|MANUAL_CPC"),
    start_date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (optional)"),
    end_date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (optional)"),
    dry_run: bool = typer.Option(True, help="validate_only for create"),
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

    if action == "create":
        from src.ads.campaigns import create_campaign
        if not name:
            name = typer.prompt("Campaign name")
        if budget is None:
            budget = typer.prompt("Daily budget ($)", type=float)
        budget_micros = int(float(budget) * 1_000_000)
        # If start/end provided as empty strings, normalize to None
        start_date_val = start_date or None
        end_date_val = end_date or None

        resp = create_campaign(
            customer_id=customer_id,
            name=name,
            daily_budget_micros=budget_micros,
            channel=channel,
            bidding_strategy=bidding,
            start_date=start_date_val,
            end_date=end_date_val,
            dry_run=dry_run,
        )
        print("\nResult:")
        for k, v in resp.items():
            print(f"- {k}: {v}")
        return

    print(f"Unsupported action: {action}")


@app.command()
def keywords(
    customer_id: str = typer.Option(..., help="Google Ads customer ID"),
    limit: int = typer.Option(20, help="Max rows to return"),
) -> None:
    """List top keywords by impressions."""
    from src.ads.keywords import list_keywords

    rows = list_keywords(customer_id, limit)
    if not rows:
        print("No keywords found or unable to fetch keywords.")
        return

    print(f"Top {len(rows)} keywords:\n")
    print(f"{'IMP':>6} {'CLK':>6} {'AVG_CPC':>8}  KEYWORD [MATCH] (CAMP/ADG)")
    print("-" * 80)
    for r in rows:
        avg_cpc = f"${r.get('avg_cpc', 0):.2f}"
        print(f"{r['impressions']:>6} {r['clicks']:>6} {avg_cpc:>8}  {r['keyword']} [{r['match_type']}] ({r['campaign_id']}/{r['ad_group_id']})")


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
