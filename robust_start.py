#!/usr/bin/env python3
"""Robust startup script that handles database failures gracefully."""

import os
import sys
import logging
import asyncio
from typing import Optional
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Global variables
app = None
db_connected = False

def create_app() -> FastAPI:
    """Create FastAPI app with or without database."""
    
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
    
    return app

def setup_basic_routes(app: FastAPI, db_status: str):
    """Setup basic routes that work with or without database."""
    
    @app.get("/", response_class=HTMLResponse)
    async def homepage():
        """Homepage with Synter branding and status."""
        db_indicator = "🟢" if db_connected else "🟡"
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Synter - AI Advertising Agency</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                    margin: 0; padding: 40px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; min-height: 100vh;
                    display: flex; align-items: center; justify-content: center;
                }}
                .container {{ text-align: center; max-width: 800px; }}
                h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
                p {{ font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; }}
                .status {{ background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .debug {{ background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; font-size: 0.9rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Synter</h1>
                <p>The AI Advertising Agency</p>
                <div class="status">
                    <h3>✅ Service Running</h3>
                    <p>Cross-channel ads management with AI agents</p>
                    <p>Google Ads • Reddit Ads • X/Twitter Ads</p>
                </div>
                <div class="debug">
                    <h4>System Status</h4>
                    <p>{db_indicator} Database: {db_status}</p>
                    <p>🐍 Python: {sys.version.split()[0]}</p>
                    <p>🌐 Port: {os.getenv('PORT', '8000')}</p>
                </div>
            </div>
        </body>
        </html>
        """

    @app.get("/health")
    async def health_check():
        """Health check endpoint - always returns healthy if app is running."""
        return {
            "status": "healthy", 
            "service": "synter",
            "database": "connected" if db_connected else "disconnected"
        }

    @app.get("/api/status")
    async def api_status():
        """API status endpoint."""
        return {
            "service": "Synter - AI Advertising Agency",
            "status": "running",
            "version": "1.0.0",
            "database_connected": db_connected,
            "database_status": db_status
        }

async def try_database_connection() -> tuple[bool, str]:
    """Try to connect to database, return status."""
    global db_connected
    
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return False, "DATABASE_URL not set"
        
        logger.info("🔍 Attempting database connection...")
        
        # Try importing database modules
        try:
            from ..models.database import create_tables
            await create_tables()
            db_connected = True
            logger.info("✅ Database connected successfully")
            return True, "Connected successfully"
        except Exception as db_err:
            logger.warning(f"⚠️ Database connection failed: {db_err}")
            return False, f"Connection failed: {str(db_err)[:50]}..."
            
    except Exception as e:
        logger.warning(f"⚠️ Database setup failed: {e}")
        return False, f"Setup failed: {str(e)[:50]}..."

def main():
    """Main startup function with graceful database handling."""
    
    logger.info("🚀 Starting Synter - AI Advertising Agency")
    
    # Set defaults
    if not os.getenv("SECRET_KEY"):
        import secrets
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)
        logger.info("🔑 Generated temporary secret key")
    
    # Try database connection
    try:
        connected, status = asyncio.run(try_database_connection())
        logger.info(f"📊 Database status: {status}")
    except Exception as e:
        connected, status = False, f"Connection attempt failed: {e}"
        logger.warning(f"📊 Database status: {status}")
    
    # Create app
    app = create_app()
    setup_basic_routes(app, status)
    
    # Try to import full routes if database is connected
    if connected:
        try:
            logger.info("🔌 Loading full application with database features...")
            from ..api.auth_routes import router as auth_router
            from ..api.agent_routes import router as agent_router
            app.include_router(auth_router)
            app.include_router(agent_router)
            logger.info("✅ Full application routes loaded")
        except Exception as e:
            logger.warning(f"⚠️ Could not load full routes: {e}")
            logger.info("📱 Running in basic mode")
    else:
        logger.info("📱 Running in basic mode (no database)")
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    
    # Start the server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True,
        )
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
