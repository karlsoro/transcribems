#!/usr/bin/env python3
"""
Test WhisperX with PROPER integrated speaker diarization - the way it's designed to work.
No separate speaker service calls, no manual file loading.
"""

import asyncio
import json
import sys
import time
import subprocess
from pathlib import Path

# Add to path
sys.path.insert(0, '.')

from src.services.whisperx_service import WhisperXService

def get_audio_duration(file_path):
    """Get audio duration using ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', str(file_path)
        ], capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return None

def get_file_info(file_path):
    """Get detailed file information."""
    path = Path(file_path)
    size_mb = path.stat().st_size / (1024 * 1024)
    duration = get_audio_duration(file_path)

    return {
        "file": path.name,
        "size_mb": round(size_mb, 1),
        "duration_min": round(duration / 60, 1) if duration else None,
        "duration_sec": duration,
        "format": path.suffix.lower()
    }

async def test_proper_whisperx_integration(audio_file: str):
    """Test WhisperX with integrated speaker diarization - the correct way."""
    print(f"🎯 TESTING PROPER WHISPERX INTEGRATION")
    print("Using WhisperX integrated speaker diarization - single call")
    print("=" * 70)

    # Get file information
    file_info = get_file_info(audio_file)
    print(f"📁 File: {file_info['file']}")
    print(f"📊 Size: {file_info['size_mb']} MB")
    print(f"⏱️  Duration: {file_info['duration_min']} minutes")
    print(f"🎵 Format: {file_info['format']}")

    start_time = time.time()

    try:
        # Initialize WhisperX service
        print(f"\n📋 Initializing WhisperX service...")
        whisper_service = WhisperXService(
            model_size='small',  # Good balance of speed and accuracy
            device='cpu',
            compute_type='int8'  # CPU-optimized
        )

        # SINGLE CALL with integrated speaker diarization
        print(f"\n🎯 Processing with WhisperX integrated pipeline...")
        print(f"⚙️  Model: small, Device: cpu, Compute: int8")
        print(f"🎭 Speaker diarization: ENABLED (integrated)")

        processing_start = time.time()

        # This is the CORRECT way - single call with integrated speaker diarization
        result = await whisper_service.transcribe_audio(
            audio_file,
            language="auto",
            enable_speaker_diarization=True,  # WhisperX handles this efficiently
            batch_size=16,
            chunk_length=30
        )

        processing_time = time.time() - processing_start
        total_time = time.time() - start_time

        # Extract results
        text = result.get('text', '').strip()
        segments = result.get('segments', [])
        speakers = result.get('speakers', [])
        language = result.get('language', '')
        audio_duration = result.get('audio_duration', file_info.get('duration_sec', 0))

        print(f"✅ Processing completed in {processing_time:.1f}s")
        print(f"📄 Language detected: {language}")
        print(f"📊 Segments generated: {len(segments)}")
        print(f"👤 Speakers identified: {len(speakers)}")
        print(f"📝 Text length: {len(text)} characters")

        # Performance analysis
        realtime_factor = audio_duration / processing_time if processing_time > 0 else 0

        print(f"\n📊 PERFORMANCE ANALYSIS:")
        print(f"   ⏱️  Processing time: {processing_time:.1f}s")
        print(f"   🎵 Audio duration: {audio_duration:.1f}s")
        print(f"   📈 Realtime factor: {realtime_factor:.1f}x")
        print(f"   💾 File size: {file_info['size_mb']} MB")

        if realtime_factor > 1:
            print(f"   ✅ Performance: {realtime_factor:.1f}x faster than real-time")
        else:
            print(f"   ❌ Performance: {realtime_factor:.1f}x - SLOWER than real-time!")

        # Check speaker integration
        segments_with_speakers = sum(1 for seg in segments if seg.get('speaker'))
        print(f"\n🎭 SPEAKER INTEGRATION:")
        print(f"   👥 Total speakers: {len(speakers)}")
        print(f"   🎬 Total segments: {len(segments)}")
        print(f"   🎭 Segments with speakers: {segments_with_speakers}")
        if segments_with_speakers > 0:
            print(f"   ✅ Speaker integration: WORKING")
        else:
            print(f"   ❌ Speaker integration: FAILED")

        # Show sample with speakers
        print(f"\n📋 SAMPLE RESULTS (first 3 segments):")
        for i, segment in enumerate(segments[:3]):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text_sample = (segment.get('text', '')[:60] + '...') if len(segment.get('text', '')) > 60 else segment.get('text', '')
            speaker = segment.get('speaker', 'None')
            print(f"   {i+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {text_sample}")

        # Save results
        print(f"\n💾 Saving results...")
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create result with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        result_data = {
            "file_info": file_info,
            "audio_file_path": str(audio_file),
            "processing_approach": "WhisperX integrated pipeline",
            "result": {
                "text": text,
                "language": language,
                "segments": segments,
                "speakers": speakers,
                "segments_count": len(segments),
                "segments_with_speakers": segments_with_speakers
            },
            "performance": {
                "processing_time": processing_time,
                "total_time": total_time,
                "audio_duration": audio_duration,
                "realtime_factor": realtime_factor,
                "file_size_mb": file_info['size_mb']
            },
            "metadata": {
                "model_size": "small",
                "device": "cpu",
                "compute_type": "int8",
                "approach": "integrated",
                "timestamp": timestamp,
                "success": True
            }
        }

        # Save JSON result
        result_file = output_dir / f"proper_whisperx_result_{timestamp}.json"
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)

        # Save clean transcript
        transcript_file = output_dir / f"proper_whisperx_transcript_{timestamp}.txt"
        with open(transcript_file, 'w') as f:
            f.write(f"PROPER WHISPERX INTEGRATION TEST RESULT\n")
            f.write(f"=" * 60 + "\n\n")
            f.write(f"File: {file_info['file']}\n")
            f.write(f"Size: {file_info['size_mb']} MB\n")
            f.write(f"Duration: {file_info['duration_min']} minutes\n")
            f.write(f"Language: {language}\n")
            f.write(f"Speakers: {len(speakers)}\n")
            f.write(f"Processing Time: {processing_time:.1f}s\n")
            f.write(f"Realtime Factor: {realtime_factor:.1f}x\n")
            f.write(f"Approach: WhisperX Integrated Pipeline\n")
            f.write(f"\nFULL TRANSCRIPTION:\n")
            f.write(f"-" * 40 + "\n")
            f.write(text)
            f.write(f"\n\nSEGMENT BREAKDOWN:\n")
            f.write(f"-" * 40 + "\n")
            for i, segment in enumerate(segments):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                seg_text = segment.get('text', '')
                speaker = segment.get('speaker', 'None')
                f.write(f"{i+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {seg_text}\n")

        print(f"✅ Results saved:")
        print(f"   📄 JSON: {result_file}")
        print(f"   📝 Transcript: {transcript_file}")

        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        if realtime_factor >= 5:
            print(f"✅ EXCELLENT: {realtime_factor:.1f}x faster than real-time")
        elif realtime_factor >= 2:
            print(f"✅ GOOD: {realtime_factor:.1f}x faster than real-time")
        elif realtime_factor >= 1:
            print(f"⚠️  ACCEPTABLE: {realtime_factor:.1f}x faster than real-time")
        else:
            print(f"❌ FAILED: {realtime_factor:.1f}x - slower than real-time!")

        if segments_with_speakers > 0:
            print(f"✅ Speaker integration working correctly")
        else:
            print(f"❌ Speaker integration failed")

        return result_data

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Test failed after {processing_time:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return None

def find_test_audio():
    """Find suitable test audio files."""
    audio_extensions = {'.wav', '.mp3', '.aac', '.flac', '.m4a'}

    # Look in common directories
    search_paths = [
        Path(".cache/recordings"),
        Path("data/audio"),
        Path("test_data/audio"),
        Path("recordings"),
        Path(".")
    ]

    audio_files = []
    for search_path in search_paths:
        if search_path.exists():
            for ext in audio_extensions:
                audio_files.extend(list(search_path.glob(f"**/*{ext}")))

    return audio_files

def main():
    """Main test execution."""
    print("🔍 Looking for audio files...")

    audio_files = find_test_audio()

    if not audio_files:
        print("❌ No audio files found for testing")
        return

    # Filter and sort by size
    audio_files = [f for f in audio_files if f.exists()]
    audio_files.sort(key=lambda x: x.stat().st_size, reverse=True)

    print(f"🔍 Found {len(audio_files)} audio files:")
    for i, audio_file in enumerate(audio_files[:5]):  # Show top 5
        file_info = get_file_info(audio_file)
        print(f"   {i+1}. {file_info['file']} ({file_info['size_mb']} MB, {file_info['duration_min']} min)")

    if audio_files:
        # Use the largest file for testing
        test_file = audio_files[0]
        print(f"\n🎯 Testing with: {test_file}")

        # Run the test
        result = asyncio.run(test_proper_whisperx_integration(str(test_file)))

        if result:
            print(f"\n🎉 PROPER WHISPERX INTEGRATION TEST COMPLETED!")
        else:
            print(f"\n❌ Test failed")

if __name__ == "__main__":
    main()