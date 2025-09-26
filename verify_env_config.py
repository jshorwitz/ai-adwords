"""Verify environment configuration after .env update."""

import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_env_config():
    """Verify environment configuration is correct."""
    logger.info("🔍 Verifying Environment Configuration")
    logger.info("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check BigQuery configuration
    logger.info("📊 BigQuery Configuration:")
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET_ID")
    credentials_path = os.getenv("BIGQUERY_CREDENTIALS_PATH")
    
    logger.info(f"  Project ID: {project_id}")
    logger.info(f"  Dataset ID: {dataset_id}")
    logger.info(f"  Credentials: {'SET' if credentials_path else 'Using default'}")
    
    # Verify correct dataset
    if dataset_id == "synter_analytics":
        logger.info("  ✅ Correct dataset configured")
    elif dataset_id == "google_ads_data":
        logger.warning("  ⚠️  Still using old google_ads_data dataset")
        logger.info("  💡 Please update BIGQUERY_DATASET_ID=synter_analytics in .env")
    else:
        logger.warning(f"  ⚠️  Unexpected dataset: {dataset_id}")
    
    # Check Microsoft Ads configuration
    logger.info("\n🔧 Microsoft Ads Configuration:")
    ms_token = os.getenv("MICROSOFT_ADS_DEVELOPER_TOKEN")
    ms_client_id = os.getenv("MICROSOFT_ADS_CLIENT_ID")
    ms_mock = os.getenv("MOCK_MICROSOFT", "true").lower()
    
    logger.info(f"  Developer Token: {'SET' if ms_token else 'NOT SET'}")
    logger.info(f"  Client ID: {'SET' if ms_client_id else 'NOT SET'}")
    logger.info(f"  Mock Mode: {ms_mock}")
    
    if ms_token == "11085M29YT845526":
        logger.info("  ✅ Microsoft API key configured")
    else:
        logger.warning("  ⚠️  Microsoft API key missing or incorrect")
    
    # Check other platform mock settings
    logger.info("\n🎭 Mock Data Settings:")
    linkedin_mock = os.getenv("MOCK_LINKEDIN", "true").lower()
    reddit_mock = os.getenv("MOCK_REDDIT", "true").lower()
    
    logger.info(f"  LinkedIn Mock: {linkedin_mock}")
    logger.info(f"  Reddit Mock: {reddit_mock}")
    
    # Test BigQuery connection with current config
    logger.info("\n🔍 Testing BigQuery Connection...")
    
    try:
        from src.ads.bigquery_client import create_bigquery_client_from_env
        
        bq_client = create_bigquery_client_from_env()
        
        logger.info(f"✅ Connected to {bq_client.project_id}.{bq_client.dataset_id}")
        
        # Quick query test
        test_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT platform) as platforms
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.ad_metrics`
        """
        
        result_df = bq_client.query(test_query)
        
        if not result_df.empty:
            row = result_df.iloc[0]
            logger.info(f"📊 Data Available: {int(row['total_rows'])} rows across {int(row['platforms'])} platforms")
        else:
            logger.info("📊 No data in ad_metrics table")
            
    except Exception as e:
        logger.error(f"❌ BigQuery connection failed: {e}")
        logger.info("💡 Check your service account credentials and dataset access")
    
    # Configuration summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 Configuration Summary:")
    
    config_correct = True
    
    if dataset_id != "synter_analytics":
        logger.warning("⚠️  Dataset needs to be updated to synter_analytics")
        config_correct = False
    
    if not ms_token:
        logger.warning("⚠️  Microsoft Ads developer token not configured")
        config_correct = False
    
    if config_correct:
        logger.info("✅ Environment configuration is correct!")
        logger.info("🚀 Ready to use synter_analytics dataset")
    else:
        logger.warning("⚠️  Environment configuration needs updates")
        logger.info("📝 See update_env_instructions.md for guidance")

if __name__ == "__main__":
    verify_env_config()
