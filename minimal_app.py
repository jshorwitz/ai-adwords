"""Minimal working dashboard."""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Dashboard home."""
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        if bq_service.is_available():
            kpi_data = await bq_service.get_kpi_summary(90)
            platform_data = await bq_service.get_platform_performance(90)
            
            html = f"""
            <html>
            <head><title>Synter Analytics</title>
            <style>
                body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
                .card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; }}
                .kpi {{ display: inline-block; margin: 10px; text-align: center; background: #e3f2fd; padding: 15px; border-radius: 5px; }}
                .platform {{ border-left: 4px solid #2196f3; margin: 10px 0; }}
            </style>
            </head>
            <body>
                <h1>🚀 Synter Analytics Dashboard</h1>
                
                <div class="card">
                    <h2>📊 Key Performance Indicators</h2>
                    <div class="kpi">
                        <h3>Total Spend</h3>
                        <div style="font-size: 24px; color: #1976d2;">${kpi_data['total_spend']:,.2f}</div>
                    </div>
                    <div class="kpi">
                        <h3>Total Clicks</h3>
                        <div style="font-size: 24px; color: #1976d2;">{kpi_data['total_clicks']:,}</div>
                    </div>
                    <div class="kpi">
                        <h3>Conversions</h3>
                        <div style="font-size: 24px; color: #1976d2;">{kpi_data['total_conversions']:,}</div>
                    </div>
                    <div class="kpi">
                        <h3>Avg CPA</h3>
                        <div style="font-size: 24px; color: #1976d2;">${kpi_data['total_spend']/kpi_data['total_conversions']:.2f}</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🎯 Platform Performance</h2>
                    {''.join([f'''
                    <div class="platform card">
                        <h3>{p['name']}</h3>
                        <p><strong>Spend:</strong> ${p['spend']:,.2f} | <strong>Clicks:</strong> {p['clicks']:,} | <strong>Conversions:</strong> {p['conversions']:,} | <strong>CPA:</strong> ${p['spend']/p['conversions'] if p['conversions'] > 0 else 0:.2f}</p>
                    </div>
                    ''' for p in platform_data])}
                </div>
                
                <div class="card">
                    <h3>🔗 API Endpoints</h3>
                    <p><a href="/api/data">JSON Data API</a> | <a href="/docs">FastAPI Docs</a> | <a href="/health">Health Check</a></p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(html)
        else:
            return HTMLResponse("<h1>❌ BigQuery Not Available</h1>")
            
    except Exception as e:
        return HTMLResponse(f"<h1>❌ Error: {e}</h1>")

@app.get("/api/data")
async def api_data():
    try:
        from src.services.bigquery_service import get_bigquery_service
        bq_service = get_bigquery_service()
        
        kpi_data = await bq_service.get_kpi_summary(90)
        platform_data = await bq_service.get_platform_performance(90)
        
        return {"kpis": kpi_data, "platforms": platform_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Minimal Dashboard Starting...")
    print("📊 Dashboard: http://localhost:8081")
    uvicorn.run(app, host="0.0.0.0", port=8081)
