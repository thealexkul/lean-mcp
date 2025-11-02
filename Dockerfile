# Lean MCP Dockerfile
FROM python:3.11-slim

# Metadata
LABEL maintainer="Lean MCP"
LABEL description="Lean MCP - Minimal MCP server for bridging AI assistants to local services"

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

# Install system dependencies (curl for testing/debugging)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy dependencies first (for better layer caching)
COPY --chown=mcpuser:mcpuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=mcpuser:mcpuser server.py .
COPY --chown=mcpuser:mcpuser tools/ ./tools/

# Switch to non-root user
USER mcpuser

# Expose port for SSE transport
EXPOSE 8888

# Default to stdio transport (for Claude Desktop)
# Override with: docker run -e MCP_TRANSPORT=sse
ENV MCP_TRANSPORT=stdio

# Run the server
CMD ["python", "server.py"]
