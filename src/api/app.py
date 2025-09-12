"""Main FastAPI application - unified ads platform with agent orchestration."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ..models.database import create_tables
from .auth_routes import router as auth_router
from .agent_routes import router as agent_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting AI AdWords unified ads platform")
    
    # Create database tables
    try:
        await create_tables()
        logger.info("📊 Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Import agents to register them
    try:
        from ..agents import ingestors, transforms, activations, decisions
        from ..agents.runner import agent_registry
        
        agent_count = len(agent_registry.list_agents())
        logger.info(f"🤖 Registered {agent_count} agents")
    except Exception as e:
        logger.error(f"❌ Agent registration failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("⏹️ Shutting down AI AdWords platform")


# Create FastAPI application
app = FastAPI(
    title="AI AdWords - Unified Ads Platform",
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


# Include routers
app.include_router(auth_router)
app.include_router(agent_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with platform overview."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI AdWords - Unified Ads Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; }
            .endpoint { background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px; }
            .agent { background: #e8f0ff; padding: 10px; margin: 5px 0; border-radius: 3px; }
            code { background: #f0f0f0; padding: 2px 5px; border-radius: 2px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 AI AdWords - Unified Ads Platform</h1>
            <p>Cross-channel ads management with autonomous agents for Google Ads, Reddit Ads, and X/Twitter Ads</p>
        </div>
        
        <div class="section">
            <h2>🔐 Authentication</h2>
            <div class="endpoint">POST /auth/signup - Create user account</div>
            <div class="endpoint">POST /auth/login - Login with email/password</div>
            <div class="endpoint">POST /auth/magic-link - Send magic link</div>
            <div class="endpoint">GET /auth/me - Get current user</div>
            <div class="endpoint">POST /auth/logout - Logout</div>
        </div>
        
        <div class="section">
            <h2>🤖 Agent Management</h2>
            <div class="endpoint">GET /agents/list - List available agents</div>
            <div class="endpoint">POST /agents/run - Execute agent job</div>
            <div class="endpoint">GET /agents/status - View agent runs</div>
            <div class="endpoint">GET /agents/health - System health check</div>
        </div>
        
        <div class="section">
            <h2>🔧 Available Agents</h2>
            <div class="agent"><strong>ingestor-google</strong> - Pull Google Ads metrics via GAQL</div>
            <div class="agent"><strong>ingestor-reddit</strong> - Pull Reddit Ads metrics (mockable)</div>
            <div class="agent"><strong>ingestor-x</strong> - Pull X/Twitter Ads metrics (mockable)</div>
            <div class="agent"><strong>touchpoint-extractor</strong> - Extract touchpoints from events</div>
            <div class="agent"><strong>conversion-uploader</strong> - Upload conversions to platforms</div>
            <div class="agent"><strong>budget-optimizer</strong> - Optimize campaign budgets based on CAC/ROAS</div>
            <div class="agent"><strong>keywords-hydrator</strong> - Enrich keywords from external APIs</div>
        </div>
        
        <div class="section">
            <h2>📖 API Documentation</h2>
            <p>Visit <a href="/docs">/docs</a> for interactive API documentation</p>
            <p>Visit <a href="/redoc">/redoc</a> for ReDoc documentation</p>
        </div>
        
        <div class="section">
            <h2>🎯 Quick Start</h2>
            <p>1. <code>POST /auth/signup</code> to create an account</p>
            <p>2. <code>POST /auth/login</code> to authenticate</p>
            <p>3. <code>GET /agents/list</code> to see available agents</p>
            <p>4. <code>POST /agents/run</code> with <code>{"agent": "budget-optimizer", "dry_run": true}</code></p>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Application health check."""
    from ..agents.runner import agent_registry
    
    return {
        "status": "healthy",
        "service": "ai-adwords-platform",
        "agents_registered": len(agent_registry.list_agents()),
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
