# Docker Quick Reference

## Running Lean MCP in Docker

### For Claude Desktop (stdio mode)

**Interactive mode** (foreground, see logs):
```bash
docker run -it --name lean-mcp lean-mcp
```
Press `Ctrl+C` to stop.

**Detached mode** (background, appears in Docker Desktop):
```bash
docker run -d --name lean-mcp lean-mcp
```

**View logs:**
```bash
docker logs -f lean-mcp
```

**Stop:**
```bash
docker stop lean-mcp
```

**Remove:**
```bash
docker rm lean-mcp
```

### For LM Studio (SSE mode)

**Detached mode** (recommended, appears in Docker Desktop):
```bash
docker run -d --name lean-mcp \
  -p 8888:8888 \
  -e MCP_TRANSPORT=sse \
  lean-mcp
```

**View logs:**
```bash
docker logs -f lean-mcp
```

**Stop:**
```bash
docker stop lean-mcp
docker rm lean-mcp
```

### Quick Commands

**Remove old containers:**
```bash
docker rm -f lean-mcp  # Force remove if running
```

**See all lean-mcp containers:**
```bash
docker ps -a --filter "ancestor=lean-mcp"
```

**Clean up stopped containers:**
```bash
docker container prune
```

## Common Issues

### Container exits immediately
- **stdio mode**: This is normal - it waits for stdin input from Claude Desktop
- **SSE mode**: Check logs: `docker logs lean-mcp`

### Container not visible in Docker Desktop
- Use `-d` flag for detached mode
- Use `--name` to give it a fixed name
- Example: `docker run -d --name lean-mcp -p 8888:8888 -e MCP_TRANSPORT=sse lean-mcp`

### Port already in use
```bash
# Use different port
docker run -d --name lean-mcp \
  -p 9999:8888 \
  -e MCP_TRANSPORT=sse \
  -e MCP_PORT=8888 \
  lean-mcp
```

