# TranscribeMS MCP Integration Examples

Complete examples for integrating TranscribeMS MCP server into various projects.

## Table of Contents
- [Claude Desktop Integration](#claude-desktop-integration)
- [Python Client Integration](#python-client-integration)
- [Node.js Client Integration](#nodejs-client-integration)
- [REST API Wrapper](#rest-api-wrapper)
- [Advanced Usage Patterns](#advanced-usage-patterns)

---

## Claude Desktop Integration

### Configuration File

**Location:** `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "transcribems": {
      "command": "bash",
      "args": ["/home/karlsoro/Projects/TranscribeMS/scripts/start_mcp_server.sh"],
      "cwd": "/home/karlsoro/Projects/TranscribeMS"
    }
  }
}
```

### Using in Claude Desktop

Once configured, you can ask Claude to:

```
"Transcribe the audio file at /path/to/meeting.mp3 with speaker identification"

"Check the progress of job b3e5f375-3503-4f25-9de0-a5289e455cac"

"List my last 10 transcription jobs and show me the statistics"
```

Claude will automatically use the TranscribeMS MCP tools.

---

## Python Client Integration

### Complete Example

```python
#!/usr/bin/env python3
"""
Complete TranscribeMS MCP client example.
"""

import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TranscribeMSClient:
    """High-level client for TranscribeMS MCP server."""

    def __init__(self, server_path: str = "/home/karlsoro/Projects/TranscribeMS"):
        self.server_params = StdioServerParameters(
            command="bash",
            args=[f"{server_path}/scripts/start_mcp_server.sh"],
            cwd=server_path,
        )

    async def transcribe_file(
        self,
        file_path: str,
        model_size: str = "base",
        enable_diarization: bool = True,
        wait_for_completion: bool = True,
    ) -> dict:
        """
        Transcribe an audio file.

        Args:
            file_path: Path to audio file
            model_size: WhisperX model size (tiny/base/small/medium/large)
            enable_diarization: Enable speaker identification
            wait_for_completion: Wait for transcription to complete

        Returns:
            Transcription result or job info
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Start transcription
                result = await session.call_tool(
                    "transcribe_audio",
                    arguments={
                        "file_path": file_path,
                        "model_size": model_size,
                        "enable_diarization": enable_diarization,
                        "output_format": "detailed",
                    },
                )

                # Extract job_id from result
                content = result.content[0] if hasattr(result, "content") else result
                if isinstance(content, dict):
                    job_id = content.get("job", {}).get("job_id")
                else:
                    job_id = getattr(content, "job_id", None)

                if not wait_for_completion:
                    return {"job_id": job_id, "status": "submitted"}

                # Wait for completion
                while True:
                    progress = await session.call_tool(
                        "get_transcription_progress",
                        arguments={"job_id": job_id},
                    )

                    prog_content = (
                        progress.content[0]
                        if hasattr(progress, "content")
                        else progress
                    )
                    status = (
                        prog_content.get("status")
                        if isinstance(prog_content, dict)
                        else getattr(prog_content, "status", None)
                    )

                    if status == "completed":
                        # Get final results
                        final_result = await session.call_tool(
                            "get_transcription_result",
                            arguments={
                                "job_id": job_id,
                                "format": "full",
                                "include_speakers": enable_diarization,
                            },
                        )
                        return final_result.content[0] if hasattr(final_result, "content") else final_result

                    elif status in ["failed", "cancelled"]:
                        return {"status": status, "job_id": job_id}

                    # Wait before checking again
                    await asyncio.sleep(2)

    async def batch_transcribe(
        self, file_paths: list[str], model_size: str = "base", max_concurrent: int = 3
    ) -> dict:
        """Transcribe multiple files."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "batch_transcribe",
                    arguments={
                        "file_paths": file_paths,
                        "model_size": model_size,
                        "max_concurrent": max_concurrent,
                    },
                )

                return result.content[0] if hasattr(result, "content") else result

    async def get_history(
        self, limit: int = 10, status_filter: str = None, get_statistics: bool = False
    ) -> dict:
        """Get transcription history."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                args = {"limit": limit, "get_statistics": get_statistics}
                if status_filter:
                    args["status_filter"] = status_filter

                result = await session.call_tool("list_transcription_history", arguments=args)
                return result.content[0] if hasattr(result, "content") else result


# Example usage
async def main():
    client = TranscribeMSClient()

    # Single file transcription
    print("Transcribing single file...")
    result = await client.transcribe_file(
        file_path="/path/to/audio.mp3", model_size="base", wait_for_completion=True
    )
    print(f"✅ Transcription complete: {result.get('text', 'N/A')[:100]}...")

    # Batch transcription
    print("\nBatch transcription...")
    batch_result = await client.batch_transcribe(
        file_paths=["/path/to/file1.mp3", "/path/to/file2.mp3"]
    )
    print(f"✅ Batch submitted: {batch_result}")

    # Get history
    print("\nFetching history...")
    history = await client.get_history(limit=5, get_statistics=True)
    print(f"✅ Found {len(history.get('jobs', []))} recent jobs")


if __name__ == "__main__":
    asyncio.run(main())
```

### Simple Quick-Start Example

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def transcribe():
    server_params = StdioServerParameters(
        command="bash",
        args=["/home/karlsoro/Projects/TranscribeMS/scripts/start_mcp_server.sh"],
        cwd="/home/karlsoro/Projects/TranscribeMS"
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Transcribe
            result = await session.call_tool(
                "transcribe_audio",
                arguments={
                    "file_path": "/path/to/audio.mp3",
                    "model_size": "base",
                }
            )
            print(result)

asyncio.run(transcribe())
```

---

## Node.js Client Integration

### Installation

```bash
npm install @modelcontextprotocol/sdk
```

### Complete Example

```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

class TranscribeMSClient {
  constructor(serverPath = "/home/karlsoro/Projects/TranscribeMS") {
    this.serverPath = serverPath;
  }

  async connect() {
    const transport = new StdioClientTransport({
      command: "bash",
      args: [`${this.serverPath}/scripts/start_mcp_server.sh`],
      cwd: this.serverPath,
    });

    this.client = new Client(
      {
        name: "transcribems-client",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    await this.client.connect(transport);
    return this;
  }

  async transcribeFile(filePath, options = {}) {
    const {
      modelSize = "base",
      enableDiarization = true,
      language = null,
    } = options;

    const result = await this.client.callTool({
      name: "transcribe_audio",
      arguments: {
        file_path: filePath,
        model_size: modelSize,
        enable_diarization: enableDiarization,
        language: language,
      },
    });

    return result.content[0];
  }

  async getProgress(jobId) {
    const result = await this.client.callTool({
      name: "get_transcription_progress",
      arguments: { job_id: jobId },
    });

    return result.content[0];
  }

  async getResult(jobId, includeOptions = {}) {
    const {
      format = "full",
      includeSpeakers = true,
      includeTimestamps = true,
    } = includeOptions;

    const result = await this.client.callTool({
      name: "get_transcription_result",
      arguments: {
        job_id: jobId,
        format: format,
        include_speakers: includeSpeakers,
        include_timestamps: includeTimestamps,
      },
    });

    return result.content[0];
  }

  async batchTranscribe(filePaths, options = {}) {
    const { modelSize = "base", maxConcurrent = 3 } = options;

    const result = await this.client.callTool({
      name: "batch_transcribe",
      arguments: {
        file_paths: filePaths,
        model_size: modelSize,
        max_concurrent: maxConcurrent,
      },
    });

    return result.content[0];
  }

  async getHistory(options = {}) {
    const { limit = 10, statusFilter = null, getStatistics = false } = options;

    const args = { limit, get_statistics: getStatistics };
    if (statusFilter) args.status_filter = statusFilter;

    const result = await this.client.callTool({
      name: "list_transcription_history",
      arguments: args,
    });

    return result.content[0];
  }

  async disconnect() {
    await this.client.close();
  }
}

// Example usage
async function main() {
  const client = await new TranscribeMSClient().connect();

  try {
    // Transcribe single file
    console.log("Transcribing file...");
    const job = await client.transcribeFile("/path/to/audio.mp3", {
      modelSize: "base",
      enableDiarization: true,
    });
    console.log(`✅ Job submitted: ${job.job_id}`);

    // Check progress
    const progress = await client.getProgress(job.job_id);
    console.log(`Progress: ${progress.progress}%`);

    // Batch transcribe
    const batchJob = await client.batchTranscribe([
      "/path/to/file1.mp3",
      "/path/to/file2.mp3",
    ]);
    console.log(`✅ Batch submitted:`, batchJob);

    // Get history
    const history = await client.getHistory({ limit: 5, getStatistics: true });
    console.log(`✅ History:`, history);
  } finally {
    await client.disconnect();
  }
}

main().catch(console.error);
```

---

## REST API Wrapper

Create a REST API wrapper around the MCP server:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

app = FastAPI(title="TranscribeMS REST API")

SERVER_PARAMS = StdioServerParameters(
    command="bash",
    args=["/home/karlsoro/Projects/TranscribeMS/scripts/start_mcp_server.sh"],
    cwd="/home/karlsoro/Projects/TranscribeMS"
)


class TranscriptionRequest(BaseModel):
    file_path: str
    model_size: str = "base"
    enable_diarization: bool = True


class BatchRequest(BaseModel):
    file_paths: list[str]
    model_size: str = "base"
    max_concurrent: int = 3


@app.post("/api/transcribe")
async def transcribe_audio(request: TranscriptionRequest):
    """Start audio transcription."""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "transcribe_audio",
                arguments=request.model_dump()
            )

            return result.content[0] if hasattr(result, "content") else result


@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    """Get transcription progress."""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "get_transcription_progress",
                arguments={"job_id": job_id}
            )

            return result.content[0] if hasattr(result, "content") else result


@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    """Get transcription result."""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "get_transcription_result",
                arguments={"job_id": job_id, "format": "full"}
            )

            return result.content[0] if hasattr(result, "content") else result


@app.post("/api/batch")
async def batch_transcribe(request: BatchRequest):
    """Batch transcribe multiple files."""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "batch_transcribe",
                arguments=request.model_dump()
            )

            return result.content[0] if hasattr(result, "content") else result


@app.get("/api/history")
async def get_history(limit: int = 10, status_filter: str = None):
    """Get transcription history."""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            args = {"limit": limit}
            if status_filter:
                args["status_filter"] = status_filter

            result = await session.call_tool(
                "list_transcription_history",
                arguments=args
            )

            return result.content[0] if hasattr(result, "content") else result


# Run with: uvicorn rest_api_wrapper:app --reload
```

---

## Advanced Usage Patterns

### Pattern 1: Polling with Timeout

```python
async def transcribe_with_timeout(client, file_path, timeout_seconds=300):
    """Transcribe with timeout."""
    start_time = asyncio.get_event_loop().time()

    # Start transcription
    result = await client.transcribe_file(file_path, wait_for_completion=False)
    job_id = result["job_id"]

    # Poll with timeout
    while True:
        if asyncio.get_event_loop().time() - start_time > timeout_seconds:
            # Cancel job
            await client.cancel_transcription(job_id, "Timeout exceeded")
            raise TimeoutError(f"Transcription exceeded {timeout_seconds}s")

        progress = await client.get_progress(job_id)
        if progress["status"] == "completed":
            return await client.get_result(job_id)

        await asyncio.sleep(2)
```

### Pattern 2: Progress Callback

```python
async def transcribe_with_callback(client, file_path, on_progress):
    """Transcribe with progress callback."""
    result = await client.transcribe_file(file_path, wait_for_completion=False)
    job_id = result["job_id"]

    while True:
        progress = await client.get_progress(job_id)

        # Call user's callback
        on_progress(progress)

        if progress["status"] == "completed":
            return await client.get_result(job_id)

        await asyncio.sleep(1)


# Usage
await transcribe_with_callback(
    client,
    "/path/to/audio.mp3",
    on_progress=lambda p: print(f"Progress: {p['progress']}%")
)
```

### Pattern 3: Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def transcribe_with_retry(client, file_path):
    """Transcribe with automatic retry."""
    try:
        return await client.transcribe_file(file_path)
    except Exception as e:
        print(f"Attempt failed: {e}")
        raise
```

---

## Testing Your Integration

```python
import pytest

@pytest.mark.asyncio
async def test_transcription():
    """Test basic transcription."""
    client = TranscribeMSClient()
    result = await client.transcribe_file(
        "/path/to/test.mp3",
        wait_for_completion=True
    )
    assert result["status"] == "completed"
    assert "text" in result
```

---

For more details, see:
- [MCP_CONNECTION_GUIDE.md](../MCP_CONNECTION_GUIDE.md) - Complete setup guide
- [MCP_QUICK_REFERENCE.md](../MCP_QUICK_REFERENCE.md) - Quick reference
- [README.md](../README.md) - Project overview
