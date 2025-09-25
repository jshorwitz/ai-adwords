#!/usr/bin/env python3
"""Minimal FastAPI app for Synter deployment."""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="Synter - AI Advertising Agency",
    description="Cross-channel ads management with AI agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Homepage with Synter branding."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Synter - AI Advertising Agency</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                margin: 0; padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; min-height: 100vh;
                display: flex; align-items: center; justify-content: center;
            }
            .container { text-align: center; max-width: 800px; }
            h1 { font-size: 3rem; margin-bottom: 1rem; }
            p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }
            .status { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Synter</h1>
            <p>The AI Advertising Agency</p>
            <div class="status">
                <h3>✅ Deployment Successful!</h3>
                <p>Cross-channel ads management with AI agents</p>
                <p>Google Ads • Reddit Ads • X/Twitter Ads</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "synter"}

@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "service": "Synter - AI Advertising Agency",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
