# TranscribeMCP CLI Quick Start

Quick reference for using the TranscribeMCP command-line interface.

## Installation

```bash
pip install -e .
```

## Basic Commands

### Stdio Mode (Claude Desktop)

```bash
# Start stdio mode
transcribe-mcp stdio

# With debug logging
transcribe-mcp stdio --log-level DEBUG

# Legacy command (still supported)
transcribe-mcp-stdio
```

### HTTP Mode (Web Applications)

```bash
# Start HTTP server (SSE mode, default)
transcribe-mcp http

# Custom host and port
transcribe-mcp http --host 127.0.0.1 --port 3000

# StreamableHTTP mode
transcribe-mcp http --transport streamable_http

# With debug logging
transcribe-mcp http --log-level DEBUG
```

## Configuration Options

### Stdio Mode
| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--log-level` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Logging verbosity |

### HTTP Mode
| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--host` | IP address | 0.0.0.0 | Host to bind to |
| `--port` | Port number | 8000 | Port to listen on |
| `--transport` | sse, streamable_http | sse | HTTP transport type |
| `--log-level` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Logging verbosity |

## Integration Examples

### Claude Desktop Configuration

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "transcribe_mcp": {
      "command": "transcribe-mcp",
      "args": ["stdio"]
    }
  }
}
```

### Test HTTP Server

```bash
# Start server
transcribe-mcp http

# Test with curl (in another terminal)
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse
```

### Python HTTP Client

```python
import httpx
import asyncio

async def test_connection():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            "http://localhost:8000/sse",
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                print(line)
                break  # Just test connection

asyncio.run(test_connection())
```

## Common Use Cases

### Development (Local Testing)
```bash
# Bind to localhost only
transcribe-mcp http --host 127.0.0.1 --port 3000 --log-level DEBUG
```

### Production (Network Access)
```bash
# Allow external connections
transcribe-mcp http --host 0.0.0.0 --port 8000
```

### Claude Desktop
```bash
# Stdio mode for desktop integration
transcribe-mcp stdio
```

### Web Application Integration
```bash
# SSE mode for standard web apps
transcribe-mcp http --transport sse

# StreamableHTTP for advanced streaming
transcribe-mcp http --transport streamable_http
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
transcribe-mcp http --port 3000
```

### Connection Issues
```bash
# Enable debug logging
transcribe-mcp http --log-level DEBUG

# Check server is accessible
curl http://localhost:8000/sse
```

### Server Won't Start
```bash
# Check dependencies
pip install -e .

# Verify installation
transcribe-mcp --help
```

## Environment Variables

Configure defaults using environment variables:

```bash
export FASTMCP_HOST=127.0.0.1
export FASTMCP_PORT=3000
export FASTMCP_LOG_LEVEL=DEBUG
export FASTMCP_DEBUG=true

# Then run without flags
transcribe-mcp http
```

## Help Commands

```bash
# Main help
transcribe-mcp --help

# Stdio mode help
transcribe-mcp stdio --help

# HTTP mode help
transcribe-mcp http --help
```

## Additional Resources

- [Complete Server Modes Guide](SERVER_MODES.md)
- [MCP Connection Guide](guides/MCP_CONNECTION_GUIDE.md)
- [Integration Examples](INTEGRATION_EXAMPLES.md)
