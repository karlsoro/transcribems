"""Fixed WhisperX + pyannote diarization with proper audio format handling."""

import asyncio
import json
import time
from pathlib import Path
import warnings
import tempfile
import torch
warnings.filterwarnings("ignore")

async def test_whisperx_fixed_format():
    """Test WhisperX with pyannote using compatible audio format."""

    print("🔧 WhisperX + pyannote with Audio Format Fix")
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
        from pyannote.audio import Pipeline
        import soundfile as sf

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"🖥️  Device: {device}")

        # Step 1: Load audio using WhisperX (handles AAC)
        print("\\n🎵 Loading audio with WhisperX...")
        audio = whisperx.load_audio(str(test_file))
        audio_duration = len(audio) / 16000
        print(f"📊 Audio duration: {audio_duration:.1f} seconds")

        # Step 2: WhisperX transcription
        print("\\n📥 Loading WhisperX model...")
        start_time = time.time()
        model = whisperx.load_model("base", device, compute_type=compute_type)
        model_load_time = time.time() - start_time
        print(f"✅ WhisperX model loaded in {model_load_time:.1f}s")

        print("\\n🔤 Transcribing audio...")
        start_time = time.time()
        result = model.transcribe(audio, batch_size=16)
        transcription_time = time.time() - start_time
        print(f"✅ Transcription completed in {transcription_time:.1f}s")
        print(f"📊 Generated {len(result.get('segments', []))} segments")

        # Step 3: Align for better timestamps
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

        # Step 4: Convert audio to WAV for pyannote compatibility
        print("\\n🔄 Converting audio for pyannote compatibility...")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        # Write the audio array as WAV file
        sf.write(temp_wav_path, audio, 16000)
        print(f"✅ Audio converted to WAV: {temp_wav_path}")

        # Step 5: REAL pyannote-audio speaker diarization
        print("\\n👥 Loading pyannote-audio speaker diarization...")
        start_time = time.time()

        try:
            # Load the speaker diarization pipeline
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=None
            )

            if device == "cuda":
                pipeline = pipeline.to(torch.device("cuda"))

            diarize_load_time = time.time() - start_time
            print(f"✅ Pyannote pipeline loaded in {diarize_load_time:.1f}s")

            # Perform speaker diarization on WAV file
            print("\\n🎭 Performing speaker diarization...")
            start_time = time.time()

            diarization = pipeline(temp_wav_path)

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

            # Show speaker timeline sample
            print("\\n⏰ Speaker timeline (first 5 segments):")
            for seg in speaker_timeline[:5]:
                print(f"   [{seg['start']:.1f}s-{seg['end']:.1f}s]: {seg['speaker']}")

            # Step 6: Assign speakers to WhisperX segments
            print("\\n🏷️  Assigning speakers to transcription segments...")
            start_time = time.time()

            def get_speaker_for_time(timestamp):
                """Find speaker for given timestamp."""
                for seg in speaker_timeline:
                    if seg["start"] <= timestamp <= seg["end"]:
                        return seg["speaker"]
                return "UNKNOWN"

            # Assign speakers to each transcription segment
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
            print(f"\\n🗣️  Final transcription with speakers (first 5):")
            for i, segment in enumerate(final_segments[:5]):
                start = segment["start"]
                end = segment["end"]
                speaker = segment["speaker"]
                text = segment["text"]
                print(f"   [{start:.1f}s-{end:.1f}s] {speaker}: {text}")

            # Analyze speaker distribution
            speaker_stats = {}
            for segment in final_segments:
                speaker = segment["speaker"]
                speaker_stats[speaker] = speaker_stats.get(speaker, 0) + 1

            print(f"\\n📊 Speaker distribution:")
            for speaker, count in sorted(speaker_stats.items()):
                percentage = (count / len(final_segments)) * 100
                print(f"   {speaker}: {count} segments ({percentage:.1f}%)")

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
                "speaker_stats": speaker_stats,
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
            with open("whisperx_real_diarization_results.json", "w") as f:
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

            # Cleanup temp file
            Path(temp_wav_path).unlink()

            return True

        except Exception as diarize_error:
            print(f"❌ Diarization failed: {diarize_error}")
            import traceback
            traceback.print_exc()

            # Cleanup temp file
            if 'temp_wav_path' in locals():
                Path(temp_wav_path).unlink()

            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_whisperx_fixed_format())
    print(f"\\n🎯 Test Result: {'SUCCESS' if success else 'FAILED'}")