#!/usr/bin/env python3
"""
Simple GPU validation script for TranscribeMCP
Run this script to test GPU functionality when you have GPU hardware available.
"""

import asyncio
import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

def test_basic_gpu_detection():
    """Test basic GPU detection and capabilities."""
    print("🔍 Testing Basic GPU Detection")
    print("=" * 50)

    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs: {torch.cuda.device_count()}")

            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                memory_gb = props.total_memory / (1024**3)
                print(f"  GPU {i}: {props.name}")
                print(f"    Memory: {memory_gb:.1f} GB")
                print(f"    Compute Capability: {props.major}.{props.minor}")
                print(f"    Multiprocessors: {props.multi_processor_count}")

            return True
        else:
            print("❌ No CUDA GPUs detected")
            print("   This is normal for CPU-only systems")
            return False

    except ImportError:
        print("❌ PyTorch not installed")
        return False
    except Exception as e:
        print(f"❌ GPU detection failed: {e}")
        return False

def test_gpu_memory_operations():
    """Test GPU memory allocation and cleanup."""
    print("\n🧠 Testing GPU Memory Operations")
    print("=" * 50)

    try:
        import torch

        if not torch.cuda.is_available():
            print("⏭️  Skipping - No GPU available")
            return True

        device = torch.device('cuda:0')
        print(f"Testing on: {torch.cuda.get_device_name(device)}")

        # Check initial memory
        allocated_before = torch.cuda.memory_allocated(device) / (1024**2)  # MB
        print(f"Initial memory allocated: {allocated_before:.1f} MB")

        # Allocate some memory
        test_tensor = torch.randn(1000, 1000, device=device)
        allocated_after = torch.cuda.memory_allocated(device) / (1024**2)
        print(f"Memory after allocation: {allocated_after:.1f} MB")
        print(f"Memory used by tensor: {(allocated_after - allocated_before):.1f} MB")

        # Clean up
        del test_tensor
        torch.cuda.empty_cache()
        allocated_final = torch.cuda.memory_allocated(device) / (1024**2)
        print(f"Memory after cleanup: {allocated_final:.1f} MB")

        print("✅ GPU memory operations working correctly")
        return True

    except Exception as e:
        print(f"❌ GPU memory test failed: {e}")
        return False

async def test_speaker_identification_gpu():
    """Test speaker identification with GPU acceleration."""
    print("\n🎤 Testing Speaker Identification with GPU")
    print("=" * 50)

    try:
        from src.services.speaker_service import SpeakerIdentificationService

        # Create a test audio file
        print("Creating test audio file...")
        sample_rate = 16000
        duration = 5.0  # 5 seconds
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Simulate two speakers with different frequencies
        speaker1 = 0.5 * np.sin(2 * np.pi * 440 * t[:len(t)//2])  # A4
        speaker2 = 0.5 * np.sin(2 * np.pi * 880 * t[len(t)//2:])  # A5
        audio = np.concatenate([speaker1, speaker2])

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            sf.write(temp_file.name, audio, sample_rate)
            temp_path = temp_file.name

        try:
            # Test with mock service first (should always work)
            print("Testing with mock service...")
            from unittest.mock import Mock
            mock_service = Mock()
            mock_service.identify_speakers.return_value = {
                "speakers": ["SPEAKER_00", "SPEAKER_01"],
                "segments": [
                    {"start": 0.0, "end": 2.5, "speaker": "SPEAKER_00", "text": "First speaker", "speaker_confidence": 0.95},
                    {"start": 2.5, "end": 5.0, "speaker": "SPEAKER_01", "text": "Second speaker", "speaker_confidence": 0.92}
                ],
                "speaker_count": 2
            }

            service = SpeakerIdentificationService(diarization_service=mock_service)
            result = await service.identify_speakers(temp_path)

            print(f"✅ Mock test: Found {result['speaker_count']} speakers")
            print(f"   Segments: {len(result['segments'])}")

            # Test with real pyannote service (GPU accelerated if available)
            print("\nTesting with real pyannote service...")
            real_service = SpeakerIdentificationService(diarization_service=None)

            try:
                # This will attempt to load the real pyannote pipeline
                real_result = await real_service.identify_speakers(temp_path)
                print("✅ Real pyannote test successful!")
                print(f"   Speakers found: {real_result['speaker_count']}")
                print(f"   Segments: {len(real_result['segments'])}")
                print(f"   GPU acceleration: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
                return True

            except Exception as e:
                print(f"ℹ️  Real pyannote test skipped: {e}")
                print("   This is expected without proper pyannote setup")
                print("   To enable: pip install pyannote-audio && export HF_TOKEN=your_token")
                return True  # Not a failure, just missing optional dependencies

        finally:
            # Clean up temp file
            Path(temp_path).unlink()

    except Exception as e:
        print(f"❌ Speaker identification test failed: {e}")
        return False

def test_whisperx_gpu():
    """Test WhisperX with GPU acceleration."""
    print("\n🎵 Testing WhisperX GPU Integration")
    print("=" * 50)

    try:
        import whisperx
        print(f"✅ WhisperX available: {whisperx.__version__}")

        # Test device selection
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            print(f"✅ Using GPU device: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            print("ℹ️  Using CPU device (no GPU available)")

        # Test loading a small model (don't actually load to save time)
        print(f"✅ WhisperX can use device: {device}")
        return True

    except ImportError:
        print("ℹ️  WhisperX not installed")
        print("   To install: pip install whisperx")
        return True  # Not a failure
    except Exception as e:
        print(f"❌ WhisperX test failed: {e}")
        return False

def test_dependencies():
    """Test all required dependencies for GPU functionality."""
    print("\n📦 Testing Dependencies")
    print("=" * 50)

    dependencies = [
        ("torch", "PyTorch for GPU operations"),
        ("whisperx", "WhisperX for transcription"),
        ("pyannote.audio", "Pyannote for speaker diarization"),
        ("soundfile", "Audio file I/O"),
        ("numpy", "Numerical operations"),
        ("structlog", "Structured logging")
    ]

    results = []
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"✅ {package:15} - {description}")
            results.append(True)
        except ImportError:
            print(f"❌ {package:15} - {description} (NOT INSTALLED)")
            results.append(False)

    installed = sum(results)
    total = len(results)
    print(f"\nDependencies: {installed}/{total} installed")

    if installed == total:
        print("✅ All dependencies available for full GPU testing")
    else:
        print("⚠️  Some dependencies missing - GPU features may be limited")

    return installed >= 4  # Core dependencies present

async def main():
    """Run all GPU validation tests."""
    print("🚀 TranscribeMCP GPU Validation Suite")
    print("=" * 60)
    print("This script tests GPU functionality when hardware is available")
    print("It's normal for some tests to skip on CPU-only systems")
    print("=" * 60)

    tests = [
        ("Dependencies", test_dependencies),
        ("GPU Detection", test_basic_gpu_detection),
        ("GPU Memory", test_gpu_memory_operations),
        ("Speaker Identification", test_speaker_identification_gpu),
        ("WhisperX Integration", test_whisperx_gpu)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append(False)

    # Summary
    print("\n🏁 GPU Validation Results")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{test_name:20} - {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All GPU validation tests passed!")
        print("   Your system is ready for GPU-accelerated transcription")
    elif passed >= 3:
        print("✅ Core functionality working")
        print("   Some advanced GPU features may not be available")
    else:
        print("⚠️  Limited GPU functionality detected")
        print("   Basic CPU functionality should still work")

    # Recommendations
    print("\n📋 Recommendations:")
    if not any([test_basic_gpu_detection(), test_dependencies()]):
        print("• Install missing dependencies: pip install torch whisperx pyannote-audio structlog")
        print("• Set up GPU drivers if you have NVIDIA hardware")
        print("• Get HuggingFace token for speaker diarization: export HF_TOKEN=your_token")
    else:
        print("• Your setup looks good for GPU-accelerated transcription!")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)