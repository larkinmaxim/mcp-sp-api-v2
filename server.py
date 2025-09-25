#!/usr/bin/env python3
"""
FastMCP server runner for Transport Order XML Generator.
"""

import sys
import asyncio
from pathlib import Path

# Add the tools to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from tools.main_tool import app

def main():
    """Main entry point for the FastMCP server."""
    try:
        print("Starting Transport Order XML Generator FastMCP Server...")
        print("Available tools:")
        print("- generate_transport_order_xml")
        print("- validate_transport_order_xml")
        print("- get_transport_type_info")
        print("- get_available_transport_types")
        print("- get_transport_order_example")
        print("- get_parameter_requirements")
        print("- get_user_credentials")
        print("- send_xml_to_transporeon_api")
        
        # Run the FastMCP server with streamable HTTP transport
        app.run(
            transport="http",
            host="0.0.0.0",
            port=8000,
            path="/mcp",
            show_banner=True,
            log_level="INFO",
            stateless_http=True  # Enable stateless HTTP for direct POST requests
        )
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
