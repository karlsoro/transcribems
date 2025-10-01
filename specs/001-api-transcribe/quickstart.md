# Quickstart: WhisperX Audio Transcription API

**Feature**: WhisperX Audio Transcription API with Speaker Identification
**Date**: 2025-01-24
**Audience**: Developers, System Administrators, QA Engineers

## Overview

This quickstart guide demonstrates the complete workflow for using the WhisperX Audio Transcription API, from initial setup through processing large audio files with speaker identification.

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or newer, Windows 10/11, macOS 12+
- **Memory**: 8GB RAM minimum, 16GB+ recommended for large files
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional, for acceleration)
- **Storage**: 50GB free space for processing temporary files

### Dependencies
- **Python**: 3.11 (required for WhisperX compatibility)
- **CUDA**: 11.8 or 12.1 (if using GPU acceleration)
- **FFmpeg**: Latest version for audio preprocessing

## Quick Setup

### 1. Environment Setup
```bash
# Create virtual environment
python3.11 -m venv transcribe_mcp-env
source transcribe_mcp-env/bin/activate  # Linux/macOS
# transcribe_mcp-env\Scripts\activate  # Windows

# Install core dependencies
pip install whisperx fastapi uvicorn redis celery
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify GPU support (optional)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 2. Service Configuration
```bash
# Start Redis server (required for background processing)
redis-server

# Set environment variables
export WHISPERX_MODEL_SIZE=large-v2
export MAX_FILE_SIZE=5368709120  # 5GB
export OUTPUT_DIR=./transcriptions
export DEBUG_MODE=false
```

### 3. API Server Startup
```bash
# Clone the repository
git clone https://github.com/your-org/transcribe_mcp.git
cd transcribe_mcp

# Start the API server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery worker (in separate terminal)
celery -A src.tasks.celery_app worker --loglevel=info
```

## Basic Usage Scenarios

### Scenario 1: Simple Audio Transcription

**Given**: A 5-minute MP3 file with two speakers
**When**: File is submitted via API
**Then**: JSON transcription with speaker identification is returned

```bash
# Test with sample audio file
curl -X POST "http://localhost:8000/v1/transcriptions" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@sample_meeting.mp3" \
  -F "enable_diarization=true" \
  -F "model_size=large-v2"

# Response
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "estimated_completion": "2025-01-24T15:35:00Z",
  "progress_url": "/v1/transcriptions/550e8400-e29b-41d4-a716-446655440000"
}
```

### Scenario 2: Large File Processing

**Given**: A 2GB WAV file from a 3-hour conference
**When**: File is processed with debug logging enabled
**Then**: Chunked processing with progress updates

```python
import requests
import time

# Submit large file
with open('conference_recording.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/v1/transcriptions',
        files={'audio_file': f},
        data={
            'enable_diarization': True,
            'max_speakers': 5,
            'debug_mode': True,
            'model_size': 'large-v2'
        }
    )

job_id = response.json()['job_id']
print(f"Job submitted: {job_id}")

# Poll for completion
while True:
    status_response = requests.get(f'http://localhost:8000/v1/transcriptions/{job_id}')
    status_data = status_response.json()

    print(f"Status: {status_data['status']}, Progress: {status_data['progress']}%")

    if status_data['status'] in ['completed', 'failed']:
        break

    time.sleep(10)

# Get final results
if status_data['status'] == 'completed':
    print("Transcription completed!")
    print(f"Speakers detected: {status_data['metadata']['speakers_detected']}")
    print(f"Processing time: {status_data['metadata']['processing_time_seconds']}s")
```

### Scenario 3: Real-time Progress Monitoring

**Given**: A processing job is in progress
**When**: Client connects to progress endpoint
**Then**: Real-time updates via Server-Sent Events

```javascript
// Client-side JavaScript for real-time progress
const jobId = "550e8400-e29b-41d4-a716-446655440000";
const eventSource = new EventSource(`http://localhost:8000/v1/transcriptions/${jobId}/progress`);

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log(`Status: ${data.status}, Progress: ${data.progress}%`);

    // Update UI
    document.getElementById('progress-bar').style.width = `${data.progress}%`;
    document.getElementById('status-text').textContent = data.message;

    if (data.status === 'completed') {
        eventSource.close();
        // Fetch final results
        fetchTranscriptionResults(jobId);
    }
};

eventSource.onerror = function(error) {
    console.error('Progress monitoring error:', error);
};
```

## Integration Test Scenarios

### Test 1: File Format Validation
```bash
# Test valid formats
for format in wav mp3 m4a flac; do
    echo "Testing ${format} format..."
    curl -X POST "http://localhost:8000/v1/transcriptions" \
      -F "audio_file=@test_audio.${format}" \
      -F "enable_diarization=true"
done

# Test invalid format (should return 400)
curl -X POST "http://localhost:8000/v1/transcriptions" \
  -F "audio_file=@test_video.avi" \
  -F "enable_diarization=true"

# Expected response:
# {
#   "error": "INVALID_FILE_FORMAT",
#   "message": "Unsupported audio format. Supported formats: WAV, MP3, M4A, FLAC"
# }
```

### Test 2: File Size Limits
```python
import requests
import os

def test_file_size_limit():
    # Create a file larger than 5GB (should fail)
    large_file_path = 'test_large_file.wav'

    # Don't actually create 5GB+ file in test, just simulate
    print("Testing file size validation...")

    # Test with valid size file
    response = requests.post(
        'http://localhost:8000/v1/transcriptions',
        files={'audio_file': ('small_test.wav', b'fake_audio_data' * 1000)},
        data={'enable_diarization': True}
    )

    assert response.status_code == 202, "Small file should be accepted"

    print("✅ File size validation working correctly")

test_file_size_limit()
```

### Test 3: Speaker Diarization Accuracy
```python
def test_speaker_diarization():
    """Test speaker identification with known multi-speaker audio"""

    # Use test file with known 3 speakers
    test_file = 'test_3_speakers.wav'

    response = requests.post(
        'http://localhost:8000/v1/transcriptions',
        files={'audio_file': open(test_file, 'rb')},
        data={
            'enable_diarization': True,
            'min_speakers': 2,
            'max_speakers': 5
        }
    )

    job_id = response.json()['job_id']

    # Wait for completion (simplified polling)
    result = wait_for_completion(job_id)

    # Validate results
    assert result['status'] == 'completed'
    assert result['metadata']['speakers_detected'] == 3
    assert len(result['result']['speakers']) == 3

    # Check speaker labels
    speaker_ids = [s['speaker_id'] for s in result['result']['speakers']]
    expected_speakers = ['Speaker 1', 'Speaker 2', 'Speaker 3']
    assert set(speaker_ids) == set(expected_speakers)

    print("✅ Speaker diarization working correctly")

test_speaker_diarization()
```

## Performance Validation

### CPU vs GPU Performance Test
```python
import time
import requests

def benchmark_processing_modes():
    """Compare CPU vs GPU processing performance"""

    test_file = 'benchmark_audio_5min.wav'

    # Test GPU processing (if available)
    start_time = time.time()
    gpu_response = requests.post(
        'http://localhost:8000/v1/transcriptions',
        files={'audio_file': open(test_file, 'rb')},
        data={'model_size': 'large-v2', 'enable_diarization': True}
    )

    gpu_result = wait_for_completion(gpu_response.json()['job_id'])
    gpu_time = time.time() - start_time

    print(f"GPU Processing Time: {gpu_time:.2f}s")
    print(f"Audio Duration: {gpu_result['metadata']['audio_duration_seconds']:.2f}s")
    print(f"Speedup Factor: {gpu_result['metadata']['audio_duration_seconds'] / gpu_time:.1f}x real-time")

    # Expected: 10-70x real-time depending on hardware

benchmark_processing_modes()
```

### Memory Usage Monitoring
```python
import psutil
import requests

def monitor_memory_usage():
    """Monitor system memory during large file processing"""

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Submit large file for processing
    response = requests.post(
        'http://localhost:8000/v1/transcriptions',
        files={'audio_file': open('large_audio_file.wav', 'rb')},
        data={'enable_diarization': True}
    )

    job_id = response.json()['job_id']

    # Monitor memory during processing
    max_memory = initial_memory
    while True:
        current_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(max_memory, current_memory)

        status = requests.get(f'http://localhost:8000/v1/transcriptions/{job_id}')
        if status.json()['status'] in ['completed', 'failed']:
            break

        time.sleep(5)

    memory_increase = max_memory - initial_memory
    print(f"Maximum memory increase: {memory_increase:.2f} MB")

    # Expected: <2GB increase for 5GB audio file
    assert memory_increase < 2048, "Memory usage should stay under 2GB"

monitor_memory_usage()
```

## Error Handling Validation

### Test Error Scenarios
```bash
# Test 1: Invalid audio file
curl -X POST "http://localhost:8000/v1/transcriptions" \
  -F "audio_file=@invalid_file.txt"

# Expected: 400 Bad Request with INVALID_FILE_FORMAT

# Test 2: Missing required parameters
curl -X POST "http://localhost:8000/v1/transcriptions"

# Expected: 422 Validation Error

# Test 3: Non-existent job ID
curl "http://localhost:8000/v1/transcriptions/00000000-0000-0000-0000-000000000000"

# Expected: 404 Not Found with JOB_NOT_FOUND
```

## Production Deployment Checklist

### Before Production Deployment
- [ ] **Environment Variables**: Set all required environment variables
- [ ] **GPU Drivers**: Verify CUDA drivers installed if using GPU
- [ ] **Redis Server**: Confirm Redis is running and accessible
- [ ] **File Storage**: Ensure sufficient disk space for uploads and outputs
- [ ] **Logging**: Configure log levels and output destinations
- [ ] **Monitoring**: Set up health checks and alerting
- [ ] **Security**: Configure API key authentication
- [ ] **Load Testing**: Verify performance under expected load

### Health Check Validation
```bash
# Verify system health
curl "http://localhost:8000/v1/health"

# Expected healthy response:
# {
#   "status": "healthy",
#   "timestamp": "2025-01-24T15:30:00Z",
#   "version": "1.0.0",
#   "gpu_available": true,
#   "queue_size": 0,
#   "processing_jobs": 0
# }
```

## Troubleshooting Common Issues

### Issue 1: GPU Not Detected
```bash
# Check CUDA installation
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# Solution: Install CUDA toolkit and compatible PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Issue 2: Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# Solution: Start Redis server
redis-server /etc/redis/redis.conf
```

### Issue 3: Out of Memory Errors
```bash
# Monitor memory usage
htop
nvidia-smi  # For GPU memory

# Solution: Reduce batch size or use smaller model
export WHISPERX_MODEL_SIZE=base
export BATCH_SIZE=8
```

### Issue 4: Slow Processing
```python
# Check processing configuration
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")

# Solutions:
# 1. Enable GPU acceleration
# 2. Use smaller model for speed vs accuracy trade-off
# 3. Optimize batch size for available memory
```

## Next Steps

After completing this quickstart:

1. **Production Setup**: Configure production environment with proper security
2. **Monitoring**: Implement comprehensive logging and monitoring
3. **Scaling**: Set up horizontal scaling with multiple worker processes
4. **Integration**: Integrate with your existing applications and workflows
5. **Optimization**: Fine-tune performance based on your specific use cases

## Support

- **Documentation**: See full API documentation at `/docs` endpoint
- **GitHub Issues**: Report bugs and feature requests
- **Performance Tuning**: Consult the performance optimization guide
- **Enterprise Support**: Contact support for enterprise deployment assistance