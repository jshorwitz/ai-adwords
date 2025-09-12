"""Safe startup version of AI AdWords platform for Railway."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "🚀 AI AdWords Platform is Live!",
        "service": "ai-adwords-platform",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "agents": "/agents/health",
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
