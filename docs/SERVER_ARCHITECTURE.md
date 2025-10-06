# TranscribeMCP Server Architecture

## Overview

TranscribeMCP provides **THREE SEPARATE SERVER IMPLEMENTATIONS** designed for different integration scenarios. This document explains when and how to use each one.

---

## Server Implementations

### 1. MCP Server (stdio mode)

**File**: `src/mcp_server/server.py`
**Command**: `transcribe-mcp stdio`

**Purpose**: Integration with Claude Desktop and stdio-based MCP clients

**How it works**:
- Communicates via stdin/stdout
- Uses MCP JSON-RPC protocol
- No network ports required
- Single-process, synchronous execution

**When to use**:
- Claude Desktop integration
- Local development with MCP-compatible tools
- stdin/stdout based workflows

**Example**:
```bash
# Start the MCP server for Claude Desktop
transcribe-mcp stdio

# Add to Claude Desktop config:
{
  "mcpServers": {
    "transcribe": {
      "command": "transcribe-mcp",
      "args": ["stdio"]
    }
  }
}
```

---

### 2. MCP Server (HTTP mode)

**File**: `src/mcp_server/server.py`
**Command**: `transcribe-mcp http`

**Purpose**: Integration with web-based MCP clients and AI applications

**How it works**:
- Exposes MCP JSON-RPC protocol over HTTP
- Uses Server-Sent Events (SSE) or StreamableHTTP
- Network-accessible MCP endpoints: `/sse`, `/message`
- Multi-client support

**When to use**:
- Web-based AI applications that speak MCP protocol
- Remote MCP client connections
- MCP-compatible services over network

**Example**:
```bash
# Start MCP server in HTTP mode
transcribe-mcp http --host 0.0.0.0 --port 8000

# Or with StreamableHTTP transport
transcribe-mcp http --transport streamable_http
```

**Client Connection** (MCP JSON-RPC):
```javascript
// Connect to MCP server via HTTP
const response = await fetch('http://localhost:8000/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'transcribe_audio',
      arguments: {
        file_path: '/path/to/audio.mp3',
        model_size: 'base'
      }
    },
    id: 1
  })
});
```

---

### 3. REST API Server (Simplified)

**File**: `src/main_simple.py`
**Command**: `transcribe-rest`

**Purpose**: Traditional REST API for web UIs, mobile apps, and standard HTTP clients

**How it works**:
- Traditional REST API with JSON responses
- Standard HTTP endpoints: `/v1/transcribe`, `/v1/jobs/{id}`
- No MCP protocol required
- In-memory job storage (no Redis/Celery required)

**When to use**:
- Web application frontends
- Mobile applications
- Traditional REST API clients
- Testing and development
- Simple deployments without infrastructure dependencies

**Example**:
```bash
# Start REST API server
transcribe-rest

# Server starts on http://0.0.0.0:8000
```

**Client Connection** (Standard REST):
```javascript
// Upload audio file
const formData = new FormData();
formData.append('file', audioFile);
formData.append('language', 'auto');

const response = await fetch('http://localhost:8000/v1/transcribe', {
  method: 'POST',
  body: formData
});

const { job_id } = await response.json();

// Poll for status
const statusResponse = await fetch(`http://localhost:8000/v1/jobs/${job_id}`);
const status = await statusResponse.json();
```

---

## Comparison Matrix

| Feature | MCP (stdio) | MCP (HTTP) | REST API |
|---------|------------|------------|----------|
| **Protocol** | MCP JSON-RPC | MCP JSON-RPC | REST JSON |
| **Transport** | stdin/stdout | HTTP/SSE | HTTP |
| **Endpoints** | N/A | `/sse`, `/message` | `/v1/*` |
| **Network** | No | Yes | Yes |
| **Port** | None | 8000 (configurable) | 8000 (configurable) |
| **Multi-client** | No | Yes | Yes |
| **Client Type** | MCP clients | MCP clients | Any HTTP client |
| **Dependencies** | mcp | mcp, starlette, uvicorn | fastapi, uvicorn |
| **Infrastructure** | None | None | None |
| **Job Storage** | In-memory | In-memory | In-memory |
| **Use Case** | Claude Desktop | Web MCP clients | Web/mobile UIs |

---

## Architecture Diagrams

### MCP Server (stdio mode)
```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │ stdin/stdout
         │ (MCP JSON-RPC)
         │
┌────────▼────────┐
│  MCP Server     │
│  (stdio mode)   │
└────────┬────────┘
         │
┌────────▼────────┐
│  WhisperX       │
│  Service        │
└─────────────────┘
```

### MCP Server (HTTP mode)
```
┌─────────────────┐     ┌─────────────────┐
│  MCP Client 1   │     │  MCP Client 2   │
│  (Web App)      │     │  (AI Service)   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │ HTTP (MCP JSON-RPC)   │
         │                       │
         └───────┬───────────────┘
                 │
         ┌───────▼───────┐
         │  MCP Server   │
         │  (HTTP mode)  │
         │  Port: 8000   │
         └───────┬───────┘
                 │
         ┌───────▼───────┐
         │  WhisperX     │
         │  Service      │
         └───────────────┘
```

### REST API Server
```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Web UI     │  │  Mobile App │  │  cURL/API   │
│  (React)    │  │  (Flutter)  │  │  Client     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       │    REST API (JSON)              │
       │                │                │
       └────────┬───────┴────────────────┘
                │
        ┌───────▼────────┐
        │  REST API      │
        │  Server        │
        │  (FastAPI)     │
        │  Port: 8000    │
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │  WhisperX      │
        │  Service       │
        └────────────────┘
```

---

## Why Three Servers?

### Historical Context

The project evolved to support different integration patterns:

1. **MCP (stdio)** - Original implementation for Claude Desktop
2. **MCP (HTTP)** - Added to support web-based MCP clients
3. **REST API** - Added for traditional web/mobile applications

### Protocol Differences

**MCP JSON-RPC Protocol**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "transcribe_audio",
    "arguments": { "file_path": "/path/to/audio.mp3" }
  },
  "id": 1
}
```

**REST API Protocol**:
```http
POST /v1/transcribe HTTP/1.1
Content-Type: multipart/form-data

file=@audio.mp3&language=auto
```

---

## Which Server Should You Use?

### Use MCP Server (stdio) if:
- ✅ You're integrating with Claude Desktop
- ✅ You need local, single-process execution
- ✅ You're building MCP-compatible tools

### Use MCP Server (HTTP) if:
- ✅ You're building web-based AI applications
- ✅ Your client speaks MCP JSON-RPC protocol
- ✅ You need network-accessible MCP services
- ✅ You want standardized AI tool integration

### Use REST API Server if:
- ✅ You're building a web UI or mobile app
- ✅ You need a traditional REST API
- ✅ Your client doesn't speak MCP protocol
- ✅ You want simple HTTP integration
- ✅ You're prototyping or testing

---

## Installation & Setup

All three servers are included in the base installation:

```bash
# Install TranscribeMCP
pip install -e .

# All three commands are now available:
transcribe-mcp stdio          # MCP stdio mode
transcribe-mcp http           # MCP HTTP mode
transcribe-rest               # REST API mode
```

---

## Production Considerations

### Simplified Servers (Current)
- **Storage**: In-memory (jobs lost on restart)
- **Processing**: Background tasks (asyncio)
- **Scaling**: Single instance
- **Best for**: Development, testing, small-scale deployments

### Production Servers (Future)
For production deployments, you would add:
- **Job Queue**: Celery + Redis
- **Storage**: PostgreSQL database
- **Processing**: Distributed workers
- **Caching**: Redis
- **Load Balancer**: nginx/HAProxy

See `src/main.py` and `src/tasks/transcription_tasks.py` for the Celery-based production implementation (requires additional setup).

---

## Common Questions

### Q: Can I run multiple servers simultaneously?
**A**: Yes! They use different communication methods:
- MCP (stdio): Uses stdin/stdout
- MCP (HTTP): Uses port 8000 (configurable)
- REST API: Uses port 8000 (configurable)

Just use different ports for HTTP servers:
```bash
# MCP HTTP on port 8000
transcribe-mcp http --port 8000

# REST API on port 8001
PORT=8001 transcribe-rest
```

### Q: Which server is faster?
**A**: All three use the same WhisperX backend, so transcription speed is identical. Network overhead:
- MCP (stdio): No network overhead (fastest)
- MCP (HTTP): Minimal HTTP + SSE overhead
- REST API: Standard HTTP overhead

### Q: Can I convert between protocols?
**A**: No. Each server speaks a specific protocol. Your client must match:
- MCP client → MCP server
- REST client → REST API server

### Q: Why not just use one server?
**A**: Different clients need different protocols:
- Claude Desktop requires MCP stdio
- Web MCP clients require MCP HTTP
- Traditional web UIs require REST API

---

## Next Steps

- **For MCP integration**: See [MCP_CONNECTION_GUIDE.md](guides/MCP_CONNECTION_GUIDE.md)
- **For REST API usage**: See [REST_API_GUIDE.md](REST_API_GUIDE.md)
- **For production deployment**: See [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md)
