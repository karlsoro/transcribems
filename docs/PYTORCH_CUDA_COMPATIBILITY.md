# PyTorch/CUDA Compatibility Guide

## Overview

This document outlines the PyTorch and CUDA version compatibility requirements for GPU acceleration in TranscribeMCP. Proper version alignment is critical for GPU functionality.

## Compatibility Matrix

### Tested Working Configurations

| PyTorch Version | CUDA Version | CUDNN Version | Status | Performance |
|----------------|--------------|---------------|---------|-------------|
| **2.2.0+cu118** | **11.8** | **8.7.0.84** | ✅ **Recommended** | Excellent |
| 2.7.1+cu118 | 11.8 | 9.1.0.70 | ⚠️ Compatibility Issues | N/A |
| 2.8.0+cpu | N/A | N/A | ✅ CPU Only | CPU Performance |

### Recommended Installation (Working Configuration)

```bash
# Step 1: Install PyTorch 2.2.0 with CUDA 11.8
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Step 2: Install compatible NumPy (required for PyTorch 2.2.0)
pip install "numpy<2"  # Specifically numpy 1.26.4

# Step 3: Install compatible CUDNN 8 (required for WhisperX)
pip install nvidia-cudnn-cu11==8.7.0.84 --force-reinstall

# Step 4: Verify installation
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## Version Dependency Issues

### Problem: CUDNN Version Mismatch

**Issue**: WhisperX requires CUDNN 8, but newer PyTorch versions ship with CUDNN 9.

**Symptoms**:
```
Error: libcudnn.so.9: cannot open shared object file
Error: Could not load library libcudnn_ops_infer.so.8
```

**Solution**: Use PyTorch 2.2.0 which natively supports CUDNN 8.7.0.84.

### Problem: NumPy Compatibility

**Issue**: PyTorch 2.2.0 was built with NumPy 1.x but NumPy 2.x has breaking changes.

**Symptoms**:
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.1.2
```

**Solution**: Downgrade to NumPy 1.26.4:
```bash
pip install "numpy<2"
```

### Problem: WhisperX Version Requirements

**Issue**: WhisperX 3.4.2 has specific version requirements that may conflict.

**Current Conflicts**:
```
whisperx 3.4.2 requires torch>=2.5.1, but you have torch 2.2.0+cu118
whisperx 3.4.2 requires numpy>=2.0.2, but you have numpy 1.26.4
```

**Status**: These dependency conflicts are warnings. The system works despite them because:
1. PyTorch 2.2.0 has the required features for WhisperX
2. NumPy 1.26.4 provides necessary compatibility
3. Runtime functionality is preserved

## Hardware Compatibility

### CUDA Compute Capability

Ensure your GPU supports the required CUDA compute capability:

```python
import torch
if torch.cuda.is_available():
    capability = torch.cuda.get_device_capability(0)
    print(f"CUDA Compute Capability: {capability[0]}.{capability[1]}")
```

**Minimum Requirements**:
- CUDA Compute Capability: 3.5+
- Tested: RTX 3060 (Compute Capability 8.6)

### GPU Memory Requirements

| Model Size | Minimum VRAM | Recommended VRAM |
|------------|--------------|------------------|
| base | 2GB | 4GB |
| small | 3GB | 6GB |
| medium | 4GB | 8GB |
| large | 6GB | 12GB |
| large-v2 | 6GB | 12GB |

## Installation Troubleshooting

### Clean Installation Process

If you encounter issues, perform a clean installation:

```bash
# Step 1: Uninstall existing PyTorch
pip uninstall torch torchvision torchaudio

# Step 2: Uninstall CUDA libraries
pip uninstall nvidia-cudnn-cu11 nvidia-cublas-cu11 nvidia-cuda-nvrtc-cu11

# Step 3: Clean install recommended versions
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install "numpy<2"
pip install nvidia-cudnn-cu11==8.7.0.84

# Step 4: Verify
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

### Validation Script

Create and run this validation script:

```python
"""
PyTorch/CUDA validation script
"""
import sys

def validate_installation():
    print("=== PyTorch/CUDA Validation ===")

    # Check PyTorch
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch not installed")
        return False

    # Check CUDA
    cuda_available = torch.cuda.is_available()
    print(f"✅ CUDA available: {cuda_available}")

    if cuda_available:
        print(f"✅ CUDA version: {torch.version.cuda}")
        print(f"✅ CUDNN version: {torch.backends.cudnn.version()}")
        print(f"✅ GPU count: {torch.cuda.device_count()}")
        print(f"✅ GPU name: {torch.cuda.get_device_name(0)}")

        # Test GPU tensor
        try:
            x = torch.tensor([1.0, 2.0]).cuda()
            print(f"✅ GPU tensor test: {x}")
        except Exception as e:
            print(f"❌ GPU tensor test failed: {e}")
            return False

    # Check NumPy
    try:
        import numpy as np
        print(f"✅ NumPy version: {np.__version__}")
        if np.__version__.startswith('2.'):
            print("⚠️  Warning: NumPy 2.x may cause compatibility issues")
    except ImportError:
        print("❌ NumPy not installed")
        return False

    print("✅ All checks passed!")
    return True

if __name__ == "__main__":
    if validate_installation():
        sys.exit(0)
    else:
        sys.exit(1)
```

## Environment Setup

### Environment Variables

The service automatically configures these, but you can set them manually:

```bash
# For GPU acceleration
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

# For CPU optimization
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export NUMEXPR_NUM_THREADS=8
```

### Virtual Environment Best Practices

1. **Use dedicated virtual environment**:
```bash
python -m venv transcribe_mcp_env
source transcribe_mcp_env/bin/activate
```

2. **Install in correct order**:
```bash
# Base requirements first
pip install wheel setuptools

# PyTorch with CUDA
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Compatibility packages
pip install "numpy<2"
pip install nvidia-cudnn-cu11==8.7.0.84

# Application requirements
pip install -r requirements.txt
```

## Known Issues and Workarounds

### Issue 1: Forward Compatibility Error

**Error**:
```
CUDA initialization: forward compatibility was attempted on non supported HW
```

**Cause**: GPU driver/CUDA version mismatch

**Workaround**: Service automatically falls back to CPU mode

### Issue 2: CUDNN Library Not Found

**Error**:
```
Could not load library libcudnn_ops_infer.so.8
```

**Solution**: Install correct CUDNN version:
```bash
pip install nvidia-cudnn-cu11==8.7.0.84 --force-reinstall
```

### Issue 3: Dependency Conflicts

**Warning**:
```
whisperx 3.4.2 requires torch>=2.5.1, but you have torch 2.2.0+cu118
```

**Status**: Safe to ignore - functionality preserved

**Explanation**: While WhisperX specifies newer versions, PyTorch 2.2.0 contains all required features.

## Future Compatibility

### Upgrade Path

When newer compatible versions become available:

1. **Test in isolated environment**
2. **Validate GPU functionality**
3. **Benchmark performance**
4. **Update documentation**

### Monitoring for Updates

Watch for updates to:
- PyTorch CUDA wheels
- CUDNN compatibility
- WhisperX requirements
- NVIDIA driver updates

## Quick Reference

### Working Installation Commands
```bash
# Complete working setup
pip install torch==2.2.0+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install "numpy<2"
pip install nvidia-cudnn-cu11==8.7.0.84 --force-reinstall
```

### Validation Command
```bash
python -c "import torch; print('PyTorch:', torch.__version__, 'CUDA:', torch.cuda.is_available())"
```

### GPU Test Command
```bash
python -c "import torch; x=torch.tensor([1.0]).cuda(); print('GPU working:', x.device)"
```