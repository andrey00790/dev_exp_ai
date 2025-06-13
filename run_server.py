#!/usr/bin/env python3
"""
Wrapper script to run the AI Assistant MVP server.

This script sets up the correct Python path and runs the server.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = str(project_root)

if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting AI Assistant MVP server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Project root: {project_root}")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1) 