# Manual Setup & Running Instructions

## Prerequisites

- Python 3.11+
- pip
- Docker (for containerized deployment)

## Manual Setup (Without Docker)

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Server

#### For Claude Desktop (stdio mode):

```bash
python server.py
```

The server will run in stdio mode by default, waiting for JSON-RPC input on stdin.

#### For LM Studio (SSE mode):

```bash
# Windows:
set MCP_TRANSPORT=sse
python server.py

# Linux/Mac:
export MCP_TRANSPORT=sse
python server.py
```

Server will be available at: `http://localhost:8888/sse`

### 3. Configure Your LLM Client

**Claude Desktop**: Edit config file with absolute path to server.py

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lean-mcp": {
      "command": "python",
      "args": ["C:\\full\\path\\to\\server.py"],
      "env": {
        "MODEL_SERVICE_URL": "http://localhost:8000"
      }
    }
  }
}
```

**LM Studio**: Configure in Settings → Developer → MCP Servers:

```json
{
  "mcpServers": {
    "lean-mcp": {
      "url": "http://127.0.0.1:8888/sse"
    }
  }
}
```

## Docker Setup

### 1. Build the Image

```bash
docker build -t lean-mcp:latest .
```

### 2. Run the Container

#### For Claude Desktop (stdio):

```bash
docker run -it lean-mcp:latest
```

Configure Claude Desktop with Docker:

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

#### For LM Studio (SSE):

```bash
docker run -p 8888:8888 -e MCP_TRANSPORT=sse lean-mcp:latest
```

### 3. Advanced Docker Options

**With custom model service URL** (accessing host at localhost:80):
```bash
docker run -it \
  -e MODEL_SERVICE_URL=http://host.docker.internal:80 \
  lean-mcp
```

**Important**: 
- Use `host.docker.internal` (not `localhost`) to access host services from Docker
- Always include `http://` prefix (httpx requires it)
- Port 80 requires explicit port number: `:80`

**With host networking** (access localhost services directly):
```bash
docker run --network=host lean-mcp
```

**Background mode**:
```bash
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  lean-mcp:latest
```

**View logs**:
```bash
docker logs -f lean-mcp
```

**Stop container**:
```bash
docker stop lean-mcp
docker rm lean-mcp
```

## Configuration Options

All configuration is done via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `sse` |
| `MCP_PORT` | `8888` | Port for SSE mode |
| `MCP_HOST` | `0.0.0.0` | Host binding for SSE mode |
| `MODEL_SERVICE_URL` | `http://localhost:8000` | Your model service URL |
| `API_TIMEOUT` | `30` | API request timeout (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Setting Environment Variables

**Windows CMD**:
```cmd
set MCP_TRANSPORT=sse
set MODEL_SERVICE_URL=http://localhost:8000
python server.py
```

**Windows PowerShell**:
```powershell
$env:MCP_TRANSPORT="sse"
$env:MODEL_SERVICE_URL="http://localhost:8000"
python server.py
```

**Linux/Mac**:
```bash
export MCP_TRANSPORT=sse
export MODEL_SERVICE_URL=http://localhost:8000
python server.py
```

## Verifying Setup

### Manual (stdio mode):

Run the server and it should display:
```
============================================================
MCP Server Configuration:
  Transport: stdio
  Mode: stdio (stdin/stdout)
  Model Service: http://localhost:8000
============================================================
```

The server waits for JSON-RPC input. Press Ctrl+C to stop.

### Manual (SSE mode):

1. Start server with `MCP_TRANSPORT=sse`
2. Open another terminal and test:

**Windows**:
```cmd
curl http://localhost:8888/sse
```

**Linux/Mac**:
```bash
curl http://localhost:8888/sse
```

You should see SSE event stream start (will hang - that's correct). Press Ctrl+C to stop.

### Docker:

```bash
# Test stdio mode
docker run --rm lean-mcp:latest

# Test SSE mode
docker run --rm -p 8888:8888 -e MCP_TRANSPORT=sse lean-mcp:latest
```

Both should show configuration output and start successfully.

## Troubleshooting

### "ModuleNotFoundError: No module named 'mcp'"

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### "Address already in use" (port 8888)

**Solution**: Change port or stop existing process:
```bash
# Windows:
set MCP_PORT=9999
python server.py

# Linux/Mac:
export MCP_PORT=9999
python server.py
```

### Claude Desktop: "Server exits unexpectedly"

**Solutions**:
1. Verify Python is in PATH: `python --version`
2. Use absolute paths in config
3. Check server runs manually first: `python server.py`
4. Ensure stdio mode (default)

### LM Studio: "Connection failed"

**Solutions**:
1. Set `MCP_TRANSPORT=sse`
2. Verify server is running: `curl http://localhost:8888/sse`
3. Use `/sse` endpoint, not `/mcp`
4. Check firewall isn't blocking port 8888

### Tools return errors

**This is normal** if your actual service isn't running. Tools handle errors gracefully. To test with a real service, ensure your service is running on the configured URL.

## Next Steps

1. **Test manually** with one of the methods above
2. **Configure your LLM** client (Claude Desktop or LM Studio)
3. **Add custom tools** by creating new files in `tools/` directory
4. **Deploy with Docker** for production use

See [README.md](README.md) for more information on adding tools and customization.

