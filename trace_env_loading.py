"""Trace where environment variables are being loaded from."""

import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trace_env_loading():
    """Trace environment variable loading and .env file locations."""
    logger.info("🔍 Tracing Environment Variable Loading")
    logger.info("=" * 70)
    
    # Check current working directory
    logger.info(f"📁 Current Working Directory: {os.getcwd()}")
    
    # Find all .env files in the workspace
    logger.info("\n📋 Found .env files:")
    
    workspace_root = "/Users/joelhorwitz/dev/synter"
    env_files = []
    
    for root, dirs, files in os.walk(workspace_root):
        if '.env' in files:
            env_file = os.path.join(root, '.env')
            env_files.append(env_file)
            logger.info(f"  📄 {env_file}")
    
    # Check each .env file for BigQuery configuration
    logger.info("\n🔍 Checking BigQuery configuration in each .env file:")
    
    for env_file in env_files:
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            logger.info(f"\n📄 {env_file}:")
            
            # Look for BigQuery settings
            if 'BIGQUERY_DATASET_ID' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'BIGQUERY_DATASET_ID' in line and not line.strip().startswith('#'):
                        logger.info(f"  🎯 {line.strip()}")
            else:
                logger.info("  ❌ No BIGQUERY_DATASET_ID found")
                
            if 'BIGQUERY_PROJECT_ID' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'BIGQUERY_PROJECT_ID' in line and not line.strip().startswith('#'):
                        logger.info(f"  🎯 {line.strip()}")
            
        except Exception as e:
            logger.warning(f"  ❌ Could not read file: {e}")
    
    # Test dotenv loading from different locations
    logger.info("\n🔧 Testing dotenv loading from different locations:")
    
    from dotenv import load_dotenv
    
    # Test loading from current directory
    current_dir_env = os.path.join(os.getcwd(), '.env')
    if os.path.exists(current_dir_env):
        logger.info(f"📁 Loading from current directory: {current_dir_env}")
        load_dotenv(current_dir_env, override=True)
        dataset_from_current = os.getenv('BIGQUERY_DATASET_ID')
        logger.info(f"  Result: BIGQUERY_DATASET_ID={dataset_from_current}")
    else:
        logger.info(f"📁 No .env file in current directory: {os.getcwd()}")
    
    # Test loading from ai-adwords directory
    ai_adwords_env = "/Users/joelhorwitz/dev/synter/ai-adwords/.env"
    if os.path.exists(ai_adwords_env):
        logger.info(f"📁 Loading from ai-adwords: {ai_adwords_env}")
        load_dotenv(ai_adwords_env, override=True)
        dataset_from_ai_adwords = os.getenv('BIGQUERY_DATASET_ID')
        logger.info(f"  Result: BIGQUERY_DATASET_ID={dataset_from_ai_adwords}")
    else:
        logger.info(f"📁 No .env file at: {ai_adwords_env}")
    
    # Check how BigQuery client loads configuration
    logger.info("\n🔧 Checking BigQuery client configuration loading:")
    
    try:
        # Reset environment
        if 'BIGQUERY_DATASET_ID' in os.environ:
            del os.environ['BIGQUERY_DATASET_ID']
        
        # Load from ai-adwords .env
        load_dotenv("/Users/joelhorwitz/dev/synter/ai-adwords/.env")
        
        from src.ads.bigquery_client import create_bigquery_client_from_env
        
        bq_client = create_bigquery_client_from_env()
        
        logger.info(f"📊 BigQuery Client Configuration:")
        logger.info(f"  Project: {bq_client.project_id}")
        logger.info(f"  Dataset: {bq_client.dataset_id}")
        
        # Check if it's using hardcoded values
        logger.info("\n🔍 Checking for hardcoded values in BigQuery client...")
        
    except Exception as e:
        logger.error(f"❌ Error checking BigQuery client: {e}")
    
    # Check environment variables currently set
    logger.info("\n🌍 Current Environment Variables:")
    logger.info(f"  BIGQUERY_DATASET_ID: {os.getenv('BIGQUERY_DATASET_ID', 'NOT SET')}")
    logger.info(f"  BIGQUERY_PROJECT_ID: {os.getenv('BIGQUERY_PROJECT_ID', 'NOT SET')}")
    logger.info(f"  GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")

if __name__ == "__main__":
    trace_env_loading()
