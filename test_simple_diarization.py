"""Simple test to verify pyannote diarization is working."""

import tempfile
import time
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

def test_simple_diarization():
    """Test just the pyannote diarization part."""

    print("🧪 Simple Pyannote Diarization Test")
    print("=" * 50)

    # Find audio files
    recordings_dir = Path("recordings")
    audio_files = list(recordings_dir.rglob("*.aac"))

    if not audio_files:
        print("❌ No audio files found")
        return False

    test_file = audio_files[0]
    file_size_mb = test_file.stat().st_size / (1024 * 1024)
    print(f"📁 Testing: {test_file.name} ({file_size_mb:.1f} MB)")

    try:
        import whisperx
        from pyannote.audio import Pipeline
        import soundfile as sf
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Device: {device}")

        # Step 1: Load audio using WhisperX (handles AAC)
        print("\\n🎵 Loading audio with WhisperX...")
        start_time = time.time()
        audio = whisperx.load_audio(str(test_file))
        audio_load_time = time.time() - start_time
        audio_duration = len(audio) / 16000
        print(f"✅ Audio loaded in {audio_load_time:.1f}s")
        print(f"📊 Duration: {audio_duration:.1f} seconds")

        # Step 2: Convert to WAV for pyannote
        print("\\n🔄 Converting to WAV for pyannote...")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        sf.write(temp_wav_path, audio, 16000)
        print(f"✅ WAV created: {Path(temp_wav_path).name}")

        # Step 3: Test pyannote diarization
        print("\\n👥 Loading pyannote pipeline...")
        start_time = time.time()
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=None
        )
        pipeline_load_time = time.time() - start_time
        print(f"✅ Pipeline loaded in {pipeline_load_time:.1f}s")

        print("\\n🎭 Performing diarization...")
        start_time = time.time()
        diarization = pipeline(temp_wav_path)
        diarize_time = time.time() - start_time
        print(f"✅ Diarization completed in {diarize_time:.1f}s")

        # Extract results
        speakers = set()
        segments = []

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.add(speaker)
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })

        print(f"\\n📊 RESULTS:")
        print(f"👥 Speakers detected: {len(speakers)}")
        print(f"📊 Speaker segments: {len(segments)}")
        print(f"🏷️  Speaker labels: {', '.join(sorted(speakers))}")

        # Show first few segments
        print("\\n🗣️  First 5 speaker segments:")
        for i, seg in enumerate(segments[:5]):
            duration = seg["end"] - seg["start"]
            print(f"   [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['speaker']} ({duration:.1f}s)")

        # Performance
        realtime_factor = audio_duration / diarize_time
        print(f"\\n⚡ Performance:")
        print(f"   Audio Duration: {audio_duration:.1f}s")
        print(f"   Processing Time: {diarize_time:.1f}s")
        print(f"   Realtime Factor: {realtime_factor:.1f}x")

        # Cleanup
        Path(temp_wav_path).unlink()

        if len(speakers) > 1:
            print("\\n✅ MULTI-SPEAKER DETECTION SUCCESS!")
            return True
        else:
            print("\\n⚠️  Only one speaker detected - might be a single speaker file")
            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_diarization()
    print(f"\\n🎯 Result: {'SUCCESS' if success else 'FAILED'}")