# HTTP Client Integration Examples

Complete examples for integrating with TranscribeMCP HTTP server.

## Starting the HTTP Server

```bash
# Start HTTP server (SSE mode, default)
transcribe-mcp http

# Custom port
transcribe-mcp http --port 3000

# StreamableHTTP mode
transcribe-mcp http --transport streamable_http

# With debug logging
transcribe-mcp http --log-level DEBUG
```

---

## Python HTTP Client Integration

### Complete HTTP Client Class

```python
#!/usr/bin/env python3
"""
Complete TranscribeMCP HTTP client example.
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional

class TranscribeMCPHTTPClient:
    """High-level HTTP client for TranscribeMCP server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.message_endpoint = f"{base_url}/message"
        self.sse_endpoint = f"{base_url}/sse"

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Call an MCP tool via HTTP POST."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.message_endpoint,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    },
                    "id": 1
                },
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

    async def transcribe_file(
        self,
        file_path: str,
        model_size: str = "base",
        enable_diarization: bool = True,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe an audio file."""
        return await self.call_tool(
            "transcribe_audio",
            {
                "file_path": file_path,
                "model_size": model_size,
                "enable_diarization": enable_diarization,
                "language": language,
                "output_format": "detailed"
            },
            timeout=300.0  # 5 minutes for transcription
        )

    async def get_progress(self, job_id: str) -> Dict[str, Any]:
        """Get transcription progress."""
        return await self.call_tool(
            "get_transcription_progress",
            {"job_id": job_id}
        )

    async def get_result(
        self,
        job_id: str,
        format: str = "full",
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Get transcription result."""
        return await self.call_tool(
            "get_transcription_result",
            {
                "job_id": job_id,
                "format": format,
                "include_metadata": include_metadata,
                "include_timestamps": True,
                "include_speakers": True
            }
        )

    async def list_history(
        self,
        limit: int = 10,
        status_filter: Optional[str] = None,
        get_statistics: bool = False
    ) -> Dict[str, Any]:
        """List transcription history."""
        args = {
            "limit": limit,
            "get_statistics": get_statistics
        }
        if status_filter:
            args["status_filter"] = status_filter

        return await self.call_tool("list_transcription_history", args)

    async def batch_transcribe(
        self,
        file_paths: list[str],
        model_size: str = "base",
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """Batch transcribe multiple files."""
        return await self.call_tool(
            "batch_transcribe",
            {
                "file_paths": file_paths,
                "model_size": model_size,
                "max_concurrent": max_concurrent
            },
            timeout=600.0  # 10 minutes for batch
        )

    async def cancel_transcription(
        self,
        job_id: str,
        reason: str = "Cancelled by user"
    ) -> Dict[str, Any]:
        """Cancel a transcription job."""
        return await self.call_tool(
            "cancel_transcription",
            {"job_id": job_id, "reason": reason}
        )

    async def listen_sse_events(self, callback):
        """Listen to Server-Sent Events."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                self.sse_endpoint,
                headers={"Accept": "text/event-stream"},
                timeout=None
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            await callback(data)
                        except json.JSONDecodeError:
                            pass


# Example usage
async def main():
    client = TranscribeMCPHTTPClient("http://localhost:8000")

    # Single file transcription
    print("Transcribing single file...")
    result = await client.transcribe_file(
        file_path="/path/to/audio.mp3",
        model_size="base",
        enable_diarization=True
    )
    print(f"✅ Result: {result}")

    # Get job progress (if job_id was returned)
    if "job_id" in str(result):
        job_id = result.get("result", {}).get("job_id")
        if job_id:
            progress = await client.get_progress(job_id)
            print(f"📊 Progress: {progress}")

    # List history
    print("\nFetching history...")
    history = await client.list_history(limit=5, get_statistics=True)
    print(f"📜 History: {history}")

    # Batch transcription
    print("\nBatch transcription...")
    batch_result = await client.batch_transcribe(
        file_paths=["/path/to/file1.mp3", "/path/to/file2.mp3"],
        max_concurrent=2
    )
    print(f"✅ Batch result: {batch_result}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Simple HTTP Example

```python
import asyncio
import httpx

async def simple_transcribe():
    """Simple transcription example."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/message",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "transcribe_audio",
                    "arguments": {
                        "file_path": "/path/to/audio.mp3",
                        "model_size": "base",
                        "enable_diarization": True
                    }
                },
                "id": 1
            },
            timeout=300.0
        )
        result = response.json()
        print(f"Result: {result}")

asyncio.run(simple_transcribe())
```

### SSE Event Listener Example

```python
import asyncio
import httpx
import json

async def listen_to_events():
    """Listen to Server-Sent Events."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            "http://localhost:8000/sse",
            headers={"Accept": "text/event-stream"},
            timeout=None
        ) as response:
            print("Connected to SSE stream...")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        print(f"Event: {data}")
                    except json.JSONDecodeError as e:
                        print(f"JSON error: {e}")

asyncio.run(listen_to_events())
```

---

## JavaScript/Node.js HTTP Client Integration

### Complete Node.js Client Class

```javascript
const axios = require('axios');
const EventSource = require('eventsource');

class TranscribeMCPHTTPClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.messageEndpoint = `${baseUrl}/message`;
    this.sseEndpoint = `${baseUrl}/sse`;
  }

  async callTool(toolName, arguments, timeout = 30000) {
    try {
      const response = await axios.post(
        this.messageEndpoint,
        {
          jsonrpc: '2.0',
          method: 'tools/call',
          params: {
            name: toolName,
            arguments: arguments
          },
          id: 1
        },
        { timeout }
      );
      return response.data;
    } catch (error) {
      console.error('Error calling tool:', error.message);
      throw error;
    }
  }

  async transcribeFile(filePath, options = {}) {
    const {
      modelSize = 'base',
      enableDiarization = true,
      language = null
    } = options;

    return this.callTool(
      'transcribe_audio',
      {
        file_path: filePath,
        model_size: modelSize,
        enable_diarization: enableDiarization,
        language: language,
        output_format: 'detailed'
      },
      300000  // 5 minutes
    );
  }

  async getProgress(jobId) {
    return this.callTool('get_transcription_progress', { job_id: jobId });
  }

  async getResult(jobId, format = 'full') {
    return this.callTool('get_transcription_result', {
      job_id: jobId,
      format: format,
      include_metadata: true,
      include_timestamps: true,
      include_speakers: true
    });
  }

  async listHistory(limit = 10, statusFilter = null, getStatistics = false) {
    const args = { limit, get_statistics: getStatistics };
    if (statusFilter) {
      args.status_filter = statusFilter;
    }
    return this.callTool('list_transcription_history', args);
  }

  async batchTranscribe(filePaths, modelSize = 'base', maxConcurrent = 3) {
    return this.callTool(
      'batch_transcribe',
      {
        file_paths: filePaths,
        model_size: modelSize,
        max_concurrent: maxConcurrent
      },
      600000  // 10 minutes
    );
  }

  async cancelTranscription(jobId, reason = 'Cancelled by user') {
    return this.callTool('cancel_transcription', { job_id: jobId, reason });
  }

  listenSSE(callback) {
    const es = new EventSource(this.sseEndpoint);

    es.onopen = () => {
      console.log('Connected to SSE stream');
    };

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        callback(data);
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    es.onerror = (error) => {
      console.error('SSE error:', error);
    };

    return es;  // Return for cleanup
  }
}

// Example usage
async function main() {
  const client = new TranscribeMCPHTTPClient('http://localhost:8000');

  try {
    // Single file transcription
    console.log('Transcribing single file...');
    const result = await client.transcribeFile('/path/to/audio.mp3', {
      modelSize: 'base',
      enableDiarization: true
    });
    console.log('✅ Result:', result);

    // List history
    console.log('\nFetching history...');
    const history = await client.listHistory(5, null, true);
    console.log('📜 History:', history);

    // Listen to SSE events
    console.log('\nListening to SSE events...');
    const es = client.listenSSE((data) => {
      console.log('📡 Event:', data);
    });

    // Clean up after 30 seconds
    setTimeout(() => {
      es.close();
      console.log('Closed SSE connection');
    }, 30000);

  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

### Simple Node.js Example

```javascript
const axios = require('axios');

async function simpleTranscribe() {
  try {
    const response = await axios.post(
      'http://localhost:8000/message',
      {
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: 'transcribe_audio',
          arguments: {
            file_path: '/path/to/audio.mp3',
            model_size: 'base',
            enable_diarization: true
          }
        },
        id: 1
      },
      { timeout: 300000 }
    );
    console.log('Result:', response.data);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

simpleTranscribe();
```

---

## cURL Examples

### Transcribe Audio

```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "transcribe_audio",
      "arguments": {
        "file_path": "/path/to/audio.mp3",
        "model_size": "base",
        "enable_diarization": true,
        "output_format": "detailed"
      }
    },
    "id": 1
  }'
```

### Get Progress

```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_transcription_progress",
      "arguments": {
        "job_id": "your-job-id-here"
      }
    },
    "id": 1
  }'
```

### List History

```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_transcription_history",
      "arguments": {
        "limit": 10,
        "get_statistics": true
      }
    },
    "id": 1
  }'
```

### Listen to SSE

```bash
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse
```

---

## Testing and Debugging

### Test Server Connection

```bash
# Test if server is running
curl http://localhost:8000/sse

# Test with timeout
curl --max-time 5 http://localhost:8000/sse
```

### Debug Mode

```bash
# Start server with debug logging
transcribe-mcp http --log-level DEBUG

# Monitor requests in real-time
tail -f /path/to/server.log
```

### Error Handling

```python
import asyncio
import httpx

async def transcribe_with_error_handling():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/message",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "transcribe_audio",
                        "arguments": {
                            "file_path": "/path/to/audio.mp3",
                            "model_size": "base"
                        }
                    },
                    "id": 1
                },
                timeout=300.0
            )
            response.raise_for_status()
            result = response.json()

            # Check for JSON-RPC error
            if "error" in result:
                print(f"Error: {result['error']['message']}")
                return None

            return result["result"]

    except httpx.TimeoutException:
        print("Request timed out")
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(transcribe_with_error_handling())
```

---

## See Also

- [Server Modes Guide](SERVER_MODES.md)
- [MCP Connection Guide](guides/MCP_CONNECTION_GUIDE.md)
- [Quick Start CLI](QUICK_START_CLI.md)
