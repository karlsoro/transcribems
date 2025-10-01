# CLI Enhancement Changelog

## Version 1.1.0 - Multi-Transport Support

### Overview
Added HTTP-based server support alongside the existing stdio mode, enabling TranscribeMCP to integrate with a wider range of AI applications beyond Claude Desktop.

### New Features

#### 1. **New CLI Command Structure**
- Main command: `transcribe-mcp {stdio|http} [OPTIONS]`
- Replaces the stdio-only entry point with a flexible mode selection system
- Legacy `transcribe-mcp-stdio` command maintained for backward compatibility

#### 2. **HTTP Server Modes**
Two HTTP transport options now available:

**SSE (Server-Sent Events)** - Default HTTP mode
- Standard HTTP streaming with Server-Sent Events
- Compatible with most web applications and REST clients
- Best for: Web applications, standard integrations

**StreamableHTTP** - Advanced streaming mode
- Enhanced streaming capabilities
- Stateless or stateful operation
- Best for: High-throughput scenarios, complex workflows

#### 3. **Command-Line Options**

**Stdio Mode:**
```bash
transcribe-mcp stdio [--log-level LEVEL]
```

**HTTP Mode:**
```bash
transcribe-mcp http [--host HOST] [--port PORT]
                    [--transport {sse|streamable_http}]
                    [--log-level LEVEL]
```

### Changes to Existing Code

#### Modified Files

1. **`src/mcp_server/server.py`**
   - Added `run_stdio()` method for stdio mode
   - Added `run_sse()` method for SSE HTTP mode
   - Added `run_streamable_http()` method for StreamableHTTP mode
   - Converted tool registrations from `add_tool()` to `@tool()` decorators
   - Updated `run()` to call `run_stdio()` for backward compatibility

2. **`pyproject.toml`**
   - Changed main script entry point from `src.mcp_server.server:main` to `src.mcp_server.cli:main`
   - Added `transcribe-mcp-stdio` as legacy script entry point
   - Added dependencies: `uvicorn>=0.27.0`, `starlette>=0.36.0`

3. **`README.md`**
   - Updated MCP Server Integration section with new command examples
   - Added examples for HTTP clients (JavaScript, Python)
   - Added link to new Server Modes documentation

#### New Files

1. **`src/mcp_server/cli.py`**
   - Complete CLI implementation with argparse
   - Mode selection (stdio vs HTTP)
   - Configuration options for each mode
   - Comprehensive help text and examples

2. **`docs/SERVER_MODES.md`**
   - Complete guide to server modes
   - Integration examples for each mode
   - Configuration reference
   - Troubleshooting guide
   - Security considerations

3. **`docs/QUICK_START_CLI.md`**
   - Quick reference card for CLI usage
   - Common use cases
   - Troubleshooting tips

4. **`tests/test_cli.py`**
   - CLI functionality tests
   - Help message verification
   - Import and initialization tests

### Backward Compatibility

✅ **100% Backward Compatible**

- Existing `transcribe-mcp-stdio` command works unchanged
- Old server initialization code continues to work
- No breaking changes to existing integrations
- Claude Desktop configurations remain valid

### Migration Guide

#### For Claude Desktop Users
No changes needed! But you can update to the new syntax:

**Old (still works):**
```json
{
  "mcpServers": {
    "transcribe_mcp": {
      "command": "transcribe-mcp-stdio"
    }
  }
}
```

**New (recommended):**
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

#### For Script Users
Update any scripts that call the server:

**Old:**
```bash
transcribe-mcp-stdio
```

**New:**
```bash
transcribe-mcp stdio
```

### Usage Examples

#### Start Server in Different Modes

```bash
# Stdio mode (Claude Desktop)
transcribe-mcp stdio

# HTTP SSE mode (default HTTP)
transcribe-mcp http

# HTTP on custom port
transcribe-mcp http --port 3000

# StreamableHTTP mode
transcribe-mcp http --transport streamable_http

# Debug mode
transcribe-mcp http --log-level DEBUG
```

#### Integrate with Web Applications

**JavaScript/Node.js:**
```javascript
const EventSource = require('eventsource');
const es = new EventSource('http://localhost:8000/sse');

es.onmessage = (event) => {
  console.log('Event:', event.data);
};
```

**Python:**
```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "GET",
        "http://localhost:8000/sse",
        headers={"Accept": "text/event-stream"}
    ) as response:
        async for line in response.aiter_lines():
            process_line(line)
```

### Installation

```bash
# Install/upgrade
pip install -e .

# Verify installation
transcribe-mcp --help
```

### Dependencies Added

- `uvicorn>=0.27.0` - ASGI server for HTTP mode
- `starlette>=0.36.0` - Web framework (already required by FastMCP)

### Benefits

1. **Broader Integration**: Works with any AI application that supports HTTP/SSE
2. **Network Access**: Server can be accessed remotely over network
3. **Multiple Clients**: Support concurrent connections from multiple clients
4. **Industry Standard**: Uses standard HTTP/SSE protocols
5. **Flexible Deployment**: Choose the right transport for your use case

### Testing

Run the test suite:
```bash
python -m pytest tests/test_cli.py -v
```

Verify CLI commands:
```bash
transcribe-mcp --help
transcribe-mcp stdio --help
transcribe-mcp http --help
```

### Documentation

- [Complete Server Modes Guide](SERVER_MODES.md)
- [CLI Quick Start](QUICK_START_CLI.md)
- [MCP Connection Guide](guides/MCP_CONNECTION_GUIDE.md)
- [Integration Examples](INTEGRATION_EXAMPLES.md)

### Future Enhancements

Potential future additions:
- WebSocket transport support
- Authentication/authorization for HTTP mode
- TLS/SSL support for secure HTTP
- Rate limiting for HTTP endpoints
- Metrics and monitoring endpoints

### Support

For issues or questions:
1. Check [SERVER_MODES.md](SERVER_MODES.md) documentation
2. Review [QUICK_START_CLI.md](QUICK_START_CLI.md) for examples
3. Run with `--log-level DEBUG` for detailed logs
4. Open an issue with logs and configuration details

---

**Release Date:** 2025-10-01
**Author:** TranscribeMCP Team
**Version:** 1.1.0
