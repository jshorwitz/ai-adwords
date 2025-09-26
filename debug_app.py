"""Debug version of the dashboard to identify the issue."""

import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import asyncio
import traceback

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Setup
app = FastAPI(title="Debug Dashboard", version="1.0.0")

# Test if templates work
try:
    templates = Jinja2Templates(directory="src/dashboard/templates")
    templates_working = True
except Exception as e:
    print(f"Template error: {e}")
    templates_working = False

@app.get("/")
async def debug_home():
    """Debug homepage."""
    try:
        return {"message": "Dashboard debug endpoint working", "templates": templates_working}
    except Exception as e:
        return {"error": f"Debug home error: {e}"}

@app.get("/test-bigquery")
async def test_bigquery():
    """Test BigQuery connection."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if not bq_service.is_available():
            return {"error": "BigQuery service not available"}
        
        # Test a simple query
        kpi_data = await bq_service.get_kpi_summary(30)
        
        return {
            "success": True,
            "project": bq_service.bq_client.project_id,
            "dataset": bq_service.bq_client.dataset_id,
            "kpi_data": kpi_data
        }
        
    except Exception as e:
        return {"error": f"BigQuery test failed: {e}", "traceback": traceback.format_exc()}

@app.get("/simple", response_class=HTMLResponse)
async def simple_page(request: Request):
    """Simple HTML page without complex data."""
    try:
        if not templates_working:
            return HTMLResponse("""
            <html>
                <head><title>Simple Dashboard</title></head>
                <body>
                    <h1>Synter Analytics Dashboard (Simple)</h1>
                    <p>Templates not working, showing basic HTML</p>
                    <p><a href="/test-bigquery">Test BigQuery</a></p>
                </body>
            </html>
            """)
        
        simple_data = {
            "title": "Simple Dashboard",
            "data": {
                "kpis": {"total_spend": 100000, "total_clicks": 10000, "total_conversions": 500, "total_impressions": 200000, "avg_ctr": 5.0, "avg_cpc": 10.0},
                "platforms": [
                    {"name": "Test Platform", "spend": 100000, "clicks": 10000, "conversions": 500, "cpa": 200, "status": "Active"}
                ],
                "connected": False,
                "last_updated": "Test data"
            }
        }
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            **simple_data
        })
        
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>Dashboard Error</title></head>
            <body>
                <h1>Dashboard Error</h1>
                <p>Error: {e}</p>
                <pre>{traceback.format_exc()}</pre>
            </body>
        </html>
        """)

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "templates": templates_working}

if __name__ == "__main__":
    print("🚀 Starting Debug Dashboard...")
    print("📊 Debug endpoints:")
    print("  - http://localhost:8080/ (basic JSON)")
    print("  - http://localhost:8080/simple (simple HTML)")
    print("  - http://localhost:8080/test-bigquery (BigQuery test)")
    print("  - http://localhost:8080/health (health check)")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
