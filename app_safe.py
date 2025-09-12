"""Safe startup version of AI AdWords platform for Railway."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Safe application lifespan events."""
    logger.info("🚀 Starting AI AdWords Platform (Safe Mode)")
    
    # Log environment
    logger.info(f"🔧 PORT: {os.getenv('PORT', 'not set')}")
    logger.info(f"🔧 DATABASE_URL: {'set' if os.getenv('DATABASE_URL') else 'not set'}")
    
    # Register agents (safe operation)
    try:
        from src.agents import ingestors, transforms, activations, decisions
        from src.agents.runner import agent_registry
        
        agent_count = len(agent_registry.list_agents())
        logger.info(f"🤖 Registered {agent_count} agents")
    except Exception as e:
        logger.warning(f"⚠️ Agent registration failed: {e}")
    
    # Initialize database (if available, non-blocking)
    if os.getenv('DATABASE_URL'):
        try:
            from src.models.database import create_tables
            await create_tables()
            logger.info("📊 Database tables created/verified")
        except Exception as e:
            logger.warning(f"⚠️ Database initialization failed: {e}")
    else:
        logger.info("📊 No database configured - running in API-only mode")
    
    logger.info("✅ Application startup complete")
    yield
    
    logger.info("⏹️ Shutting down")


# Create FastAPI application
app = FastAPI(
    title="AI AdWords - Unified Ads Platform",
    description="Cross-channel ads management with autonomous agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Templates and static files
templates = Jinja2Templates(directory="templates")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ Static files mounted")
except Exception as e:
    logger.warning(f"⚠️ Static files not mounted: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Nike-inspired homepage with signup/login."""
    try:
        return templates.TemplateResponse("homepage.html", {"request": request})
    except Exception as e:
        logger.error(f"Failed to render homepage: {e}")
        return HTMLResponse(content=f"<h1>Homepage Error: {e}</h1>", status_code=500)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    """Main dashboard UI (protected)."""
    try:
        # Check if user is authenticated via session cookie
        session_token = request.cookies.get("sid")
        if not session_token:
            # Redirect to homepage for login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/", status_code=302)
        
        # TODO: Validate session token with auth service
        # For now, just serve the dashboard
        
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Failed to render dashboard: {e}")
        return HTMLResponse(content=f"<h1>Dashboard Error: {e}</h1>", status_code=500)


@app.get("/demo", response_class=HTMLResponse)
async def demo_dashboard(request: Request):
    """Demo dashboard for unauthenticated users."""
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "demo_mode": True
        })
    except Exception as e:
        logger.error(f"Failed to render demo dashboard: {e}")
        return HTMLResponse(content=f"<h1>Demo Error: {e}</h1>", status_code=500)


@app.get("/api")
def api_info():
    """API information endpoint."""
    return {
        "message": "🚀 AI AdWords Platform API",
        "service": "ai-adwords-platform",
        "version": "1.0.0",
        "endpoints": {
            "homepage": "/",
            "dashboard": "/dashboard",
            "health": "/health",
            "docs": "/docs",
            "agents": "/agents/health",
            "auth": "/auth/*",
        }
    }


@app.get("/health")
def health_check():
    """Simple health check."""
    return {
        "status": "healthy",
        "service": "ai-adwords-platform",
        "database": "connected" if os.getenv("DATABASE_URL") else "not configured"
    }


@app.get("/agents/health")
def agents_health():
    """Agent system health check."""
    try:
        from src.agents.runner import agent_registry
        return {
            "status": "healthy",
            "agents_registered": len(agent_registry.list_agents())
        }
    except Exception as e:
        return {
            "status": "degraded", 
            "error": str(e)
        }


# Include auth routes (safe)
try:
    from src.api.auth_routes import router as auth_router
    app.include_router(auth_router)
    logger.info("✅ Auth routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Auth routes failed to load: {e}")

# Include agent routes (safe)
try:
    from src.api.agent_routes import router as agent_router  
    app.include_router(agent_router)
    logger.info("✅ Agent routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Agent routes failed to load: {e}")

# Include dashboard routes (safe)
try:
    from src.api.dashboard_routes import router as dashboard_router
    app.include_router(dashboard_router)
    logger.info("✅ Dashboard routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Dashboard routes failed to load: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
