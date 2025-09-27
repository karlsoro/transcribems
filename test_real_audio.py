"""Real audio file testing with WhisperX and speaker diarization.

This script tests the actual transcription and speaker identification
functionality using the real meeting recordings.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any

# Import our services
from src.services.speaker_service import SpeakerIdentificationService
from src.services.transcription_service import TranscriptionService

async def test_whisperx_with_real_audio():
    """Test WhisperX transcription with real meeting recordings."""

    print("🎙️  Testing Real Audio Transcription with Speaker Identification")
    print("=" * 70)

    # Find real audio files
    recordings_dir = Path("recordings")
    audio_files = list(recordings_dir.rglob("*.aac"))

    if not audio_files:
        print("❌ No .aac files found in recordings directory")
        return

    print(f"📁 Found {len(audio_files)} audio files:")
    for audio_file in audio_files:
        file_size = audio_file.stat().st_size / (1024 * 1024)  # MB
        print(f"   {audio_file.name}: {file_size:.1f} MB")

    # Test with the first audio file
    test_file = audio_files[0]
    print(f"\\n🧪 Testing with: {test_file}")

    try:
        # Test 1: Direct WhisperX transcription (without speaker service)
        print("\\n📝 Test 1: Basic WhisperX Transcription")
        print("-" * 40)

        start_time = time.time()

        # Import WhisperX directly
        import whisperx
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"Device: {device}, Compute type: {compute_type}")

        # Load model
        print("Loading WhisperX model...")
        model = whisperx.load_model("large-v2", device, compute_type=compute_type)

        # Load and transcribe audio
        print("Loading audio file...")
        audio = whisperx.load_audio(str(test_file))

        print("Transcribing audio...")
        result = model.transcribe(audio, batch_size=16)

        transcription_time = time.time() - start_time

        print(f"✅ Basic transcription completed in {transcription_time:.1f} seconds")
        print(f"📊 Segments found: {len(result.get('segments', []))}")

        # Show first few segments
        segments = result.get('segments', [])[:3]
        for i, segment in enumerate(segments):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            print(f"   [{start:.1f}s - {end:.1f}s]: {text}")

        # Test 2: Speaker Diarization
        print("\\n👥 Test 2: Speaker Diarization")
        print("-" * 40)

        start_time = time.time()

        # Load diarization model
        print("Loading diarization model...")
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=None, device=device)

        # Assign speaker labels
        print("Performing speaker diarization...")
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)

        diarization_time = time.time() - start_time

        print(f"✅ Speaker diarization completed in {diarization_time:.1f} seconds")

        # Analyze speakers
        speakers = set()
        for segment in result.get('segments', []):
            if 'speaker' in segment:
                speakers.add(segment['speaker'])

        print(f"👥 Speakers identified: {len(speakers)} ({', '.join(sorted(speakers))})")

        # Show speaker segments
        for i, segment in enumerate(result.get('segments', [])[:5]):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            speaker = segment.get('speaker', 'Unknown')
            print(f"   [{start:.1f}s - {end:.1f}s] {speaker}: {text}")

        # Test 3: Our Speaker Service Integration
        print("\\n🔧 Test 3: Speaker Service Integration")
        print("-" * 40)

        # Create mock diarization service that returns the WhisperX results
        class MockWhisperXService:
            def identify_speakers(self, audio_path):
                return {
                    "speakers": list(speakers),
                    "segments": [
                        {
                            "start": seg.get('start', 0),
                            "end": seg.get('end', 0),
                            "speaker": seg.get('speaker', 'SPEAKER_00'),
                            "text": seg.get('text', '').strip(),
                            "speaker_confidence": 0.95
                        }
                        for seg in result.get('segments', [])
                    ],
                    "speaker_count": len(speakers)
                }

        # Test our service
        mock_service = MockWhisperXService()
        speaker_service = SpeakerIdentificationService(diarization_service=mock_service)

        service_result = await speaker_service.identify_speakers(str(test_file))

        print(f"✅ Speaker service integration successful")
        print(f"📊 Service returned {service_result['speaker_count']} speakers")
        print(f"📊 Service returned {len(service_result['segments'])} segments")

        # Save results
        output_file = Path("real_audio_test_results.json")
        test_results = {
            "test_file": str(test_file),
            "file_size_mb": test_file.stat().st_size / (1024 * 1024),
            "transcription_time_seconds": transcription_time,
            "diarization_time_seconds": diarization_time,
            "total_time_seconds": transcription_time + diarization_time,
            "speakers_found": len(speakers),
            "speakers_list": list(speakers),
            "segments_count": len(result.get('segments', [])),
            "service_integration": {
                "speakers_count": service_result['speaker_count'],
                "segments_count": len(service_result['segments']),
                "diarization_enabled": service_result.get('diarization_enabled', True)
            },
            "sample_segments": [
                {
                    "start": seg.get('start', 0),
                    "end": seg.get('end', 0),
                    "speaker": seg.get('speaker', 'Unknown'),
                    "text": seg.get('text', '').strip()
                }
                for seg in result.get('segments', [])[:10]
            ]
        }

        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2)

        print(f"\\n💾 Results saved to: {output_file}")

        # Summary
        print("\\n📋 SUMMARY")
        print("=" * 70)
        print(f"✅ File: {test_file.name} ({test_results['file_size_mb']:.1f} MB)")
        print(f"✅ Transcription: {transcription_time:.1f}s")
        print(f"✅ Diarization: {diarization_time:.1f}s")
        print(f"✅ Total Processing: {test_results['total_time_seconds']:.1f}s")
        print(f"✅ Speakers Found: {len(speakers)}")
        print(f"✅ Segments Generated: {len(result.get('segments', []))}")
        print("✅ Speaker Service Integration: Working")
        print("🎉 REAL AUDIO TESTING SUCCESSFUL!")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_whisperx_with_real_audio())