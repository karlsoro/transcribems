
"""
Audio backend configuration using TorchCodec (replacement for deprecated TorchAudio).
TorchCodec provides modern audio/video decoding and encoding capabilities.
Import this at the start of audio processing modules.
"""

import os
import warnings

# Suppress all audio-related warnings during transition
warnings.filterwarnings("ignore", message=".*torchaudio.*")
warnings.filterwarnings("ignore", message=".*TorchAudio.*")
warnings.filterwarnings("ignore", message=".*TorchCodec.*")
warnings.filterwarnings("ignore", category=UserWarning)

def configure_audio_backend():
    """Configure modern audio backend using TorchCodec exclusively."""
    try:
        # Use TorchCodec for modern audio processing
        import torchcodec
        # Configure environment
        os.environ.setdefault('AUDIO_BACKEND', 'torchcodec')
        print(f"✅ TorchCodec {torchcodec.__version__} configured for audio processing")
        return True
    except ImportError:
        print("❌ TorchCodec not available - install with: pip install torchcodec")
        return False

def get_audio_backend_info():
    """Get information about the current audio backend."""
    try:
        import torchcodec
        return {
            "backend": "torchcodec",
            "version": torchcodec.__version__,
            "status": "modern"
        }
    except ImportError:
        return {
            "backend": "none",
            "version": "unknown",
            "status": "torchcodec_required"
        }

# Auto-configure when imported
configure_audio_backend()
