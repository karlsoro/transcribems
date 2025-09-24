# TranscribeMS - WhisperX Audio Transcription API

Enterprise-grade audio transcription service with speaker identification using WhisperX.

## Features

- **High-Accuracy Transcription**: WhisperX integration with 70x speed improvement over base Whisper
- **Speaker Identification**: Automatic speaker diarization with sequential labeling (Speaker 1, Speaker 2, etc.)
- **Large File Support**: Process audio files up to 5GB with chunked processing strategy
- **GPU Acceleration**: Automatic GPU detection with CPU fallback for optimal performance
- **Real-time Progress**: Server-Sent Events for live transcription progress monitoring
- **Enterprise Integration**: Comprehensive logging, error handling, and validation
- **Async Processing**: Background processing with Celery and Redis for scalability

## Supported Audio Formats

- WAV (recommended for best quality)
- MP3
- M4A
- FLAC

## Quick Start

### Prerequisites

- Python 3.11+
- Redis server
- NVIDIA GPU with CUDA 11.8+ (optional, for acceleration)
- 16GB+ RAM (32GB recommended for large files)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd TranscribeMS
```

2. Create virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start Redis server:
```bash
redis-server
```

6. Start Celery worker:
```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

7. Start the API server:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Setup (Recommended)

```bash
docker-compose up --build
```

## API Usage

### Submit Transcription Job

```bash
curl -X POST "http://localhost:8000/v1/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@/path/to/your/audio.wav" \
  -F "enable_diarization=true" \
  -F "debug_mode=false"
```

### Check Job Status

```bash
curl "http://localhost:8000/v1/transcriptions/{job_id}"
```

### Monitor Progress (Real-time)

```javascript
const eventSource = new EventSource(`http://localhost:8000/v1/transcriptions/${jobId}/progress`);
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(`Progress: ${data.progress}%`);
};
```

## Configuration

Key environment variables:

- `WHISPERX_MODEL_SIZE`: Model size (base, large-v2, large-v3)
- `MAX_FILE_SIZE`: Maximum upload size in bytes (default: 5GB)
- `REDIS_HOST`: Redis server hostname
- `HF_TOKEN`: Hugging Face token for speaker diarization

## Performance

- **CPU Mode**: 1-2x real-time processing
- **GPU Mode**: 10-70x real-time processing (model dependent)
- **Memory Usage**: <2GB system RAM for large files
- **Throughput**: Optimized for enterprise workloads

## Architecture

- **FastAPI**: Async REST API framework
- **WhisperX**: Advanced speech recognition with speaker diarization
- **Celery**: Background task processing
- **Redis**: Message queue and result storage
- **Docker**: Containerized deployment with CUDA support

## Development

### Running Tests

```bash
pytest tests/ -v --cov=src --cov-report=html
```

### Code Quality

```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: See `/docs` endpoint when running
- Issues: GitHub Issues
- Performance: Consult performance optimization guide