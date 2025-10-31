"""
Lean MCP - Minimal MCP Server for Local Services Integration
Supports both stdio (Claude Desktop) and SSE (LM Studio) transports
"""
import os
import sys
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize fastMCP server
mcp = FastMCP("Lean MCP")

# Import and register tools
logger.info("Loading tools...")
try:
    from tools import models
    models.register_tools(mcp)
    logger.info("Loaded model service tools")
except Exception as e:
    logger.error("Failed to load tools: %s", e)
    sys.exit(1)

# Configuration
TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # stdio or sse
PORT = int(os.getenv("MCP_PORT", "8888"))
HOST = os.getenv("MCP_HOST", "0.0.0.0")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Lean MCP Configuration:")
    logger.info("  Transport: %s", TRANSPORT)
    
    if TRANSPORT == "sse":
        logger.info("  Host: %s", HOST)
        logger.info("  Port: %s", PORT)
        logger.info("  Endpoint: http://localhost:%s/sse", PORT)
    else:
        logger.info("  Mode: stdio (stdin/stdout)")
    
    logger.info("  Model Service: %s", os.getenv('MODEL_SERVICE_URL', 'http://localhost:8000'))
    logger.info("=" * 60)
    
    if TRANSPORT == "sse":
        # HTTP/SSE transport for LM Studio, web clients
        import uvicorn
        app = mcp.sse_app()
        uvicorn.run(app, host=HOST, port=PORT, log_level=LOG_LEVEL.lower())
    else:
        # stdio transport for Claude Desktop, MCP clients
        mcp.run(transport='stdio')

