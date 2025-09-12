"""Minimal FastAPI app for debugging Railway startup issues."""

import os
import logging
from fastapi import FastAPI

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(title="Debug App")

@app.get("/")
def read_root():
    return {"message": "App is working!", "port": os.getenv("PORT")}

@app.get("/health")  
def health():
    return {"status": "healthy", "service": "debug-app"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting debug app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
