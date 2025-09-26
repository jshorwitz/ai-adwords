"""Simple dashboard start without complex async operations."""

import os
import sys
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Create simple FastAPI app
app = FastAPI(title="Synter Analytics Dashboard", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    
    # Get real data from BigQuery
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        print(f"BigQuery available: {bq_service.is_available()}")
        
        if bq_service.is_available():
            print("Getting KPI data...")
            kpi_data = await bq_service.get_kpi_summary(90)
            print(f"KPI data: {kpi_data}")
            
            print("Getting platform data...")
            platform_data = await bq_service.get_platform_performance(90)
            print(f"Platform data: {len(platform_data)} platforms")
            
            # Create simple HTML response
            platform_html = ""
            total_spend = 0
            
            for platform in platform_data:
                total_spend += platform['spend']
                platform_html += f"""
                <div style="border: 1px solid #ccc; margin: 10px; padding: 15px; border-radius: 5px;">
                    <h3>{platform['name']}</h3>
                    <p><strong>Spend:</strong> ${platform['spend']:,.2f}</p>
                    <p><strong>Clicks:</strong> {platform['clicks']:,}</p>
                    <p><strong>Conversions:</strong> {platform['conversions']:,}</p>
                    <p><strong>CPA:</strong> ${platform['spend']/platform['conversions'] if platform['conversions'] > 0 else 0:.2f}</p>
                </div>
                """
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Synter Analytics Dashboard</title>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                        .header {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                        .kpi-container {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                        .kpi-card {{ background: white; padding: 20px; border-radius: 10px; flex: 1; text-align: center; }}
                        .kpi-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
                        .platform-container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                        .status {{ background: #10b981; color: white; padding: 5px 10px; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🚀 Synter Analytics Dashboard</h1>
                        <p><span class="status">✅ Live BigQuery Data</span> | Last Updated: {kpi_data.get('last_updated', 'Just now')}</p>
                    </div>
                    
                    <div class="kpi-container">
                        <div class="kpi-card">
                            <h3>Total Spend</h3>
                            <div class="kpi-value">${kpi_data['total_spend']:,.0f}</div>
                        </div>
                        <div class="kpi-card">
                            <h3>Total Clicks</h3>
                            <div class="kpi-value">{kpi_data['total_clicks']:,}</div>
                        </div>
                        <div class="kpi-card">
                            <h3>Conversions</h3>
                            <div class="kpi-value">{kpi_data['total_conversions']:,}</div>
                        </div>
                        <div class="kpi-card">
                            <h3>Avg CPA</h3>
                            <div class="kpi-value">${kpi_data['total_spend']/kpi_data['total_conversions']:.2f}</div>
                        </div>
                    </div>
                    
                    <h2>Platform Performance</h2>
                    <div class="platform-container">
                        {platform_html}
                    </div>
                    
                    <p style="margin-top: 30px; text-align: center; color: #666;">
                        🔗 <a href="/api/data">View Raw JSON Data</a> | 
                        <a href="/api/daily-breakdown">Daily Breakdown</a> | 
                        <a href="/docs">API Documentation</a>
                    </p>
                </body>
            </html>
            """
            
            return HTMLResponse(content=html_content)
        else:
            return HTMLResponse("""
            <html>
                <head><title>Dashboard Error</title></head>
                <body>
                    <h1>❌ BigQuery Connection Failed</h1>
                    <p>Unable to connect to BigQuery. Check your credentials.</p>
                </body>
            </html>
            """)
    
    except Exception as e:
        error_html = f"""
        <html>
            <head><title>Dashboard Error</title></head>
            <body>
                <h1>❌ Dashboard Error</h1>
                <p><strong>Error:</strong> {e}</p>
                <pre style="background: #f0f0f0; padding: 10px; margin: 10px 0;">{traceback.format_exc()}</pre>
                <p><a href="/health">Check Health</a></p>
            </body>
        </html>
        """
        return HTMLResponse(content=error_html)

@app.get("/api/data")
async def get_api_data():
    """Get dashboard data as JSON."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if bq_service.is_available():
            kpi_data = await bq_service.get_kpi_summary(90)
            platform_data = await bq_service.get_platform_performance(90)
            
            return {
                "kpis": kpi_data,
                "platforms": platform_data,
                "connected": True,
                "total_platforms": len(platform_data)
            }
        else:
            return {"error": "BigQuery not available", "connected": False}
            
    except Exception as e:
        return {"error": f"API error: {e}", "traceback": traceback.format_exc()}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        return {
            "status": "healthy",
            "bigquery_available": bq_service.is_available(),
            "dataset": bq_service.bq_client.dataset_id if bq_service.is_available() else "unknown"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Simple Debug Dashboard...")
    print("📊 Available at: http://localhost:8081")
    print("🔧 Debug endpoints:")
    print("  - / (main dashboard)")
    print("  - /api/data (JSON data)")
    print("  - /health (health check)")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8081,
        log_level="debug"
    )
