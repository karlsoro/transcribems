# TranscribeMS MCP Server - Connection Guide

## Overview

TranscribeMS provides a **Model Context Protocol (MCP)** server that exposes GPU-accelerated audio transcription capabilities with speaker diarization. This guide shows how to connect and use the MCP server from other projects.

## Server Details

- **Server Name**: `transcribems`
- **Protocol**: MCP over stdio
- **Package**: `transcribems`
- **Version**: 1.0.0
- **Entry Point**: `transcribems-mcp` or `python -m src.mcp_server.server`

## Installation

### Option 1: Install as Package (Recommended for Production)

```bash
# From the TranscribeMS directory
cd /home/karlsoro/Projects/TranscribeMS

# Install in development mode (editable)
pip install -e .

# Or install with GPU support
pip install -e ".[gpu]"

# Or install with all development tools
pip install -e ".[dev,gpu]"
```

### Option 2: Direct Python Execution (Development)

```bash
# Ensure dependencies are installed
cd /home/karlsoro/Projects/TranscribeMS
pip install -r requirements.txt

# Run directly
python -m src.mcp_server.server
```

## MCP Server Configuration

### For Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "transcribems": {
      "command": "transcribems-mcp",
      "cwd": "/home/karlsoro/Projects/TranscribeMS"
    }
  }
}
```

Or using Python directly:

```json
{
  "mcpServers": {
    "transcribems": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/home/karlsoro/Projects/TranscribeMS",
      "env": {
        "PYTHONPATH": "/home/karlsoro/Projects/TranscribeMS"
      }
    }
  }
}
```

### For Python MCP Clients

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def connect_to_transcribems():
    server_params = StdioServerParameters(
        command="transcribems-mcp",
        cwd="/home/karlsoro/Projects/TranscribeMS"
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools]}")

            # Use a tool
            result = await session.call_tool(
                "transcribe_audio",
                arguments={
                    "file_path": "/path/to/audio.mp3",
                    "model_size": "base",
                    "enable_diarization": True
                }
            )
            print(result)

asyncio.run(connect_to_transcribems())
```

### For Node.js MCP Clients

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function connectToTranscribeMS() {
  const transport = new StdioClientTransport({
    command: "transcribems-mcp",
    cwd: "/home/karlsoro/Projects/TranscribeMS"
  });

  const client = new Client({
    name: "my-client",
    version: "1.0.0"
  }, {
    capabilities: {}
  });

  await client.connect(transport);

  // List available tools
  const tools = await client.listTools();
  console.log("Available tools:", tools.tools.map(t => t.name));

  // Call transcription tool
  const result = await client.callTool({
    name: "transcribe_audio",
    arguments: {
      file_path: "/path/to/audio.mp3",
      model_size: "base",
      enable_diarization: true
    }
  });

  console.log(result);
}

connectToTranscribeMS().catch(console.error);
```

## Available MCP Tools

The TranscribeMS MCP server exposes 6 primary tools:

### 1. `transcribe_audio`
Transcribe a single audio file with GPU acceleration and speaker diarization.

**Parameters:**
- `file_path` (string, required): Path to audio file
- `model_size` (string, default: "base"): Model size (tiny/base/small/medium/large)
- `language` (string, optional): Language code (auto-detect if not provided)
- `enable_diarization` (boolean, default: true): Enable speaker identification
- `output_format` (string, default: "detailed"): Output format (simple/detailed/segments)
- `device` (string, optional): Processing device (cpu/cuda, auto-detected if not provided)
- `compute_type` (string, optional): Computation type (int8/float16/float32)

**Returns:** Job information with job_id for tracking

### 2. `get_transcription_progress`
Get real-time progress for transcription jobs.

**Parameters:**
- `job_id` (string, optional): Specific job ID to query
- `all_jobs` (boolean, default: false): Get all active jobs

**Returns:** Progress information with GPU performance metrics

### 3. `get_transcription_result`
Retrieve completed transcription results.

**Parameters:**
- `job_id` (string, required): Job ID
- `format` (string, default: "full"): Output format (text/segments/full/summary)
- `include_metadata` (boolean, default: true): Include processing metadata
- `include_timestamps` (boolean, default: true): Include word-level timestamps
- `include_confidence` (boolean, default: true): Include confidence scores
- `include_speakers` (boolean, default: true): Include speaker information

**Returns:** Transcription results with requested formatting

### 4. `list_transcription_history`
List historical transcription jobs with filtering.

**Parameters:**
- `limit` (integer, default: 10): Maximum entries to return (1-100)
- `status_filter` (string, optional): Filter by status (pending/processing/completed/failed/cancelled)
- `date_from` (string, optional): Start date (ISO format)
- `date_to` (string, optional): End date (ISO format)
- `search_query` (string, optional): Search in filenames
- `get_statistics` (boolean, default: false): Include usage statistics
- `statistics_days` (integer, default: 30): Days for statistics (1-365)

**Returns:** List of historical jobs with optional statistics

### 5. `batch_transcribe`
Transcribe multiple audio files with shared settings.

**Parameters:**
- `file_paths` (array, required): List of audio file paths (1-10 files)
- `model_size` (string, default: "base"): Model size for all files
- `language` (string, optional): Language code
- `enable_diarization` (boolean, default: true): Enable speaker diarization
- `output_format` (string, default: "detailed"): Output format
- `device` (string, optional): Processing device
- `max_concurrent` (integer, default: 3): Maximum concurrent jobs (1-5)

**Returns:** Batch job information with individual job IDs

### 6. `cancel_transcription`
Cancel in-progress transcription jobs.

**Parameters:**
- `job_id` (string, required): Job ID to cancel
- `reason` (string, default: "Cancelled by user"): Cancellation reason

**Returns:** Cancellation confirmation

## Usage Examples

### Example 1: Basic Transcription

```python
# Call via MCP client
result = await session.call_tool(
    "transcribe_audio",
    arguments={
        "file_path": "/path/to/meeting.mp3",
        "model_size": "large-v2",
        "enable_diarization": True
    }
)

job_id = result.content[0].job_id

# Check progress
progress = await session.call_tool(
    "get_transcription_progress",
    arguments={"job_id": job_id}
)

# Get results when complete
transcription = await session.call_tool(
    "get_transcription_result",
    arguments={
        "job_id": job_id,
        "format": "full",
        "include_speakers": True
    }
)
```

### Example 2: Batch Processing

```python
result = await session.call_tool(
    "batch_transcribe",
    arguments={
        "file_paths": [
            "/path/to/file1.mp3",
            "/path/to/file2.mp3",
            "/path/to/file3.mp3"
        ],
        "model_size": "base",
        "max_concurrent": 2
    }
)
```

### Example 3: History and Statistics

```python
history = await session.call_tool(
    "list_transcription_history",
    arguments={
        "limit": 20,
        "status_filter": "completed",
        "get_statistics": True,
        "statistics_days": 7
    }
)
```

## Environment Requirements

### Python Environment
- Python 3.11+
- Virtual environment recommended

### GPU Support (Optional but Recommended)
- NVIDIA GPU with CUDA Compute Capability 3.5+
- CUDA 11.8 or 12.1
- 6GB+ VRAM for best models

### System Requirements
- 16GB+ RAM
- NVMe SSD recommended for large files

## Performance

| Mode | Processing Speed | Use Case |
|------|-----------------|----------|
| **GPU (CUDA)** | **6-7x realtime** | Production, large files |
| **CPU** | 1x realtime | Development, small files |

**Real Example**: 47-minute audio processed in 6.8 minutes on RTX 3060.

## Troubleshooting

### Server Won't Start

```bash
# Check if package is installed
pip show transcribems

# Verify Python version
python3 --version  # Should be 3.11+

# Check dependencies
pip install -r /home/karlsoro/Projects/TranscribeMS/requirements.txt

# Run with debugging
python -m src.mcp_server.server
```

### Tool Calls Fail

1. **Check file paths**: Must be absolute paths
2. **Verify audio format**: Supports MP3, WAV, FLAC, M4A, OGG
3. **GPU issues**: Falls back to CPU automatically
4. **Memory**: Ensure sufficient RAM/VRAM for model size

### Connection Issues

```bash
# Test MCP server directly
cd /home/karlsoro/Projects/TranscribeMS
transcribems-mcp

# Should output MCP protocol messages
```

## Support and Documentation

- **Repository**: `/home/karlsoro/Projects/TranscribeMS`
- **Main Server**: [src/mcp_server/fastmcp_server.py](../../src/mcp_server/fastmcp_server.py)
- **Alternative Server**: [src/mcp_server/server.py](../../src/mcp_server/server.py)
- **Tool Implementations**: `../../src/tools/`
- **Project Structure**: [docs/PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)

## Integration Checklist

- [ ] Install TranscribeMS package or add to Python path
- [ ] Configure MCP server in client configuration
- [ ] Verify server starts correctly (`scripts/test_mcp_connection.py`)
- [ ] Test basic transcribe_audio tool call
- [ ] Check GPU detection (if applicable)
- [ ] Test progress tracking
- [ ] Implement error handling for tool calls
- [ ] Set up proper file path management

## Additional Resources

- **Quick Reference**: [MCP_QUICK_REFERENCE.md](MCP_QUICK_REFERENCE.md)
- **Integration Examples**: [INTEGRATION_EXAMPLES.md](../INTEGRATION_EXAMPLES.md)
- **Server Status**: [MCP_SERVER_READY.md](MCP_SERVER_READY.md)
- **Project Structure**: [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)

## Security Notes

- Server runs locally via stdio (no network exposure)
- File paths must be accessible to server process
- Ensure proper file permissions for audio files
- Results stored temporarily in memory

## License

MIT License - See project README for details.
