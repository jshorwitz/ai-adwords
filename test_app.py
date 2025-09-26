"""Test app to verify BigQuery connection locally vs production."""

import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.append("src")

async def test_bigquery_connection():
    """Test BigQuery connection and data retrieval."""
    try:
        print("🔍 Testing BigQuery Connection")
        print("=" * 50)
        
        # Check environment variables
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        dataset_id = os.getenv("BIGQUERY_DATASET_ID") 
        credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        print(f"📊 Environment Configuration:")
        print(f"  GOOGLE_CLOUD_PROJECT: {project_id}")
        print(f"  BIGQUERY_DATASET_ID: {dataset_id}")
        print(f"  GOOGLE_APPLICATION_CREDENTIALS: {'SET' if credentials else 'NOT SET'}")
        
        if credentials and os.path.exists(credentials):
            print(f"  Credentials file exists: ✅")
        elif credentials:
            print(f"  Credentials: JSON content (Railway style)")
        
        # Test BigQuery service
        from src.services.bigquery_service import get_bigquery_service
        
        bq_service = get_bigquery_service()
        print(f"\n📊 BigQuery Service:")
        print(f"  Available: {bq_service.is_available()}")
        
        if bq_service.is_available():
            print(f"  Project: {bq_service.bq_client.project_id}")
            print(f"  Dataset: {bq_service.bq_client.dataset_id}")
            
            # Test data retrieval
            print(f"\n🔍 Testing Data Retrieval:")
            
            kpi_data = await bq_service.get_kpi_summary(90)
            print(f"  KPI Data: {'✅ SUCCESS' if kpi_data else '❌ FAILED'}")
            
            if kpi_data:
                print(f"    Total Spend: ${kpi_data['total_spend']:,.2f}")
                print(f"    Total Conversions: {kpi_data['total_conversions']:,}")
            
            platform_data = await bq_service.get_platform_performance(90)
            print(f"  Platform Data: {'✅ SUCCESS' if platform_data else '❌ FAILED'}")
            
            if platform_data:
                print(f"    Platforms Found: {len(platform_data)}")
                for p in platform_data:
                    print(f"      {p['name']}: ${p['spend']:,.2f} spend")
        else:
            print("  ❌ BigQuery service not available")
            
            # Try to understand why
            try:
                from src.ads.bigquery_client import create_bigquery_client_from_env
                bq_client = create_bigquery_client_from_env()
                print(f"  Direct client project: {bq_client.project_id}")
                print(f"  Direct client dataset: {bq_client.dataset_id}")
            except Exception as e:
                print(f"  Direct client error: {e}")
        
        return bq_service.is_available()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bigquery_connection())
    
    print("=" * 50)
    if success:
        print("✅ BigQuery connection test successful!")
    else:
        print("❌ BigQuery connection test failed!")
        print("💡 For Railway deployment, ensure GOOGLE_APPLICATION_CREDENTIALS")
        print("   contains the full JSON content as environment variable")
