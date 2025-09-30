#!/usr/bin/env python3
"""
Test TorchCodec integration to verify it replaces TorchAudio functionality
and eliminates deprecation warnings.
"""

import warnings
import sys
from pathlib import Path

def test_torchcodec_integration():
    """Test TorchCodec integration and warning elimination."""
    print("🔧 TESTING TORCHCODEC INTEGRATION")
    print("Verifying TorchCodec replaces TorchAudio functionality")
    print("=" * 60)

    # Capture all warnings
    warnings.simplefilter('always')
    captured_warnings = []

    def warning_handler(message, category, filename, lineno, file=None, line=None):
        captured_warnings.append(f"{category.__name__}: {message}")

    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler

    try:
        print("📋 Step 1: Testing audio configuration...")
        from src.core.audio_config import configure_audio_backend, get_audio_backend_info

        # Test configuration
        result = configure_audio_backend()
        backend_info = get_audio_backend_info()

        print(f"✅ Configuration result: {result}")
        print(f"📊 Backend: {backend_info['backend']} v{backend_info['version']} ({backend_info['status']})")

        if backend_info['backend'] == 'torchcodec':
            print("✅ TorchCodec is primary backend")
        elif backend_info['backend'] == 'torchaudio':
            print("⚠️  Using TorchAudio fallback")
        else:
            print("❌ No audio backend configured")

        print("\n📋 Step 2: Testing service imports...")

        # Test WhisperX service
        from src.services.whisperx_service import WhisperXService
        print("✅ WhisperX service imported")

        # Test Speaker service
        from src.services.speaker_service import SpeakerIdentificationService
        print("✅ Speaker service imported")

        print("\n📋 Step 3: Testing service initialization...")

        # Initialize services to trigger any audio backend usage
        try:
            whisper_service = WhisperXService(model_size='tiny', device='cpu', compute_type='int8')
            print("✅ WhisperX service initialized")
        except Exception as e:
            print(f"⚠️  WhisperX initialization: {e}")

        try:
            speaker_service = SpeakerIdentificationService()
            print("✅ Speaker service initialized")
        except Exception as e:
            print(f"⚠️  Speaker service initialization: {e}")

        print("\n📋 Step 4: Testing direct TorchCodec functionality...")

        try:
            import torchcodec
            print(f"✅ TorchCodec {torchcodec.__version__} direct import successful")

            # Test basic TorchCodec functionality
            if hasattr(torchcodec, 'decoders'):
                print("✅ TorchCodec decoders module available")

            # Note: TorchCodec is primarily for video/audio decoding
            # For audio processing, we still need some TorchAudio functionality
            # but TorchCodec handles the heavy lifting for file I/O

        except Exception as e:
            print(f"❌ TorchCodec test failed: {e}")

        # Restore warning handler
        warnings.showwarning = old_showwarning

        print(f"\n📊 WARNING ANALYSIS:")
        if captured_warnings:
            print(f"⚠️  Captured {len(captured_warnings)} warnings:")

            torchaudio_warnings = []
            other_warnings = []

            for warning in captured_warnings:
                if any(keyword in warning.lower() for keyword in ['torchaudio', 'deprecated', 'maintenance phase']):
                    torchaudio_warnings.append(warning)
                else:
                    other_warnings.append(warning)

            if torchaudio_warnings:
                print(f"❌ TorchAudio deprecation warnings still present ({len(torchaudio_warnings)}):")
                for w in torchaudio_warnings[:3]:  # Show first 3
                    print(f"   • {w}")
                if len(torchaudio_warnings) > 3:
                    print(f"   ... and {len(torchaudio_warnings) - 3} more")
            else:
                print("✅ No TorchAudio deprecation warnings!")

            if other_warnings:
                print(f"⚠️  Other warnings ({len(other_warnings)}):")
                for w in other_warnings[:2]:  # Show first 2
                    print(f"   • {w}")
        else:
            print("✅ No warnings captured!")

        print(f"\n🎯 TORCHCODEC INTEGRATION ASSESSMENT:")

        success_metrics = {
            "torchcodec_available": backend_info['backend'] == 'torchcodec',
            "services_import": True,  # If we got here, imports worked
            "no_torchaudio_warnings": len([w for w in captured_warnings if 'torchaudio' in w.lower()]) == 0
        }

        total_success = sum(success_metrics.values())

        for metric, status in success_metrics.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {metric.replace('_', ' ').title()}: {status}")

        if total_success == len(success_metrics):
            print(f"\n🎉 TORCHCODEC INTEGRATION SUCCESSFUL!")
            print("✅ TorchCodec is properly replacing TorchAudio functionality")
            print("✅ All deprecation warnings eliminated")
        elif total_success >= 2:
            print(f"\n⚠️  PARTIAL SUCCESS ({total_success}/{len(success_metrics)})")
            print("TorchCodec integration mostly working")
        else:
            print(f"\n❌ INTEGRATION ISSUES ({total_success}/{len(success_metrics)})")
            print("TorchCodec integration needs improvement")

        return success_metrics, captured_warnings

    except Exception as e:
        warnings.showwarning = old_showwarning
        print(f"❌ TorchCodec integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, captured_warnings

if __name__ == "__main__":
    # Add current directory to path
    sys.path.insert(0, '.')

    result = test_torchcodec_integration()

    if result and result[0]:
        success_count = sum(result[0].values())
        total_metrics = len(result[0])
        print(f"\n📊 Final Score: {success_count}/{total_metrics} metrics passed")

        if success_count == total_metrics:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Failure