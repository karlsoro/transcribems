"""Correct WhisperX + pyannote-audio speaker diarization implementation."""

import asyncio
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

async def test_correct_whisperx_diarization():
    """Test WhisperX with proper pyannote-audio speaker diarization."""

    print("🎯 CORRECT WhisperX + pyannote-audio Diarization")
    print("=" * 60)

    # Find audio files
    recordings_dir = Path("recordings")
    audio_files = list(recordings_dir.rglob("*.aac"))

    if not audio_files:
        print("❌ No audio files found")
        return False

    # Use smaller file for test
    audio_files.sort(key=lambda x: x.stat().st_size)
    test_file = audio_files[0]

    file_size_mb = test_file.stat().st_size / (1024 * 1024)
    print(f"📁 Testing: {test_file.name} ({file_size_mb:.1f} MB)")

    try:
        import whisperx
        import torch
        from pyannote.audio import Pipeline

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"🖥️  Device: {device}")

        # Step 1: WhisperX transcription
        print("\\n📥 Loading WhisperX model...")
        start_time = time.time()
        model = whisperx.load_model("base", device, compute_type=compute_type)
        model_load_time = time.time() - start_time
        print(f"✅ WhisperX model loaded in {model_load_time:.1f}s")

        print("\\n🎵 Loading and transcribing audio...")
        audio = whisperx.load_audio(str(test_file))
        audio_duration = len(audio) / 16000
        print(f"📊 Audio duration: {audio_duration:.1f} seconds")

        start_time = time.time()
        result = model.transcribe(audio, batch_size=16)
        transcription_time = time.time() - start_time
        print(f"✅ Transcription completed in {transcription_time:.1f}s")
        print(f"📊 Generated {len(result.get('segments', []))} segments")

        # Step 2: Align for better timestamps
        print("\\n⏱️  Loading alignment model...")
        start_time = time.time()
        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"],
            device=device
        )
        align_load_time = time.time() - start_time
        print(f"✅ Alignment model loaded in {align_load_time:.1f}s")

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

        # Step 3: REAL pyannote-audio speaker diarization
        print("\\n👥 Loading pyannote-audio speaker diarization...")
        start_time = time.time()

        try:
            # Try to load the speaker diarization pipeline
            # This uses a public model - no token required
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=None
            )

            if device == "cuda":
                pipeline = pipeline.to(torch.device("cuda"))

            diarize_load_time = time.time() - start_time
            print(f"✅ Pyannote pipeline loaded in {diarize_load_time:.1f}s")

            # Perform speaker diarization
            print("\\n🎭 Performing speaker diarization...")
            start_time = time.time()

            # Convert audio file to format pyannote expects
            diarization = pipeline(str(test_file))

            diarize_time = time.time() - start_time
            print(f"✅ Diarization completed in {diarize_time:.1f}s")

            # Extract speaker information
            speakers = set()
            speaker_timeline = []

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speakers.add(speaker)
                speaker_timeline.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            print(f"👥 Speakers found by pyannote: {len(speakers)} ({', '.join(sorted(speakers))})")
            print(f"📊 Speaker segments: {len(speaker_timeline)}")

            # Step 4: Assign speakers to WhisperX segments
            print("\\n🏷️  Assigning speakers to transcription segments...")
            start_time = time.time()

            # Create speaker mapping function
            def get_speaker_for_time(timestamp):
                for seg in speaker_timeline:
                    if seg["start"] <= timestamp <= seg["end"]:
                        return seg["speaker"]
                return "UNKNOWN"

            # Assign speakers to each segment
            final_segments = []
            for segment in result.get("segments", []):
                start_time_seg = segment.get("start", 0)
                end_time_seg = segment.get("end", 0)

                # Use the midpoint to determine speaker
                midpoint = (start_time_seg + end_time_seg) / 2
                speaker = get_speaker_for_time(midpoint)

                final_segments.append({
                    "start": start_time_seg,
                    "end": end_time_seg,
                    "text": segment.get("text", "").strip(),
                    "speaker": speaker
                })

            assignment_time = time.time() - start_time
            print(f"✅ Speaker assignment completed in {assignment_time:.1f}s")

            # Show results
            print(f"\\n🗣️  Final speaker segments (first 5):")
            for i, segment in enumerate(final_segments[:5]):
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
                "final_segments_count": len(final_segments),
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
                "sample_segments": final_segments[:10],
                "status": "SUCCESS - REAL WHISPERX + PYANNOTE DIARIZATION"
            }

            # Save results
            with open("correct_whisperx_diarization_results.json", "w") as f:
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
            print(f"📊 Final Segments: {len(final_segments)}")
            print("✅ REAL WHISPERX + PYANNOTE DIARIZATION SUCCESS!")

            return True

        except Exception as diarize_error:
            print(f"❌ Diarization failed: {diarize_error}")
            print("💡 This might require downloading the pyannote model")
            print("💡 Or a HuggingFace token for some models")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_correct_whisperx_diarization())
    print(f"\\n🎯 Test Result: {'SUCCESS' if success else 'FAILED'}")