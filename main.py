"""Alternative entry point for Railway deployment."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Import and run the start script
    import start_app
    start_app.main()
