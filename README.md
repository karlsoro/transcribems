# TranscribeMCP - GPU-Accelerated Audio Transcription

High-performance audio transcription service with GPU acceleration, speaker diarization, and enterprise-grade reliability.

## 🚀 Key Features

- **GPU Acceleration**: 7x faster processing with NVIDIA CUDA
- **Speaker Diarization**: Automatic speaker identification and labeling
- **Multiple Output Formats**: JSON, TXT, SRT, VTT, TSV
- **Large File Support**: Process hours of audio efficiently
- **Automatic Optimization**: Intelligent GPU/CPU detection and configuration
- **Production Ready**: Enterprise-grade reliability and performance monitoring

## ⚡ Performance

| Mode | Processing Speed | Best Use Case |
|------|-----------------|---------------|
| **GPU (CUDA)** | **6-7x realtime** | Production workloads, large files |
| **CPU** | 1x realtime | Development, small files |

**Real Example**: 47-minute audio file processed in 6.8 minutes (6.97x realtime) on RTX 3060.

## 🛠️ Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd TranscribeMCP

# Create virtual environment
python -m venv transcribe_mcp_env
source transcribe_mcp_env/bin/activate  # Linux/Mac
# transcribe_mcp_env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install GPU support (recommended)
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install "numpy<2"
pip install nvidia-cudnn-cu11==8.7.0.84
```

### Basic Usage

```python
import asyncio
from src.services.simple_whisperx_cli import SimpleWhisperXCLI

async def transcribe_audio():
    cli = SimpleWhisperXCLI()

    result = await cli.transcribe_audio(
        audio_path="your_audio_file.wav",
        model="large-v2",           # Best quality
        enable_diarization=True,    # Speaker identification
        # GPU automatically detected and used
    )

    print(f"Success: {result['success']}")
    print(f"Device used: {result['device_used']}")
    print(f"Processing time: {result['processing_time_seconds']:.1f}s")
    print(f"Speakers detected: {result['speakers_count']}")
    print(f"Text: {result['text'][:200]}...")

# Run transcription
asyncio.run(transcribe_audio())
```

### Command Line Usage

```bash
# Activate environment
source transcribe_mcp_env/bin/activate

# Run transcription (GPU auto-detected)
python -c "
import asyncio
from src.services.simple_whisperx_cli import SimpleWhisperXCLI

async def main():
    cli = SimpleWhisperXCLI()
    result = await cli.transcribe_audio('audio.wav', model='large-v2')
    print(f'Success: {result[\"success\"]}, Device: {result[\"device_used\"]}')

asyncio.run(main())
"
```

## 📋 Requirements

### Hardware Requirements

#### For GPU Acceleration (Recommended)
- **NVIDIA GPU** with CUDA Compute Capability 3.5+
- **VRAM**: 6GB+ for best models (RTX 3060/3070/3080/4070/4080/4090)
- **RAM**: 16GB+ system memory
- **Storage**: NVMe SSD recommended for large files

#### For CPU-Only Mode
- **CPU**: Modern multi-core processor
- **RAM**: 8GB+ system memory
- **Storage**: Any storage type

### Software Requirements

- **Python**: 3.8+
- **CUDA**: 11.8 (for GPU acceleration)
- **FFmpeg**: For audio format conversion
- **Linux/Windows/macOS**: Cross-platform support

## 🎯 Models and Performance

### Available Models

| Model | Quality | Speed | VRAM | Use Case |
|-------|---------|-------|------|----------|
| `base` | Good | Fastest | 2GB | Development, testing |
| `small` | Better | Fast | 3GB | Balanced performance |
| `medium` | Very Good | Medium | 4GB | Production quality |
| `large` | Excellent | Slower | 6GB | High quality |
| `large-v2` | **Best** | Slower | 6GB | **Production** |

### Performance Benchmarks

Tested on RTX 3060 with large-v2 model:

| File Size | Audio Duration | Processing Time | Realtime Factor |
|-----------|----------------|-----------------|-----------------|
| 10MB | 5 min | 45s | 6.7x |
| 50MB | 25 min | 3.5min | 7.1x |
| 111MB | 47 min | 6.8min | 6.97x |

## 📊 Features

### Automatic GPU Detection

The service automatically detects and configures optimal settings:

```python
# Automatic configuration
cli = SimpleWhisperXCLI()
result = await cli.transcribe_audio("audio.wav")

# Manual configuration
result = await cli.transcribe_audio(
    "audio.wav",
    device="cuda",          # Force GPU
    compute_type="float16", # GPU precision
    batch_size=16          # GPU batch size
)
```

### Speaker Diarization

Identify and label different speakers:

```python
result = await cli.transcribe_audio(
    "meeting.wav",
    enable_diarization=True
)

print(f"Speakers: {result['speakers']}")
# Output: ['SPEAKER_00', 'SPEAKER_01', 'SPEAKER_02']

for segment in result['segments'][:3]:
    speaker = segment['speaker']
    text = segment['text']
    print(f"{speaker}: {text}")
```

### Multiple Output Formats

```python
result = await cli.transcribe_audio("audio.wav")

print("Generated files:")
for format_name, file_path in result['generated_files'].items():
    print(f"  {format_name.upper()}: {file_path}")

# Output:
# JSON: /path/to/audio.json (detailed segments)
# TXT: /path/to/audio.txt (plain text)
# SRT: /path/to/audio.srt (subtitles)
# VTT: /path/to/audio.vtt (web subtitles)
# TSV: /path/to/audio.tsv (tab-separated)
```

### Performance Monitoring

```python
result = await cli.transcribe_audio("audio.wav")

# Performance metrics
print(f"Processing time: {result['processing_time_seconds']:.1f}s")
print(f"Audio duration: {result['audio_duration_seconds']:.1f}s")
print(f"Realtime factor: {result['realtime_factor']:.2f}x")
print(f"File processing speed: {result['processing_speed_mb_per_sec']:.2f} MB/s")
print(f"Device used: {result['device_used']}")
print(f"GPU available: {result['gpu_available']}")
```

## 🧪 Testing

### Run Test Suite

```bash
# Activate environment
source transcribe_mcp_env/bin/activate

# Quick validation
python test_service_validation.py

# Comprehensive GPU test
python test_gpu_enhanced_service.py

# Performance benchmark (if large file available)
python large_file_gpu_test.py
```

### Validate GPU Setup

```bash
# Check CUDA availability
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Check GPU details
python -c "import torch; print('GPU:', torch.cuda.get_device_name(0))"

# Test GPU tensor
python -c "import torch; x=torch.tensor([1.0]).cuda(); print('GPU working:', x.device)"
```

## 📚 Documentation

### Comprehensive Guides

- **[GPU Acceleration Guide](docs/GPU_ACCELERATION_GUIDE.md)** - Complete GPU setup and optimization
- **[PyTorch/CUDA Compatibility](docs/PYTORCH_CUDA_COMPATIBILITY.md)** - Version compatibility matrix
- **[Performance Benchmarks](docs/PERFORMANCE_BENCHMARKS.md)** - Detailed performance analysis

### API Reference

```python
class SimpleWhisperXCLI:
    async def transcribe_audio(
        self,
        audio_path: str,                    # Path to audio file
        output_dir: Optional[str] = None,   # Output directory
        model: str = "base",                # Model size
        language: str = "en",               # Language code
        enable_diarization: bool = True,    # Speaker diarization
        timeout_minutes: int = 30,          # Processing timeout
        device: Optional[str] = None,       # Force device (cuda/cpu)
        compute_type: Optional[str] = None, # Precision (float16/float32)
        batch_size: Optional[int] = None    # Batch size
    ) -> Dict[str, Any]:
        """
        Transcribe audio with automatic GPU optimization.

        Returns:
            Dict containing results, performance metrics, and file paths
        """
```

## 🔧 Troubleshooting

### Common Issues

#### GPU Not Detected
```bash
# Install CUDA-enabled PyTorch
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Check GPU
python -c "import torch; print(torch.cuda.is_available())"
```

#### CUDNN Library Issues
```bash
# Install compatible CUDNN
pip install nvidia-cudnn-cu11==8.7.0.84 --force-reinstall
```

#### Out of Memory
```python
# Reduce batch size for lower VRAM
result = await cli.transcribe_audio(
    "audio.wav",
    batch_size=8,  # Reduce from default 16
    model="medium"  # Use smaller model
)
```

### Performance Optimization

#### For Production
```python
# Optimal production settings
result = await cli.transcribe_audio(
    "audio.wav",
    model="large-v2",        # Best quality
    enable_diarization=True, # Speaker ID
    device="cuda",           # Force GPU
    batch_size=16           # Optimal batch size
)
```

#### For Development
```python
# Fast development settings
result = await cli.transcribe_audio(
    "audio.wav",
    model="base",            # Fastest model
    enable_diarization=False, # Skip for speed
    timeout_minutes=5        # Short timeout
)
```

## 🏗️ Architecture

### Project Structure

```
TranscribeMCP/
├── src/
│   ├── mcp_server/
│   │   ├── server.py                # MCP server
│   │   └── fastmcp_server.py        # FastMCP implementation
│   ├── services/
│   │   └── simple_whisperx_cli.py   # Main service (GPU-enhanced)
│   ├── tools/                       # MCP tool implementations
│   └── models/                      # Data models
├── tests/                           # Test suite
│   ├── integration/                 # Integration tests
│   ├── validation/                  # Validation tests
│   └── results/                     # Test results
├── docs/                            # Documentation
│   ├── guides/                      # Setup and integration guides
│   └── INTEGRATION_EXAMPLES.md      # Code examples
├── scripts/                         # Utility scripts
│   ├── start_mcp_server.sh          # MCP server launcher
│   └── test_mcp_connection.py       # Connection test
├── test_data/                       # Sample audio files
└── requirements.txt                 # Dependencies
```

For detailed structure, see [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

### Key Components

- **SimpleWhisperXCLI**: Main transcription service with GPU acceleration
- **MCP Server**: Model Context Protocol server for integrations
- **Automatic Detection**: GPU/CPU detection and optimization
- **Process Management**: Timeout protection and cleanup
- **Performance Monitoring**: Real-time metrics collection
- **Multi-format Output**: JSON, TXT, SRT, VTT, TSV generation

## 🔌 MCP Server Integration

TranscribeMCP provides a Model Context Protocol (MCP) server for easy integration:

```bash
# Start MCP server
./scripts/start_mcp_server.sh

# Test connection
python scripts/test_mcp_connection.py
```

### Quick Integration

**Claude Desktop:**
```json
{
  "mcpServers": {
    "transcribe_mcp": {
      "command": "bash",
      "args": ["/path/to/TranscribeMCP/scripts/start_mcp_server.sh"],
      "cwd": "/path/to/TranscribeMCP"
    }
  }
}
```

**Python:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="bash",
    args=["/path/to/TranscribeMCP/scripts/start_mcp_server.sh"],
    cwd="/path/to/TranscribeMCP"
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("transcribe_audio", {...})
```

### Documentation

- **Connection Guide**: [docs/guides/MCP_CONNECTION_GUIDE.md](docs/guides/MCP_CONNECTION_GUIDE.md)
- **Quick Reference**: [docs/guides/MCP_QUICK_REFERENCE.md](docs/guides/MCP_QUICK_REFERENCE.md)
- **Integration Examples**: [docs/INTEGRATION_EXAMPLES.md](docs/INTEGRATION_EXAMPLES.md)
- **Server Status**: [docs/guides/MCP_SERVER_READY.md](docs/guides/MCP_SERVER_READY.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_service_validation.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** - Foundation transcription model
- **WhisperX** - Enhanced diarization and alignment
- **PyTorch** - Machine learning framework
- **NVIDIA CUDA** - GPU acceleration platform

## 📞 Support

For issues, questions, or feature requests:

1. Check the [documentation](docs/)
2. Run the validation script: `python test_service_validation.py`
3. Review [troubleshooting](#-troubleshooting) section
4. Open an issue with detailed logs and system info

---

**TranscribeMCP** - Making audio transcription fast, accurate, and accessible. 🎵➡️📝