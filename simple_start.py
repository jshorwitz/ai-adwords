#!/usr/bin/env python3
"""Simple startup script for Synter without database dependencies."""

import os
import sys
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    """Simple main function to start the FastAPI app."""
    
    logger.info("🚀 Starting Synter - AI Advertising Agency")
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🌐 Starting server on {host}:{port}")
    
    # Start the server with the API app
    try:
        uvicorn.run(
            "src.api.app:app",
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
