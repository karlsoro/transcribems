# GPU Acceleration Guide for TranscribeMS

## Overview

TranscribeMS now supports GPU acceleration for significantly improved transcription performance. The system automatically detects GPU availability and optimizes settings for the best performance.

## Performance Improvements

### GPU vs CPU Performance Comparison

| Mode | Processing Speed | Realtime Factor | Best Use Case |
|------|-----------------|-----------------|---------------|
| **GPU (CUDA)** | 6.97x realtime | Up to 7x faster | Large files, production workloads |
| **CPU** | 1-2x realtime | Baseline | Small files, development |

### Real-World Performance Examples

**Large File Test (111MB, 47 minutes of audio):**
- **GPU Mode**: 6.8 minutes processing time (6.97x realtime)
- **CPU Mode**: ~47+ minutes processing time (1x realtime or slower)
- **Speedup**: ~7x faster with GPU

## Hardware Requirements

### Minimum GPU Requirements
- **NVIDIA GPU** with CUDA Compute Capability 3.5+
- **VRAM**: 4GB minimum, 8GB+ recommended for large files
- **CUDA Version**: 11.8 or compatible

### Supported GPUs
- RTX Series: RTX 3060, RTX 3070, RTX 3080, RTX 3090, RTX 4070, RTX 4080, RTX 4090
- GTX Series: GTX 1060 6GB+, GTX 1070, GTX 1080, GTX 1660 Ti
- Tesla/Quadro: Most modern Tesla and Quadro cards

### Tested Configurations
- **RTX 3060 12GB**: Excellent performance, tested up to 111MB files
- **CPU Fallback**: Automatic fallback when GPU unavailable

## Software Requirements

### PyTorch CUDA Setup

```bash
# Install CUDA-enabled PyTorch (recommended versions)
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install compatible NumPy version
pip install "numpy<2"

# Install CUDNN 8 for compatibility
pip install nvidia-cudnn-cu11==8.7.0.84
```

### Environment Variables (Auto-configured)

The service automatically configures these when GPU is detected:
```bash
CUDA_VISIBLE_DEVICES=0
OMP_NUM_THREADS=8
MKL_NUM_THREADS=8
```

## Usage

### Automatic GPU Detection (Recommended)

```python
from services.simple_whisperx_cli import SimpleWhisperXCLI

# Service automatically detects and uses GPU if available
cli = SimpleWhisperXCLI()

result = await cli.transcribe_audio(
    audio_path="large_audio_file.wav",
    model="large-v2",  # Use largest model for best quality
    enable_diarization=True
)

print(f"Device used: {result['device_used']}")
print(f"Processing speed: {result['processing_speed_mb_per_sec']:.2f} MB/s")
print(f"Realtime factor: {result['realtime_factor']:.2f}x")
```

### Force Specific Device

```python
# Force GPU usage
result = await cli.transcribe_audio(
    audio_path="audio.wav",
    device="cuda",
    compute_type="float16",
    batch_size=16
)

# Force CPU usage
result = await cli.transcribe_audio(
    audio_path="audio.wav",
    device="cpu",
    compute_type="float32",
    batch_size=1
)
```

## Configuration Options

### GPU Optimizations (Auto-configured)

| Parameter | GPU Value | CPU Value | Description |
|-----------|-----------|-----------|-------------|
| `device` | `cuda` | `cpu` | Processing device |
| `compute_type` | `float16` | `float32` | Precision mode |
| `batch_size` | `16` | `1` | Batch processing size |

### Model Recommendations

| Model | GPU VRAM | Processing Speed | Quality |
|-------|----------|------------------|---------|
| `base` | 2GB | Fastest | Good |
| `small` | 3GB | Fast | Better |
| `medium` | 4GB | Medium | Very Good |
| `large` | 6GB | Slower | Excellent |
| `large-v2` | 6GB | Slower | Best |

## Performance Metrics

The service now provides detailed performance metrics:

```python
result = await cli.transcribe_audio("audio.wav")

# Performance metrics available in result
print(f"Audio duration: {result['audio_duration_seconds']:.1f}s")
print(f"Processing time: {result['processing_time_seconds']:.1f}s")
print(f"Realtime factor: {result['realtime_factor']:.2f}x")
print(f"File processing speed: {result['processing_speed_mb_per_sec']:.2f} MB/s")
print(f"Device used: {result['device_used']}")
print(f"GPU available: {result['gpu_available']}")
```

## Troubleshooting

### Common Issues

#### 1. CUDA Not Available
```
Error: GPU not detected, falling back to CPU
```
**Solution**: Install CUDA-enabled PyTorch and check GPU drivers.

#### 2. CUDNN Library Issues
```
Error: libcudnn.so.X: cannot open shared object file
```
**Solution**: Install compatible CUDNN version (8.7.0.84 recommended).

#### 3. Out of Memory
```
Error: CUDA out of memory
```
**Solutions**:
- Reduce batch size: `batch_size=8` or `batch_size=4`
- Use smaller model: `model="medium"` instead of `large-v2`
- Use float32: `compute_type="float32"`

#### 4. Compatibility Issues
```
Error: forward compatibility was attempted on non supported HW
```
**Solution**: Check GPU compute capability and CUDA version compatibility.

### Validation Commands

```bash
# Check GPU availability
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Check GPU details
python -c "import torch; print('GPU name:', torch.cuda.get_device_name(0))"

# Run service validation
python test_service_validation.py
```

## Best Practices

### For Production Workloads
1. **Use GPU when available** - 7x performance improvement
2. **Use largest model** - `large-v2` for best quality
3. **Enable diarization** - Better speaker separation
4. **Monitor VRAM usage** - Adjust batch size if needed

### For Development
1. **Use base model** - Faster iteration
2. **CPU mode acceptable** - For small test files
3. **Disable diarization** - For speed during testing

### For Large Files (>1GB)
1. **GPU required** - CPU will be too slow
2. **Use large-v2 model** - Best quality for long content
3. **Monitor memory** - May need batch size adjustment
4. **Increase timeout** - `timeout_minutes=120` for very large files

## Migration Notes

### From Previous CPU-Only Version

The service is backward compatible. Existing code will work unchanged:

```python
# This code works exactly as before
cli = SimpleWhisperXCLI()
result = await cli.transcribe_audio("audio.wav")

# But now automatically uses GPU when available!
```

### New Features Available

1. **Automatic GPU detection**
2. **Performance metrics in results**
3. **Optimized batch processing**
4. **Better error handling**
5. **Detailed logging**

## Performance Benchmarks

Based on testing with RTX 3060 12GB:

| File Size | Audio Duration | GPU Time | CPU Time | GPU Speedup |
|-----------|----------------|----------|----------|-------------|
| 10MB | 5 min | 45s | 5min+ | 6.7x |
| 50MB | 25 min | 3.5min | 25min+ | 7.1x |
| 111MB | 47 min | 6.8min | 47min+ | 6.9x |

**Average GPU speedup: ~7x faster than CPU**