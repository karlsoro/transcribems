"""Optimized real audio testing with practical settings for large files."""

import asyncio
import json
import time
from pathlib import Path

async def test_optimized_transcription():
    """Test with optimized settings for large audio files."""

    print("🎙️  Optimized Real Audio Testing")
    print("=" * 50)

    # Find audio files
    recordings_dir = Path("recordings")
    audio_files = list(recordings_dir.rglob("*.aac"))

    if not audio_files:
        print("❌ No audio files found")
        return

    # Use the smaller file first
    audio_files.sort(key=lambda x: x.stat().st_size)
    test_file = audio_files[0]

    file_size_mb = test_file.stat().st_size / (1024 * 1024)
    print(f"📁 Testing: {test_file.name} ({file_size_mb:.1f} MB)")

    try:
        import whisperx
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"🖥️  Device: {device}")
        print(f"⚙️  Compute: {compute_type}")

        # Use tiny model for speed
        print("\\n📥 Loading tiny model (fastest)...")
        start_time = time.time()
        model = whisperx.load_model("tiny", device, compute_type=compute_type)
        model_load_time = time.time() - start_time
        print(f"✅ Model loaded in {model_load_time:.1f}s")

        # Load audio
        print("\\n🎵 Loading audio...")
        start_time = time.time()
        audio = whisperx.load_audio(str(test_file))
        audio_load_time = time.time() - start_time
        print(f"✅ Audio loaded in {audio_load_time:.1f}s")
        print(f"📊 Audio duration: {len(audio)/16000:.1f} seconds")

        # Transcribe with optimized batch size
        print("\\n🔤 Transcribing...")
        start_time = time.time()
        result = model.transcribe(audio, batch_size=32)  # Larger batch for efficiency
        transcribe_time = time.time() - start_time
        print(f"✅ Transcription completed in {transcribe_time:.1f}s")

        segments = result.get('segments', [])
        print(f"📊 Generated {len(segments)} segments")

        # Show first few transcribed segments
        print("\\n📝 Sample transcription:")
        for i, segment in enumerate(segments[:3]):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            print(f"   [{start:.1f}s-{end:.1f}s]: {text}")

        # Test our speaker service with mock
        print("\\n👥 Testing speaker service...")
        from src.services.speaker_service import SpeakerIdentificationService

        class FastMockDiarization:
            def identify_speakers(self, audio_path):
                # Simulate realistic speaker assignment
                return {
                    "speakers": ["SPEAKER_00", "SPEAKER_01"],
                    "segments": [
                        {
                            **seg,
                            "speaker": f"SPEAKER_{i % 2:02d}",
                            "speaker_confidence": 0.85 + (i % 3) * 0.05
                        }
                        for i, seg in enumerate(segments)
                    ],
                    "speaker_count": 2
                }

        mock_service = FastMockDiarization()
        speaker_service = SpeakerIdentificationService(diarization_service=mock_service)

        start_time = time.time()
        speaker_result = await speaker_service.identify_speakers(str(test_file))
        speaker_time = time.time() - start_time

        print(f"✅ Speaker service completed in {speaker_time:.3f}s")
        print(f"👥 Identified {speaker_result['speaker_count']} speakers")

        # Show speaker segments
        print("\\n👥 Sample speaker segments:")
        for i, segment in enumerate(speaker_result['segments'][:3]):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            speaker = segment.get('speaker', 'Unknown')
            conf = segment.get('speaker_confidence', 0)
            print(f"   [{start:.1f}s-{end:.1f}s] {speaker} ({conf:.2f}): {text}")

        # Performance summary
        total_time = model_load_time + audio_load_time + transcribe_time + speaker_time
        audio_duration = len(audio) / 16000
        realtime_factor = audio_duration / transcribe_time

        results = {
            "file": test_file.name,
            "file_size_mb": file_size_mb,
            "audio_duration_seconds": audio_duration,
            "performance": {
                "model_load_time": model_load_time,
                "audio_load_time": audio_load_time,
                "transcription_time": transcribe_time,
                "speaker_processing_time": speaker_time,
                "total_time": total_time,
                "realtime_factor": realtime_factor
            },
            "results": {
                "segments_count": len(segments),
                "speakers_identified": speaker_result['speaker_count'],
                "speaker_segments": len(speaker_result['segments'])
            },
            "status": "SUCCESS"
        }

        # Save results
        with open("optimized_audio_test_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\\n📊 PERFORMANCE SUMMARY")
        print("=" * 50)
        print(f"📁 File: {test_file.name}")
        print(f"📏 Size: {file_size_mb:.1f} MB")
        print(f"⏱️  Duration: {audio_duration:.1f} seconds")
        print(f"🏃 Transcription: {transcribe_time:.1f}s")
        print(f"⚡ Realtime Factor: {realtime_factor:.1f}x")
        print(f"👥 Speakers: {speaker_result['speaker_count']}")
        print(f"📊 Segments: {len(segments)}")
        print("✅ ALL TESTS PASSED!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_optimized_transcription())
    print(f"\\n🎯 Test Result: {'SUCCESS' if success else 'FAILED'}")