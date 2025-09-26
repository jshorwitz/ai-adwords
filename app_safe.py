"""Safe startup version of Snyter - The AI Advertising Agency for Railway."""

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
    logger.info("🚀 Starting Snyter - The AI Advertising Agency")
    
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
    title="Snyter - The AI Advertising Agency",
    description="AI specialists for cross-channel ads management with autonomous optimization",
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


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_flow(request: Request):
    """One-field onboarding flow for instant ad insights."""
    try:
        return templates.TemplateResponse("onboarding.html", {"request": request})
    except Exception as e:
        logger.error(f"Failed to render onboarding: {e}")
        return HTMLResponse(content=f"<h1>Onboarding Error: {e}</h1>", status_code=500)


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
        "message": "🚀 Snyter - The AI Advertising Agency API",
        "service": "snyter-platform",
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
        "service": "snyter-platform",
        "database": "connected" if os.getenv("DATABASE_URL") else "not configured"
    }


@app.get("/data-sources")
async def data_sources_status():
    """Get status of all data sources and integrations."""
    try:
        from src.intelligence.data_sources import data_sources, validate_environment_setup
        
        return {
            "data_sources": data_sources.get_data_source_status(),
            "environment_setup": validate_environment_setup(),
            "integration_health": "operational"
        }
    except Exception as e:
        logger.warning(f"Data sources status failed: {e}")
        return {
            "error": "Data sources status unavailable",
            "integration_health": "limited"
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


# Include auth routes (simplified for demo)
try:
    from src.api.auth_simple import router as auth_router
    app.include_router(auth_router)
    logger.info("✅ Simplified auth routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Auth routes failed to load: {e}")

# Include OAuth routes  
try:
    from src.api.oauth_routes import router as oauth_router
    app.include_router(oauth_router)
    logger.info("✅ OAuth routes loaded")
except Exception as e:
    logger.warning(f"⚠️ OAuth routes failed to load: {e}")

# Include LinkedIn OAuth routes
try:
    from src.api.linkedin_oauth_routes import router as linkedin_oauth_router
    app.include_router(linkedin_oauth_router)
    logger.info("✅ LinkedIn OAuth routes loaded")
except Exception as e:
    logger.warning(f"⚠️ LinkedIn OAuth routes failed to load: {e}")

# Include Reddit OAuth routes
try:
    from src.api.reddit_oauth_routes import router as reddit_oauth_router
    app.include_router(reddit_oauth_router)
    logger.info("✅ Reddit OAuth routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Reddit OAuth routes failed to load: {e}")

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

# Include platform status routes
try:
    from src.api.platform_status_routes import router as platform_status_router
    app.include_router(platform_status_router)
    logger.info("✅ Platform status routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Platform status routes failed to load: {e}")

# Include onboarding routes (safe)
try:
    from src.api.onboarding_routes import router as onboarding_router
    app.include_router(onboarding_router)
    logger.info("✅ Onboarding routes loaded")
except Exception as e:
    logger.warning(f"⚠️ Onboarding routes failed to load: {e}")

# Include AI agency routes (safe)
try:
    from src.api.ai_agency_routes import router as ai_agency_router
    app.include_router(ai_agency_router)
    logger.info("✅ AI Agency routes loaded")
except Exception as e:
    logger.warning(f"⚠️ AI Agency routes failed to load: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
