#!/usr/bin/env python3
"""
ASGI application for production deployment with Uvicorn/Gunicorn.
"""

import sys
from pathlib import Path

# Add the tools to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from tools.main_tool import app

def create_asgi_app():
    """Create ASGI application for production deployment."""
    # Return the ASGI-compatible HTTP app
    return app.http_app(
        transport="streamable-http",
        path="/mcp",
        json_response=False,
        stateless_http=True  # Enable stateless HTTP for direct POST requests
    )

# ASGI application instance for uvicorn/gunicorn
asgi_app = create_asgi_app()

# For compatibility with different ASGI servers
app_instance = asgi_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "asgi_app:asgi_app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        reload=False
    )
