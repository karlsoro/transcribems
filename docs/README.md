# TranscribeMCP - WhisperX Audio Transcription MCP Server

Enterprise-grade audio transcription service with speaker identification using WhisperX, implemented as a Model Context Protocol (MCP) server.

## Features

- **High-Accuracy Transcription**: WhisperX integration with 70x speed improvement over base Whisper
- **Speaker Identification**: Automatic speaker diarization with sequential labeling (Speaker 1, Speaker 2, etc.)
- **Large File Support**: Process audio files up to 5GB with chunked processing strategy
- **GPU Acceleration**: Automatic GPU detection with CPU fallback for optimal performance
- **MCP Integration**: Native Model Context Protocol server for seamless AI agent integration
- **Enterprise Integration**: Comprehensive logging, error handling, and validation
- **Async Processing**: Built-in async processing for optimal performance

## Supported Audio Formats

- WAV (recommended for best quality)
- MP3
- M4A
- FLAC

## Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA GPU with CUDA 11.8+ (optional, for acceleration)
- 16GB+ RAM (32GB recommended for large files)
- MCP-compatible client (Claude Desktop, VS Code with MCP extension, or custom MCP client)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd TranscribeMCP
   ```

2. Create virtual environment:

   ```bash
   python3.11 -m venv transcribe_mcp_env
   source transcribe_mcp_env/bin/activate  # On Windows: transcribe_mcp_env\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Configure environment:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration (HF_TOKEN for speaker diarization)
   ```

5. Test the installation:

   ```bash
   # Run the integration test
   python3 integration_test.py

   # Run MCP contract tests
   python3 -m pytest tests/contract/mcp/ -v
   ```

### MCP Server Setup

#### Option 1: Direct Command Line

```bash
# Start the MCP server
transcribe_mcp-mcp

# Or run directly with Python
python -m src.mcp_server.server
```

#### Option 2: Claude Desktop Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "transcribe_mcp": {
      "command": "transcribe_mcp-mcp",
      "args": [],
      "env": {
        "HF_TOKEN": "your_huggingface_token_here"
      }
    }
  }
}
```

#### Option 3: Docker Setup

```bash
docker-compose up --build
```

## MCP Tools Usage

TranscribeMCP provides the following MCP tools:

### Available Tools

1. **transcribe_audio** - Transcribe audio files with speaker diarization
2. **get_transcription_progress** - Monitor transcription progress
3. **get_transcription_result** - Retrieve completed transcription results
4. **list_transcription_history** - View transcription history
5. **batch_transcribe** - Process multiple audio files
6. **cancel_transcription** - Cancel running transcriptions

### Example Usage (MCP Client)

```python
# Example MCP client usage
import asyncio
from mcp.client import ClientSession

async def transcribe_audio():
    async with ClientSession() as session:
        # Submit transcription
        result = await session.call_tool(
            "transcribe_audio",
            {
                "audio_file_path": "/path/to/audio.wav",
                "enable_diarization": True,
                "debug_mode": False
            }
        )

        job_id = result["job_id"]

        # Monitor progress
        while True:
            progress = await session.call_tool(
                "get_transcription_progress",
                {"job_id": job_id}
            )

            if progress["status"] == "completed":
                break

            await asyncio.sleep(1)

        # Get final result
        final_result = await session.call_tool(
            "get_transcription_result",
            {"job_id": job_id}
        )

        return final_result

# Run the transcription
result = asyncio.run(transcribe_audio())
print(result)
```

## Configuration

Key environment variables:

- `WHISPERX_MODEL_SIZE`: Model size (base, large-v2, large-v3) - default: large-v2
- `MAX_FILE_SIZE`: Maximum upload size in bytes (default: 5GB)
- `HF_TOKEN`: Hugging Face token for speaker diarization (required for diarization)
- `TRANSCRIBE_MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `TRANSCRIBE_MCP_WORK_DIR`: Working directory for temporary files

## Performance

- **CPU Mode**: 1-2x real-time processing
- **GPU Mode**: 10-70x real-time processing (model dependent)
- **Memory Usage**: <2GB system RAM for large files
- **Throughput**: Optimized for enterprise workloads

## Architecture

- **MCP Server**: Model Context Protocol server for AI agent integration
- **WhisperX**: Advanced speech recognition with speaker diarization
- **AsyncIO**: Async processing for optimal performance
- **Pydantic**: Data validation and serialization
- **Structured Logging**: Comprehensive logging with structured output
- **Docker**: Containerized deployment with CUDA support

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run all tests
python3 -m pytest tests/ -v --cov=src --cov-report=html

# Run only MCP contract tests
python3 -m pytest tests/contract/mcp/ -v

# Run integration tests
python3 -m pytest tests/integration/ -v

# Run the comprehensive integration test
python3 integration_test.py
```

### Testing Your Setup

```bash
# 1. Create test audio (if you don't have any)
python3 create_test_audio.py

# 2. Run system demo
python3 system_demo.py

# 3. Run performance benchmark
python3 performance_benchmark.py

# 4. Validate implementation
python3 validate_implementation.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Sort imports
isort src/ tests/

# Run pre-commit hooks
pre-commit run --all-files
```

### Validating Transcription Results

To ensure your setup is working correctly:

1. **Basic Validation**:

   ```bash
   python3 integration_test.py
   ```

   This will test all MCP tools and report success/failure.

2. **Audio Quality Test**:

   ```bash
   python3 create_test_audio.py  # Creates test_audio/test_speech.wav
   python3 system_demo.py        # Transcribes the test audio
   ```

   Check the output in `system_demo_report.json` for accuracy.

3. **Performance Benchmark**:

   ```bash
   python3 performance_benchmark.py
   ```

   Validates performance metrics and accuracy.

4. **Manual Validation**:
   - Use your own audio files
   - Check speaker diarization accuracy (if enabled)
   - Verify timestamps and formatting
   - Test large file processing

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: See `/docs` endpoint when running
- Issues: GitHub Issues
- Performance: Consult performance optimization guide
