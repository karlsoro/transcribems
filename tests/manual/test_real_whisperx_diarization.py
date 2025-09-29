"""Real WhisperX speaker diarization test using pyannote-audio.

This implements the ACTUAL WhisperX multi-speaker pipeline, not a mock.
"""

import asyncio
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

async def test_real_whisperx_diarization():
    """Test actual WhisperX speaker diarization with pyannote-audio."""

    print("👥 REAL WhisperX Speaker Diarization Test")
    print("=" * 60)

    # Find audio files
    recordings_dir = Path("recordings")
    audio_files = list(recordings_dir.rglob("*.aac"))

    if not audio_files:
        print("❌ No audio files found")
        return False

    # Use smaller file for initial test
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

        # Step 1: Load WhisperX model
        print("\\n📥 Loading WhisperX model...")
        start_time = time.time()
        model = whisperx.load_model("base", device, compute_type=compute_type)
        model_load_time = time.time() - start_time
        print(f"✅ Model loaded in {model_load_time:.1f}s")

        # Step 2: Load and transcribe audio
        print("\\n🎵 Loading audio...")
        audio = whisperx.load_audio(str(test_file))
        audio_duration = len(audio) / 16000
        print(f"📊 Audio duration: {audio_duration:.1f} seconds")

        print("\\n🔤 Transcribing audio...")
        start_time = time.time()
        result = model.transcribe(audio, batch_size=16)
        transcription_time = time.time() - start_time
        print(f"✅ Transcription completed in {transcription_time:.1f}s")
        print(f"📊 Generated {len(result.get('segments', []))} segments")

        # Step 3: Load alignment model for better timestamps
        print("\\n⏱️  Loading alignment model...")
        start_time = time.time()
        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"],
            device=device
        )
        align_load_time = time.time() - start_time
        print(f"✅ Alignment model loaded in {align_load_time:.1f}s")

        # Step 4: Align whisper output
        print("\\n🎯 Aligning transcription...")
        start_time = time.time()
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            device,
            return_char_alignments=False
        )
        align_time = time.time() - start_time
        print(f"✅ Alignment completed in {align_time:.1f}s")

        # Step 5: REAL SPEAKER DIARIZATION using pyannote-audio
        print("\\n👥 Loading diarization pipeline (pyannote-audio)...")
        start_time = time.time()

        # This is the REAL diarization - requires HuggingFace token for some models
        try:
            diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=None,  # Can add HF token here if needed
                device=device
            )
            diarize_load_time = time.time() - start_time
            print(f"✅ Diarization pipeline loaded in {diarize_load_time:.1f}s")

            # Perform actual speaker diarization
            print("\\n🎭 Performing speaker diarization...")
            start_time = time.time()
            diarize_segments = diarize_model(audio)
            diarize_time = time.time() - start_time
            print(f"✅ Diarization completed in {diarize_time:.1f}s")

            # Assign speaker labels to words
            print("\\n🏷️  Assigning speaker labels...")
            start_time = time.time()
            result = whisperx.assign_word_speakers(diarize_segments, result)
            assignment_time = time.time() - start_time
            print(f"✅ Speaker assignment completed in {assignment_time:.1f}s")

            # Analyze results
            speakers = set()
            speaker_segments = []

            for segment in result.get("segments", []):
                if "speaker" in segment:
                    speakers.add(segment["speaker"])
                    speaker_segments.append({
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                        "speaker": segment.get("speaker", "Unknown"),
                        "text": segment.get("text", "").strip()
                    })

            print(f"\\n👥 DIARIZATION RESULTS:")
            print(f"🎯 Speakers detected: {len(speakers)} ({', '.join(sorted(speakers))})")
            print(f"📊 Speaker segments: {len(speaker_segments)}")

            # Show sample segments with speakers
            print("\\n🗣️  Sample speaker segments:")
            for i, segment in enumerate(speaker_segments[:5]):
                start = segment["start"]
                end = segment["end"]
                speaker = segment["speaker"]
                text = segment["text"]
                print(f"   [{start:.1f}s-{end:.1f}s] {speaker}: {text}")

            # Performance summary
            total_time = (model_load_time + transcription_time + align_load_time +
                         align_time + diarize_load_time + diarize_time + assignment_time)

            realtime_factor = audio_duration / (transcription_time + diarize_time)

            results = {
                "file": test_file.name,
                "file_size_mb": file_size_mb,
                "audio_duration_seconds": audio_duration,
                "speakers_detected": len(speakers),
                "speakers_list": list(sorted(speakers)),
                "speaker_segments_count": len(speaker_segments),
                "performance": {
                    "model_load_time": model_load_time,
                    "transcription_time": transcription_time,
                    "align_load_time": align_load_time,
                    "align_time": align_time,
                    "diarize_load_time": diarize_load_time,
                    "diarize_time": diarize_time,
                    "assignment_time": assignment_time,
                    "total_time": total_time,
                    "realtime_factor": realtime_factor
                },
                "sample_segments": speaker_segments[:10],
                "status": "SUCCESS - REAL DIARIZATION"
            }

            # Save results
            with open("real_whisperx_diarization_results.json", "w") as f:
                json.dump(results, f, indent=2)

            print("\\n📊 PERFORMANCE SUMMARY")
            print("=" * 60)
            print(f"📁 File: {test_file.name}")
            print(f"📏 Size: {file_size_mb:.1f} MB")
            print(f"⏱️  Duration: {audio_duration:.1f} seconds")
            print(f"🔤 Transcription: {transcription_time:.1f}s")
            print(f"👥 Diarization: {diarize_time:.1f}s")
            print(f"⚡ Realtime Factor: {realtime_factor:.1f}x")
            print(f"🎯 Speakers Found: {len(speakers)}")
            print(f"📊 Speaker Segments: {len(speaker_segments)}")
            print("✅ REAL WHISPERX DIARIZATION SUCCESS!")

            return True

        except Exception as diarize_error:
            print(f"❌ Diarization failed: {diarize_error}")
            print("💡 This might require a HuggingFace token for some pyannote models")
            print("💡 Or the model might not be available for this configuration")

            # Show what we got from transcription only
            print("\\n📝 Transcription-only results:")
            segments = result.get("segments", [])
            for i, segment in enumerate(segments[:3]):
                start = segment.get("start", 0)
                end = segment.get("end", 0)
                text = segment.get("text", "").strip()
                print(f"   [{start:.1f}s-{end:.1f}s]: {text}")

            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_whisperx_diarization())
    print(f"\\n🎯 Test Result: {'SUCCESS' if success else 'FAILED'}")