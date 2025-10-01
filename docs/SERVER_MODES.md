# TranscribeMCP Server Modes

TranscribeMCP supports multiple server modes to accommodate different integration scenarios:

## Server Modes

### 1. Stdio Mode (Claude Desktop)

**Use Case**: Integration with Claude Desktop and other stdio-based MCP clients

**Command**:
```bash
# Using the new CLI
transcribe-mcp stdio

# Or using the backward-compatible command
transcribe-mcp-stdio
```

**Features**:
- Standard input/output communication
- No network ports required
- Ideal for local Claude Desktop integration
- Lowest latency

**Configuration**:
```bash
# Enable debug logging
transcribe-mcp stdio --log-level DEBUG
```

### 2. HTTP SSE Mode (Server-Sent Events)

**Use Case**: Integration with web-based AI applications and services

**Command**:
```bash
# Start with default settings (0.0.0.0:8000)
transcribe-mcp http

# Custom host and port
transcribe-mcp http --host 127.0.0.1 --port 3000

# With debug logging
transcribe-mcp http --log-level DEBUG
```

**Features**:
- HTTP-based communication with Server-Sent Events
- Accessible over network
- RESTful-style integration
- Compatible with most web applications

**Example Connection**:
```
http://localhost:8000/sse
```

### 3. HTTP StreamableHTTP Mode

**Use Case**: Advanced HTTP integration with streaming support

**Command**:
```bash
# Start in StreamableHTTP mode
transcribe-mcp http --transport streamable_http

# Custom configuration
transcribe-mcp http --transport streamable_http --host 0.0.0.0 --port 9000
```

**Features**:
- Full HTTP streaming capabilities
- Stateless or stateful operation modes
- Advanced session management
- Optimal for high-throughput scenarios

## Installation

### Basic Installation
```bash
pip install -e .
```

### With HTTP Support (Recommended)
```bash
# HTTP dependencies are included by default
pip install -e .
```

### Development Installation
```bash
pip install -e ".[dev]"
```

## Command Reference

### Main CLI Command: `transcribe-mcp`

```bash
transcribe-mcp {stdio|http} [OPTIONS]
```

#### Stdio Mode Options
- `--log-level {DEBUG|INFO|WARNING|ERROR|CRITICAL}`: Set logging level (default: INFO)

#### HTTP Mode Options
- `--host HOST`: Host address to bind to (default: 0.0.0.0)
- `--port PORT`: Port number to listen on (default: 8000)
- `--transport {sse|streamable_http}`: HTTP transport type (default: sse)
- `--log-level {DEBUG|INFO|WARNING|ERROR|CRITICAL}`: Set logging level (default: INFO)

### Legacy Command: `transcribe-mcp-stdio`

For backward compatibility, the stdio-only command is still available:
```bash
transcribe-mcp-stdio
```

## Integration Examples

### Claude Desktop Configuration

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### HTTP Client Integration (Python)

```python
import httpx
import asyncio

async def connect_to_transcribe_mcp():
    async with httpx.AsyncClient() as client:
        # Connect to SSE endpoint
        async with client.stream(
            "GET",
            "http://localhost:8000/sse",
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                print(line)

asyncio.run(connect_to_transcribe_mcp())
```

### HTTP Client Integration (JavaScript/Node.js)

```javascript
const EventSource = require('eventsource');

const es = new EventSource('http://localhost:8000/sse');

es.onmessage = (event) => {
  console.log('Received:', event.data);
};

es.onerror = (error) => {
  console.error('Error:', error);
};
```

### cURL Testing

```bash
# Test SSE connection
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse

# Test with StreamableHTTP
curl -X POST http://localhost:8000/streamable-http \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list", "params": {}}'
```

## Environment Variables

Configure server behavior using environment variables with the `FASTMCP_` prefix:

```bash
# Set debug mode
export FASTMCP_DEBUG=true

# Set log level
export FASTMCP_LOG_LEVEL=DEBUG

# Configure HTTP settings
export FASTMCP_HOST=127.0.0.1
export FASTMCP_PORT=3000
```

## Choosing the Right Mode

| Mode | Best For | Pros | Cons |
|------|----------|------|------|
| **Stdio** | Claude Desktop, local CLIs | Lowest latency, simple setup | Not network accessible |
| **HTTP SSE** | Web apps, REST APIs | Network accessible, standard HTTP | Requires open port |
| **StreamableHTTP** | High-throughput, complex workflows | Advanced features, scalable | More complex setup |

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use a different port
transcribe-mcp http --port 3000
```

### Connection Refused
- Ensure firewall allows incoming connections
- Check if server is bound to correct interface (0.0.0.0 vs 127.0.0.1)
- Verify the server started without errors in logs

### Debug Mode
Enable detailed logging to troubleshoot issues:
```bash
transcribe-mcp http --log-level DEBUG
```

## Security Considerations

### Network Binding
- **0.0.0.0**: Accessible from any network interface (use with caution)
- **127.0.0.1**: Only accessible from localhost (recommended for development)

### Production Deployment
For production use:
1. Use a reverse proxy (nginx, Apache)
2. Enable HTTPS/TLS
3. Implement authentication
4. Use firewall rules to restrict access
5. Monitor logs for unusual activity

## Performance Tuning

### Stdio Mode
- Minimal overhead
- Direct process communication
- Best for single-user scenarios

### HTTP Mode
- Consider load balancing for multiple clients
- Use StreamableHTTP for better concurrent request handling
- Monitor system resources under load

## Migration from Stdio-Only

If you're upgrading from a stdio-only version:

1. **No Breaking Changes**: Existing `transcribe-mcp-stdio` command still works
2. **New Features**: Access HTTP mode with `transcribe-mcp http`
3. **Dependencies**: HTTP dependencies (uvicorn, starlette) are now included

Update your scripts:
```bash
# Old (still works)
transcribe-mcp-stdio

# New (recommended)
transcribe-mcp stdio
```

## Additional Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/anthropics/mcp-python)
- [WhisperX Documentation](https://github.com/m-bain/whisperX)
