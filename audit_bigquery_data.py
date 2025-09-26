"""Comprehensive audit of all data currently in BigQuery."""

import logging
import asyncio
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def audit_bigquery_data():
    """Audit all data currently available in BigQuery."""
    try:
        from src.ads.bigquery_client import create_bigquery_client_from_env
        
        bq_client = create_bigquery_client_from_env()
        
        logger.info("🔍 BigQuery Data Audit")
        logger.info("=" * 80)
        logger.info(f"📊 Project: {bq_client.project_id}")
        logger.info(f"📚 Dataset: {bq_client.dataset_id}")
        logger.info("")
        
        # Get all tables in the dataset
        dataset_ref = bq_client.client.dataset(bq_client.dataset_id)
        tables = list(bq_client.client.list_tables(dataset_ref))
        
        logger.info(f"📋 Total Tables: {len(tables)}")
        logger.info("-" * 80)
        
        total_rows = 0
        
        for table in tables:
            table_ref = dataset_ref.table(table.table_id)
            table_obj = bq_client.client.get_table(table_ref)
            
            logger.info(f"📊 Table: {table.table_id}")
            logger.info(f"   Rows: {table_obj.num_rows:,}")
            logger.info(f"   Size: {table_obj.num_bytes:,} bytes ({table_obj.num_bytes/1024/1024:.2f} MB)")
            logger.info(f"   Created: {table_obj.created}")
            logger.info(f"   Modified: {table_obj.modified}")
            
            total_rows += table_obj.num_rows
            
            # Get sample data for each table
            try:
                sample_query = f"""
                SELECT *
                FROM `{bq_client.project_id}.{bq_client.dataset_id}.{table.table_id}`
                LIMIT 3
                """
                sample_df = bq_client.query(sample_query)
                
                if not sample_df.empty:
                    logger.info(f"   Columns: {list(sample_df.columns)}")
                    
                    # Show date range if date column exists
                    if 'date' in sample_df.columns:
                        date_query = f"""
                        SELECT 
                            MIN(date) as earliest_date,
                            MAX(date) as latest_date,
                            COUNT(DISTINCT date) as unique_dates
                        FROM `{bq_client.project_id}.{bq_client.dataset_id}.{table.table_id}`
                        """
                        date_df = bq_client.query(date_query)
                        if not date_df.empty:
                            date_info = date_df.iloc[0]
                            logger.info(f"   Date Range: {date_info['earliest_date']} to {date_info['latest_date']} ({date_info['unique_dates']} days)")
                
                logger.info("")
                
            except Exception as e:
                logger.warning(f"   ❌ Could not sample data: {e}")
                logger.info("")
        
        logger.info("=" * 80)
        logger.info(f"📊 Dataset Summary: {total_rows:,} total rows across {len(tables)} tables")
        
        # Detailed analysis of key tables
        
        # 1. Ad Metrics Table (Multi-platform data)
        if any(t.table_id == 'ad_metrics' for t in tables):
            logger.info("\n🎯 AD METRICS TABLE - Multi-Platform Data:")
            logger.info("-" * 60)
            
            platform_query = f"""
            SELECT 
                platform,
                COUNT(*) as records,
                COUNT(DISTINCT campaign_id) as campaigns,
                COUNT(DISTINCT date) as days,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(spend) as total_spend,
                SUM(conversions) as total_conversions,
                ROUND(AVG(ctr), 2) as avg_ctr,
                ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2) as cpa
            FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
            GROUP BY platform
            ORDER BY total_spend DESC
            """
            
            platform_df = bq_client.query(platform_query)
            
            for _, row in platform_df.iterrows():
                logger.info(f"  🎪 {row['platform'].title()} Ads:")
                logger.info(f"     Records: {int(row['records']):,}")
                logger.info(f"     Campaigns: {int(row['campaigns'])}")
                logger.info(f"     Date Range: {row['earliest_date']} to {row['latest_date']} ({int(row['days'])} days)")
                logger.info(f"     Spend: ${row['total_spend']:,.2f}")
                logger.info(f"     Clicks: {int(row['total_clicks']):,}")
                logger.info(f"     Conversions: {int(row['total_conversions'])}")
                logger.info(f"     CPA: ${row['cpa']:.2f}")
                logger.info("")
        
        # 2. Google Ads Campaign Performance (Legacy tables)
        if any(t.table_id == 'campaigns_performance' for t in tables):
            logger.info("🔍 CAMPAIGNS PERFORMANCE TABLE - Google Ads Legacy:")
            logger.info("-" * 60)
            
            google_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT customer_id) as customers,
                COUNT(DISTINCT campaign_id) as campaigns,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(COALESCE(cost, cost_micros/1000000)) as total_spend,
                SUM(conversions) as total_conversions
            FROM `{bq_client.project_id}.{bq_client.dataset_id}.campaigns_performance`
            """
            
            google_df = bq_client.query(google_query)
            
            if not google_df.empty:
                row = google_df.iloc[0]
                logger.info(f"  📊 Google Ads Summary:")
                logger.info(f"     Records: {int(row['total_records']):,}")
                logger.info(f"     Customers: {int(row['customers'])}")
                logger.info(f"     Campaigns: {int(row['campaigns'])}")
                logger.info(f"     Date Range: {row['earliest_date']} to {row['latest_date']}")
                logger.info(f"     Spend: ${row['total_spend']:,.2f}")
                logger.info(f"     Clicks: {int(row['total_clicks']):,}")
                logger.info(f"     Conversions: {int(row['total_conversions'])}")
                logger.info("")
        
        # 3. Keywords Performance
        if any(t.table_id == 'keywords_performance' for t in tables):
            logger.info("🔑 KEYWORDS PERFORMANCE TABLE:")
            logger.info("-" * 60)
            
            keywords_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT keyword_text) as unique_keywords,
                COUNT(DISTINCT campaign_id) as campaigns,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(COALESCE(cost, cost_micros/1000000)) as total_spend
            FROM `{bq_client.project_id}.{bq_client.dataset_id}.keywords_performance`
            """
            
            keywords_df = bq_client.query(keywords_query)
            
            if not keywords_df.empty:
                row = keywords_df.iloc[0]
                logger.info(f"  🔑 Keywords Summary:")
                logger.info(f"     Records: {int(row['total_records']):,}")
                logger.info(f"     Unique Keywords: {int(row['unique_keywords']):,}")
                logger.info(f"     Campaigns: {int(row['campaigns'])}")
                logger.info(f"     Date Range: {row['earliest_date']} to {row['latest_date']}")
                logger.info(f"     Spend: ${row['total_spend']:,.2f}")
                logger.info("")
        
        # 4. Check for Google Ads Data Transfer tables (p_*)
        google_transfer_tables = [t for t in tables if t.table_id.startswith('p_')]
        
        if google_transfer_tables:
            logger.info("📡 GOOGLE ADS DATA TRANSFER TABLES:")
            logger.info("-" * 60)
            
            for table in google_transfer_tables:
                logger.info(f"  📊 {table.table_id}")
                logger.info(f"     Rows: {table.num_rows:,}")
                logger.info(f"     Modified: {table.modified}")
        else:
            logger.info("⚠️  NO GOOGLE ADS DATA TRANSFER TABLES FOUND")
            logger.info("   (Expected tables starting with 'p_' from Data Transfer Service)")
        
        # 5. Most recent data across all sources
        logger.info("\n📅 MOST RECENT DATA BY SOURCE:")
        logger.info("-" * 60)
        
        # Check ad_metrics for latest data
        recent_query = f"""
        SELECT 
            platform,
            MAX(date) as latest_date,
            MAX(updated_at) as latest_update,
            COUNT(*) as records_on_latest_date
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
        WHERE date = (SELECT MAX(date) FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics` WHERE platform = ad_metrics.platform)
        GROUP BY platform
        ORDER BY latest_date DESC
        """
        
        recent_df = bq_client.query(recent_query)
        
        for _, row in recent_df.iterrows():
            logger.info(f"  📊 {row['platform'].title()}: Latest data from {row['latest_date']} ({int(row['records_on_latest_date'])} records)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery data audit failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 BigQuery Data Audit")
    print("=" * 60)
    
    success = asyncio.run(audit_bigquery_data())
    
    if success:
        print("=" * 60)
        print("✅ BigQuery data audit completed!")
    else:
        print("=" * 60)
        print("❌ BigQuery data audit failed")
