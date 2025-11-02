# Deployment Guide - Common Issues

## Docker Networking Issue: Cannot Access Host Services

### Problem
When running in Docker, `localhost:80` refers to the container itself, not your host machine. You'll see errors like:
- "cannot assign the requested address"
- "Connection refused"
- Service unavailable

### Solutions

#### Option 1: Use `host.docker.internal` (Recommended)

If your REST API is on the host at `localhost:80`, use:

```bash
# Set environment variable
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e MODEL_SERVICE_URL=http://host.docker.internal:80 \
  lean-mcp
```

**Always use `http://` prefix** - httpx requires it.

#### Option 2: Use Host Networking

```bash
docker run --network=host -e MCP_TRANSPORT=sse lean-mcp
```

Then in your code, use `http://localhost:80` (since you're sharing the host network).

**Note**: Host networking only works on Linux. On Windows/Mac Docker Desktop, use Option 1.

#### Option 3: Use Host IP Address

Find your host IP and use it:

```bash
# Linux/Mac
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e MODEL_SERVICE_URL=http://192.168.1.100:80 \
  lean-mcp

# Or use Docker's gateway IP (usually 172.17.0.1)
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e MODEL_SERVICE_URL=http://172.17.0.1:80 \
  lean-mcp
```

## URL Format Requirements

### Always Include Protocol

✅ **Correct:**
- `http://localhost:80`
- `http://host.docker.internal:80`
- `http://192.168.1.100:80`

❌ **Wrong:**
- `localhost:80` (missing protocol)
- `localhost:80` (no http://)

httpx requires the protocol prefix.

### Port Numbers

- Port 80 (default HTTP): `http://host.docker.internal:80` or `http://host.docker.internal`
- Port 443 (HTTPS): `https://host.docker.internal:443` or `https://host.docker.internal`
- Custom ports: Always specify `:PORT`

## 405 Method Not Allowed Error

### Problem
```
INFO: 10.17.21.248:56904 - "POST /sse HTTP/1.1" 405 Method Not Allowed
```

This happens when LM Studio sends a POST request to `/sse`, but FastMCP SSE endpoint expects GET for the initial connection.

### Solution

This is usually not a critical error - it's just LM Studio checking endpoints. The SSE connection should still work via GET requests.

If it persists:
1. Ensure LM Studio is configured correctly:
   ```json
   {
     "mcpServers": {
       "lean-mcp": {
         "url": "http://127.0.0.1:8888/sse"
       }
     }
   }
   ```
2. Check server logs for successful GET requests
3. Verify the container is accessible from LM Studio's network

## Quick Reference: Environment Variables

### For Host Services (Recommended)

```bash
# Linux/Mac Docker Desktop or Docker Engine
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e MODEL_SERVICE_URL=http://host.docker.internal:80 \
  -e API_TIMEOUT=30 \
  lean-mcp

# Windows Docker Desktop
# Same command - host.docker.internal works on Windows too
```

### For Same-Network Services

```bash
# If your REST API is in another Docker container
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e MODEL_SERVICE_URL=http://api-container-name:80 \
  lean-mcp
```

### For Host Networking (Linux only)

```bash
docker run --network=host -e MCP_TRANSPORT=sse lean-mcp
```

Then use `http://localhost:80` in your code.

## Testing Your Configuration

### 1. Test from Inside Container

```bash
# Enter the container
docker exec -it lean-mcp sh

# Test connection to host
# If using host.docker.internal:
wget -O- http://host.docker.internal:80/your-endpoint
# Or with curl:
curl http://host.docker.internal:80/your-endpoint

# Test with your actual API endpoint
curl http://host.docker.internal:80/your-api-path
```

### 2. Check Container Logs

```bash
docker logs -f lean-mcp
```

Look for:
- Connection errors
- URL being used
- Timeout errors

### 3. Verify Environment Variables

```bash
docker exec lean-mcp env | grep MODEL_SERVICE_URL
```

Should show: `MODEL_SERVICE_URL=http://host.docker.internal:80`

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "cannot assign requested address" | Using `localhost` in Docker | Use `host.docker.internal` |
| "Connection refused" | Wrong host/port | Verify service is running and accessible |
| "Name or service not known" | Wrong hostname | Use `host.docker.internal` or IP address |
| Timeout | Service not responding | Check service is running, firewall rules |
| 405 Method Not Allowed | POST to SSE endpoint | Usually harmless, check GET requests work |

## Example: Complete Deployment

```bash
# 1. Build image
docker build -t lean-mcp .

# 2. Run with host service access
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  -e MODEL_SERVICE_URL=http://host.docker.internal:80 \
  -e API_TIMEOUT=30 \
  -e LOG_LEVEL=INFO \
  lean-mcp

# 3. Check logs
docker logs -f lean-mcp

# 4. Test from host
curl http://localhost:8888/sse
```

## Updating Your Tool Code

If you have a new tool making requests to `localhost:80`, update it like this:

```python
# In your tool file (e.g., tools/your_tool.py)
import os
import httpx

# Get URL from environment (with http:// prefix)
API_URL = os.getenv("YOUR_API_URL", "http://localhost:80")
TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

http_client = httpx.Client(timeout=TIMEOUT)

def register_tools(mcp_instance):
    @mcp_instance.tool()
    def your_tool():
        # Always use full URL with http://
        response = http_client.get(f"{API_URL}/your-endpoint")
        return response.json()
```

Then set the environment variable:
```bash
-e YOUR_API_URL=http://host.docker.internal:80
```

