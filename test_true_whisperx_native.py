#!/usr/bin/env python3
"""
Test TRUE native WhisperX usage - exactly as designed by the WhisperX team.
No custom services, no manual integrations, just pure WhisperX as intended.
"""

import time
import os
from pathlib import Path

def test_true_native_whisperx():
    """Test WhisperX exactly as the documentation shows."""
    print("🔥 TESTING TRUE NATIVE WHISPERX")
    print("Using WhisperX exactly as designed - no custom integrations")
    print("=" * 70)

    # Find test audio
    audio_files = list(Path(".cache/recordings").glob("**/*.aac"))
    if not audio_files:
        print("❌ No audio files found")
        return

    audio_file = str(audio_files[0])
    file_size = Path(audio_file).stat().st_size / (1024*1024)
    print(f"📁 Audio file: {Path(audio_file).name}")
    print(f"📊 Size: {file_size:.1f}MB")

    try:
        # Import and configure exactly as WhisperX documentation
        print("\n📋 Step 1: Import and configure WhisperX...")

        # Configure audio backend first
        import os
        os.environ['TORCHAUDIO_BACKEND'] = 'soundfile'

        import whisperx
        import torch

        device = "cpu"
        compute_type = "int8"  # CPU optimized

        print(f"✅ WhisperX imported, device: {device}, compute: {compute_type}")

        # Step 1: Load model
        print("\n📋 Step 2: Load WhisperX model...")
        start_time = time.time()

        model = whisperx.load_model("small", device, compute_type=compute_type)
        model_time = time.time() - start_time

        print(f"✅ Model loaded in {model_time:.1f}s")

        # Step 2: Load audio
        print("\n📋 Step 3: Load audio...")
        audio_start = time.time()

        audio = whisperx.load_audio(audio_file)
        audio_duration = len(audio) / 16000  # WhisperX uses 16kHz
        audio_time = time.time() - audio_start

        print(f"✅ Audio loaded in {audio_time:.1f}s")
        print(f"🎵 Duration: {audio_duration:.1f}s ({audio_duration/60:.1f} minutes)")

        # Step 3: Transcribe
        print("\n📋 Step 4: Transcribe...")
        transcribe_start = time.time()

        result = model.transcribe(audio, batch_size=16)
        transcribe_time = time.time() - transcribe_start

        print(f"✅ Transcription completed in {transcribe_time:.1f}s")
        print(f"📄 Language: {result.get('language', 'unknown')}")
        print(f"📊 Segments: {len(result.get('segments', []))}")

        # Performance check
        realtime_factor = audio_duration / transcribe_time if transcribe_time > 0 else 0
        print(f"📈 Realtime factor: {realtime_factor:.1f}x")

        if realtime_factor > 1:
            print(f"✅ GOOD: {realtime_factor:.1f}x faster than real-time")
        else:
            print(f"❌ SLOW: {realtime_factor:.1f}x - slower than real-time")

        # Step 4: Alignment (optional but recommended)
        print("\n📋 Step 5: Align transcript...")
        align_start = time.time()

        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"],
                device=device
            )

            result = whisperx.align(
                result["segments"],
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False
            )

            align_time = time.time() - align_start
            print(f"✅ Alignment completed in {align_time:.1f}s")

        except Exception as e:
            print(f"⚠️  Alignment failed: {e}")
            align_time = 0

        # Step 5: Speaker Diarization (the proper way)
        print("\n📋 Step 6: Speaker diarization (native WhisperX)...")
        diarize_start = time.time()

        # Note: This requires HuggingFace token for pyannote model
        # Since we don't have one, we'll skip this step but show how it should work

        try:
            # This is how WhisperX native diarization should work:
            # diarize_model = whisperx.DiarizationPipeline(use_auth_token=YOUR_HF_TOKEN, device=device)
            # diarize_segments = diarize_model(audio)
            # result = whisperx.assign_word_speakers(diarize_segments, result)

            print("⚠️  Skipping native diarization (requires HuggingFace token)")
            print("💡 This is where proper WhisperX diarization would happen")
            print("📋 Process: DiarizationPipeline -> assign_word_speakers")

            diarize_time = 0

        except Exception as e:
            print(f"⚠️  Diarization setup failed: {e}")
            diarize_time = 0

        total_time = time.time() - start_time

        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   ⏱️  Model loading: {model_time:.1f}s")
        print(f"   📁 Audio loading: {audio_time:.1f}s")
        print(f"   🎯 Transcription: {transcribe_time:.1f}s")
        print(f"   🔧 Alignment: {align_time:.1f}s")
        print(f"   👥 Diarization: {diarize_time:.1f}s")
        print(f"   📊 Total: {total_time:.1f}s")
        print(f"   🎵 Audio duration: {audio_duration:.1f}s")
        print(f"   📈 Overall realtime factor: {audio_duration / transcribe_time:.1f}x")

        # Show results
        segments = result.get('segments', [])
        if segments:
            print(f"\n📋 SAMPLE RESULTS (first 3 segments):")
            for i, segment in enumerate(segments[:3]):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')[:60] + '...' if len(segment.get('text', '')) > 60 else segment.get('text', '')
                speaker = segment.get('speaker', 'None')
                print(f"   {i+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {text}")

        # Assessment
        if transcribe_time < audio_duration:
            print(f"\n🎉 SUCCESS: Native WhisperX transcription is faster than real-time!")
            print(f"✅ This is the performance we should expect")
        else:
            print(f"\n❌ ISSUE: Even native WhisperX is slower than real-time")
            print(f"⚠️  This suggests a fundamental system issue")

        return True

    except Exception as e:
        print(f"❌ Native WhisperX test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_true_native_whisperx()