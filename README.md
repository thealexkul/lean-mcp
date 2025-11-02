# Lean MCP - Local Services Integration

Minimal MCP server for bridging AI assistants (Claude Desktop, LM Studio) to local API services.

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Build
docker build -t lean-mcp .

# Run with stdio (for Claude Desktop)
docker run -it lean-mcp

# Run with SSE (for LM Studio)
docker run -p 8888:8888 -e MCP_TRANSPORT=sse lean-mcp
```

### Option 2: Manual

```bash
# Install dependencies
pip install -r requirements.txt

# Run with stdio (Claude Desktop)
python server.py

# Run with SSE (LM Studio)  
MCP_TRANSPORT=sse python server.py
```

## LLM Integration

### Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "lean-mcp": {
      "command": "python",
      "args": ["C:\\path\\to\\server.py"],
      "env": {
        "MODEL_SERVICE_URL": "http://localhost:8000"
      }
    }
  }
}
```

Or with Docker:

```json
{
  "mcpServers": {
    "lean-mcp": {
      "command": "docker",
      "args": ["run", "-i", "lean-mcp"]
    }
  }
}
```

### LM Studio

Configure in Settings → Developer → MCP Servers:

```json
{
  "mcpServers": {
    "lean-mcp": {
      "url": "http://127.0.0.1:8888/sse"
    }
  }
}
```

Start server with:
```bash
MCP_TRANSPORT=sse python server.py
```

## Available Tools

1. **get_available_models()** - List available models from model service
2. **get_model_details(model_id)** - Get details for specific model
3. **check_model_service_health()** - Check model service status

## Adding New Tools

1. Create a new file in `tools/` (e.g., `tools/database.py`)
2. Define tools with the registration function pattern:

```python
def register_tools(mcp_instance):
    @mcp_instance.tool()
    def your_tool_name(param: str) -> dict:
        """Tool description for AI"""
        # Your implementation
        return {"result": "data"}
```

3. Import and register in `server.py`:

```python
from tools import database
database.register_tools(mcp)
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `sse` |
| `MCP_PORT` | `8888` | Port for SSE transport |
| `MCP_HOST` | `0.0.0.0` | Host binding for SSE transport |
| `MODEL_SERVICE_URL` | `http://localhost:8000` | Model service API URL |
| `API_TIMEOUT` | `30` | API request timeout (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Docker

### Build

```bash
docker build -t lean-mcp .
```

### Run Options

**stdio mode** (Claude Desktop):
```bash
docker run -it lean-mcp
```

**SSE mode** (LM Studio):
```bash
docker run -p 8888:8888 -e MCP_TRANSPORT=sse lean-mcp
```

**With custom model service** (accessing host services):
```bash
docker run -it \
  -e MODEL_SERVICE_URL=http://host.docker.internal:80 \
  lean-mcp
```

**Note**: Use `host.docker.internal` instead of `localhost` when accessing services on your host machine from inside Docker. Always include `http://` prefix.

**With host networking** (access localhost services):
```bash
docker run --network=host lean-mcp
```

## Project Structure

```
.
├── server.py           # Main MCP server
├── tools/
│   ├── __init__.py
│   └── models.py       # Example tools for model service
├── Dockerfile          # Container definition
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Troubleshooting

### Claude Desktop: "Server exits unexpectedly"
- Ensure you're using `stdio` transport (default)
- Use full absolute path in config
- Check Python is in PATH

### LM Studio: "404 Not Found"
- Set `MCP_TRANSPORT=sse`
- Use endpoint `/sse` not `/mcp`
- Verify server is running on correct port

### Tools return errors
- This is normal if target services aren't running
- Tools handle errors gracefully
- Configure `MODEL_SERVICE_URL` to point to your service

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

## License

MIT
