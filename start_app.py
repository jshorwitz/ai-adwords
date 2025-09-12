"""Startup script for AI AdWords unified ads platform."""

import asyncio
import logging
import os
import sys

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def check_environment():
    """Check required environment variables and dependencies."""
    
    logger.info("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        logger.error("❌ Python 3.11+ required")
        return False
    
    # Set default database URL if not provided
    if not os.getenv("DATABASE_URL"):
        default_db_url = "postgresql://ads_user:ads_pass@localhost:5432/ai_adwords"
        os.environ["DATABASE_URL"] = default_db_url
        logger.info(f"📝 Using default database URL: {default_db_url}")
    
    # Set default secret key if not provided
    if not os.getenv("SECRET_KEY"):
        import secrets
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)
        logger.warning("⚠️  Using generated secret key (set SECRET_KEY env var for production)")
    
    logger.info("✅ Environment check passed")
    return True


async def initialize_database():
    """Initialize database if needed."""
    
    logger.info("📊 Initializing database...")
    
    try:
        from src.models.database import create_tables
        await create_tables()
        logger.info("✅ Database tables created/verified")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("💡 Make sure PostgreSQL is running and database exists")
        return False


def main():
    """Main startup function."""
    
    logger.info("🚀 Starting AI AdWords Unified Ads Platform")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Initialize database
    try:
        asyncio.run(initialize_database())
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"  # Disable reload in production
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info(f"🔄 Reload mode: {reload}")
    
    # Start the server
    try:
        uvicorn.run(
            "src.api.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("⏹️  Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# For Railway/platform deployments that import this module
def create_app():
    """Create and return the FastAPI app for deployment platforms."""
    from src.api.app import app
    return app
