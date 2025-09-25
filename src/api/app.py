"""Main FastAPI application - unified ads platform with agent orchestration."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

from ..models.database import create_tables
from .auth_routes import router as auth_router
from .agent_routes import router as agent_router
from .dashboard_routes import router as dashboard_router
from .onboarding_routes import router as onboarding_router
from .debug_routes import router as debug_router
from .microsoft_oauth_routes import router as microsoft_oauth_router

# Get the root directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Set up templates and static files
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = str(BASE_DIR / "static")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting AI AdWords unified ads platform")
    
    # Log environment info for debugging
    import os
    logger.info(f"🔧 PORT: {os.getenv('PORT', 'not set')}")
    logger.info(f"🔧 HOST: {os.getenv('HOST', 'not set')}")
    logger.info(f"🔧 DATABASE_URL: {'set' if os.getenv('DATABASE_URL') else 'not set'}")
    
    # Import agents to register them (safe operation)
    try:
        from ..agents import ingestors, transforms, activations, decisions
        from ..agents.runner import agent_registry
        
        agent_count = len(agent_registry.list_agents())
        logger.info(f"🤖 Registered {agent_count} agents")
    except Exception as e:
        logger.warning(f"⚠️ Agent registration failed: {e}")
    
    # Database initialization (non-blocking, can fail)
    try:
        await create_tables()
        logger.info("📊 Database tables created/verified")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization failed (will retry): {e}")
    
    logger.info("✅ Application startup complete")
    yield
    
    # Shutdown
    logger.info("⏹️ Shutting down AI AdWords platform")


# Create FastAPI application
app = FastAPI(
    title="Synter - AI Advertising Agency",
    description="Cross-channel ads management with autonomous agents for Google Ads, Reddit Ads, and X/Twitter Ads",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(dashboard_router)
app.include_router(onboarding_router)
app.include_router(debug_router)
app.include_router(microsoft_oauth_router)


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Serve the marketing homepage."""
    return templates.TemplateResponse("homepage.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the protected dashboard (authentication will be handled by frontend JS).""" 
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request):
    """Serve the onboarding page."""
    return templates.TemplateResponse("onboarding.html", {"request": request})


@app.get("/health")
async def health_check():
    """Application health check."""
    try:
        # Basic health check that always works
        import time
        return {
            "status": "healthy",
            "service": "ai-adwords-platform",
            "timestamp": int(time.time()),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }

@app.get("/health/full")
async def full_health_check():
    """Full health check including agents and database."""
    try:
        from ..agents.runner import agent_registry
        
        return {
            "status": "healthy",
            "service": "ai-adwords-platform",
            "agents_registered": len(agent_registry.list_agents()),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return {
        "error": "Not found",
        "detail": f"Path {request.url.path} not found",
        "available_endpoints": [
            "/auth/*", "/agents/*", "/docs", "/health"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
