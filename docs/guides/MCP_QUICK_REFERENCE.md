# TranscribeMCP MCP Server - Quick Reference

## 🚀 Quick Start

```bash
# Start the server
cd /home/karlsoro/Projects/TranscribeMCP
./scripts/start_mcp_server.sh

# Test the connection
source transcribe_mcp_env/bin/activate
python scripts/test_mcp_connection.py
```

## 📋 Connection Details

| Property | Value |
|----------|-------|
| **Server Name** | `transcribe_mcp` |
| **Protocol** | MCP over stdio |
| **Command** | `python -m src.mcp_server.fastmcp_server` |
| **Working Directory** | `/home/karlsoro/Projects/TranscribeMCP` |
| **Python Version** | 3.12.3 (requires 3.11+) |
| **MCP SDK Version** | 1.15.0 |

## 🔧 Claude Desktop Configuration

**Location:** `~/.config/Claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "transcribe_mcp": {
      "command": "bash",
      "args": ["/home/karlsoro/Projects/TranscribeMCP/scripts/start_mcp_server.sh"],
      "cwd": "/home/karlsoro/Projects/TranscribeMCP"
    }
  }
}
```

## 🛠️ Available Tools (6)

1. **`transcribe_audio`** - GPU-accelerated transcription with speaker diarization
2. **`get_transcription_progress`** - Real-time job progress with GPU metrics
3. **`get_transcription_result`** - Retrieve completed transcription
4. **`list_transcription_history`** - Query historical jobs with statistics
5. **`batch_transcribe`** - Process multiple files concurrently
6. **`cancel_transcription`** - Cancel in-progress jobs

## 💡 Example Usage (Python)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def transcribe():
    server_params = StdioServerParameters(
        command="bash",
        args=["/home/karlsoro/Projects/TranscribeMCP/scripts/start_mcp_server.sh"],
        cwd="/home/karlsoro/Projects/TranscribeMCP"
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Transcribe audio
            result = await session.call_tool(
                "transcribe_audio",
                arguments={
                    "file_path": "/path/to/audio.mp3",
                    "model_size": "base",
                    "enable_diarization": True
                }
            )
            print(f"Job ID: {result.job_id}")
```

## 🔍 Verification Commands

```bash
# Activate environment
source transcribe_mcp_env/bin/activate

# Check server can load
python -c "from src.mcp_server.fastmcp_server import server; print('✅ Server OK')"

# Check MCP SDK
python -c "import mcp; print(f'✅ MCP {mcp.__version__}')"

# Check GPU (optional)
python -c "import torch; print('✅ CUDA' if torch.cuda.is_available() else '✅ CPU')"

# Test full connection
python scripts/test_mcp_connection.py
```

## 📊 Performance Specs

- **GPU Mode**: 6-7x realtime (RTX 3060: 47 min audio → 6.8 min processing)
- **CPU Mode**: ~1x realtime
- **Supported Formats**: MP3, WAV, FLAC, M4A, OGG
- **Model Sizes**: tiny, base, small, medium, large-v2
- **Features**: Speaker diarization, word-level timestamps, confidence scores

## 🔗 Integration Paths

### For Claude Desktop
1. Add server to `claude_desktop_config.json`
2. Restart Claude Desktop
3. Tools appear automatically in conversation

### For Python Projects
1. Use `mcp` SDK with `stdio_client`
2. Configure `StdioServerParameters` with server path
3. Call tools via `session.call_tool()`

### For Node.js Projects
1. Use `@modelcontextprotocol/sdk`
2. Configure `StdioClientTransport`
3. Connect client and call tools

## 📁 Key Files

| File | Purpose |
|------|---------|
| [MCP_CONNECTION_GUIDE.md](MCP_CONNECTION_GUIDE.md) | Complete integration guide |
| [scripts/start_mcp_server.sh](../../scripts/start_mcp_server.sh) | Server startup script |
| [scripts/test_mcp_connection.py](../../scripts/test_mcp_connection.py) | Connection test utility |
| [src/mcp_server/fastmcp_server.py](../../src/mcp_server/fastmcp_server.py) | FastMCP implementation (recommended) |
| [src/mcp_server/server.py](../../src/mcp_server/server.py) | Alternative server implementation |
| [pyproject.toml](../../pyproject.toml) | Package metadata and dependencies |
| [docs/PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) | Project organization guide |

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Server won't start | Activate venv: `source transcribe_mcp_env/bin/activate` |
| Import errors | Install deps: `pip install -r requirements.txt` |
| GPU not detected | Install CUDA toolkit or use CPU mode (automatic fallback) |
| Connection timeout | Check file paths are absolute, not relative |
| Tool call fails | Verify audio file exists and is readable |

## 📞 Support

For detailed documentation:
- **Connection Guide**: [MCP_CONNECTION_GUIDE.md](MCP_CONNECTION_GUIDE.md)
- **Integration Examples**: [INTEGRATION_EXAMPLES.md](../INTEGRATION_EXAMPLES.md)
- **Server Status**: [MCP_SERVER_READY.md](MCP_SERVER_READY.md)
- **Project Structure**: [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)

---

**Ready to integrate?** Start with `./scripts/test_mcp_connection.py` to verify everything works!
