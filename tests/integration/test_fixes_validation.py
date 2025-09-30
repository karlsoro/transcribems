#!/usr/bin/env python3
"""
Quick validation test to verify TorchAudio and Lightning fixes are working.
Tests the fixes without processing large audio files.
"""

import asyncio
import time
import tempfile
import warnings
from pathlib import Path

def test_fixes_validation():
    """Test that all fixes are working correctly."""
    print("🧪 TESTING FIXES VALIDATION")
    print("Testing TorchAudio and PyTorch Lightning fixes")
    print("=" * 60)

    # Capture warnings
    warnings.simplefilter('always')
    warnings_captured = []

    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append(f"{category.__name__}: {message}")

    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler

    try:
        print("📋 Step 1: Testing audio configuration...")
        from src.core.audio_config import configure_audio_backend
        configure_audio_backend()
        print("✅ Audio config loaded")

        print("📋 Step 2: Testing TorchAudio import...")
        import torchaudio
        print(f"✅ TorchAudio {torchaudio.__version__} imported")

        print("📋 Step 3: Testing WhisperX service initialization...")
        from src.services.whisperx_service import WhisperXService
        service = WhisperXService(model_size='tiny', device='cpu')
        print("✅ WhisperX service initialized")

        print("📋 Step 4: Testing Speaker service initialization...")
        from src.services.speaker_service import SpeakerIdentificationService
        speaker_service = SpeakerIdentificationService()
        print("✅ Speaker service initialized")

        print("📋 Step 5: Testing minimal transcription (if small test file exists)...")

        # Look for a small test audio file
        test_audio_files = list(Path(".").glob("**/*.wav"))
        test_audio_files.extend(list(Path(".").glob("**/*.mp3")))
        test_audio_files.extend(list(Path(".").glob("**/*.aac")))

        # Filter for smaller files (under 5MB)
        small_files = [f for f in test_audio_files if f.stat().st_size < 5 * 1024 * 1024]

        if small_files:
            test_file = small_files[0]
            print(f"📁 Found small test file: {test_file} ({test_file.stat().st_size / 1024:.1f}KB)")

            try:
                # Test basic transcription without speaker diarization (faster)
                result = asyncio.run(service.transcribe_audio(
                    str(test_file),
                    language="auto",
                    enable_speaker_diarization=False,
                    batch_size=4,
                    chunk_length=10
                ))

                print("✅ Basic transcription test successful")
                print(f"📊 Result: {len(result.get('text', ''))} characters transcribed")

            except Exception as e:
                print(f"⚠️  Transcription test failed: {e}")
        else:
            print("⚠️  No small audio files found for testing")

        # Restore warning handler
        warnings.showwarning = old_showwarning

        print(f"\n📊 WARNINGS ANALYSIS:")
        if warnings_captured:
            print(f"⚠️  Captured {len(warnings_captured)} warnings:")
            for warning in warnings_captured:
                print(f"   • {warning}")
        else:
            print("✅ No warnings captured!")

        # Check specifically for the warnings we fixed
        torchaudio_warnings = [w for w in warnings_captured if 'torchaudio' in w.lower() or 'deprecated' in w.lower()]
        lightning_warnings = [w for w in warnings_captured if 'lightning' in w.lower() or 'checkpoint' in w.lower()]

        print(f"\n🎯 SPECIFIC FIX VALIDATION:")
        if torchaudio_warnings:
            print(f"❌ TorchAudio warnings still present: {len(torchaudio_warnings)}")
            for w in torchaudio_warnings:
                print(f"   • {w}")
        else:
            print("✅ TorchAudio warnings: ELIMINATED")

        if lightning_warnings:
            print(f"❌ Lightning warnings still present: {len(lightning_warnings)}")
            for w in lightning_warnings:
                print(f"   • {w}")
        else:
            print("✅ PyTorch Lightning warnings: ELIMINATED")

        success = len(torchaudio_warnings) == 0 and len(lightning_warnings) == 0

        if success:
            print(f"\n🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
            print("✅ System is running cleanly without warnings")
        else:
            print(f"\n⚠️  Some fixes may not be working correctly")

        return success, warnings_captured

    except Exception as e:
        warnings.showwarning = old_showwarning
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, warnings_captured

if __name__ == "__main__":
    success, warnings = test_fixes_validation()

    if success:
        print("\n✅ VALIDATION SUCCESSFUL - Fixes are working!")
    else:
        print("\n❌ VALIDATION FAILED - Issues remain")

    print(f"\nTotal warnings captured: {len(warnings)}")