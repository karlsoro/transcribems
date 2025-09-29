#!/usr/bin/env python3
"""
Test transcription with large, real audio files.
This validates the system works with actual recordings, not just test files.
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
from src.services.speaker_service import SpeakerIdentificationService

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
        "format": path.suffix.lower()
    }

async def test_large_audio_transcription(audio_file: str):
    """Test transcription with a large real audio file."""
    print(f"🎙️ TESTING LARGE REAL AUDIO TRANSCRIPTION")
    print("=" * 70)

    # Get file information
    file_info = get_file_info(audio_file)
    print(f"📁 File: {file_info['file']}")
    print(f"📊 Size: {file_info['size_mb']} MB")
    print(f"⏱️  Duration: {file_info['duration_min']} minutes")
    print(f"🎵 Format: {file_info['format']}")

    # Check if file is too large for initial test
    if file_info['size_mb'] > 100:
        print(f"⚠️  File is very large ({file_info['size_mb']} MB)")
        print("🔄 Proceeding with transcription (may take several minutes)...")

    start_time = time.time()

    try:
        # Initialize services
        print(f"\n📋 Initializing transcription services...")
        whisper_service = WhisperXService(
            model_size='small',  # Use better model for real audio
            device='cpu',
            compute_type='int8'
        )

        speaker_service = SpeakerIdentificationService()

        # Step 1: Transcribe audio
        print(f"\n📝 Step 1: Transcribing real audio file...")
        print(f"⚙️  Model: small, Device: cpu, Format: {file_info['format']}")

        transcription_start = time.time()
        transcription_result = await whisper_service.transcribe_audio(audio_file)
        transcription_time = time.time() - transcription_start

        # Extract key metrics
        text = transcription_result.get('text', '').strip()
        segments = transcription_result.get('segments', [])
        language = transcription_result.get('language', '')
        audio_duration = transcription_result.get('audio_duration', 0)

        print(f"✅ Transcription completed in {transcription_time:.1f}s")
        print(f"📄 Language detected: {language}")
        print(f"📊 Segments generated: {len(segments)}")
        print(f"📝 Text length: {len(text)} characters")
        print(f"🎵 Audio duration: {audio_duration:.1f}s")

        # Show preview of transcription
        if text:
            preview_length = min(200, len(text))
            print(f"📋 Transcription preview:")
            print(f'   "{text[:preview_length]}{"..." if len(text) > preview_length else ""}"')
        else:
            print("⚠️  No transcription text generated")

        # Step 2: Speaker identification
        print(f"\n👥 Step 2: Speaker identification...")
        speaker_start = time.time()
        speaker_result = await speaker_service.identify_speakers(audio_file)
        speaker_time = time.time() - speaker_start

        speaker_count = speaker_result.get('speaker_count', 0)
        speakers = speaker_result.get('speakers', [])
        speaker_segments = speaker_result.get('segments', [])

        print(f"✅ Speaker identification completed in {speaker_time:.1f}s")
        print(f"👤 Speakers identified: {speaker_count}")
        print(f"🎭 Speaker labels: {speakers}")
        print(f"📍 Speaker segments: {len(speaker_segments)}")

        # Step 3: Performance analysis
        total_time = time.time() - start_time
        realtime_factor = audio_duration / transcription_time if transcription_time > 0 else 0

        print(f"\n📊 PERFORMANCE ANALYSIS:")
        print(f"   ⏱️  Total processing time: {total_time:.1f}s")
        print(f"   🎵 Audio duration: {audio_duration:.1f}s")
        print(f"   📈 Realtime factor: {realtime_factor:.2f}x")
        print(f"   💾 File size processed: {file_info['size_mb']} MB")
        print(f"   📝 Words per minute: {len(text.split()) / (audio_duration / 60):.0f}" if audio_duration > 0 else "")

        # Step 4: Save comprehensive results
        print(f"\n💾 Saving results...")

        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create comprehensive result
        comprehensive_result = {
            "file_info": file_info,
            "audio_file_path": str(audio_file),
            "transcription": {
                "text": text,
                "language": language,
                "segments_count": len(segments),
                "segments": segments[:10],  # Save first 10 segments for review
                "processing_time": transcription_time
            },
            "speakers": {
                "count": speaker_count,
                "speakers": speakers,
                "segments_count": len(speaker_segments),
                "segments": speaker_segments[:10]  # Save first 10 speaker segments
            },
            "performance": {
                "total_processing_time": total_time,
                "audio_duration": audio_duration,
                "realtime_factor": realtime_factor,
                "file_size_mb": file_info['size_mb'],
                "words_per_minute": len(text.split()) / (audio_duration / 60) if audio_duration > 0 else 0
            },
            "metadata": {
                "model_size": "small",
                "device": "cpu",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": True
            }
        }

        # Save JSON result
        result_file = output_dir / f"large_audio_result_{file_info['file'].replace('.', '_')}.json"
        with open(result_file, 'w') as f:
            json.dump(comprehensive_result, f, indent=2, default=str)

        # Save text transcript
        transcript_file = output_dir / f"large_audio_transcript_{file_info['file'].replace('.', '_')}.txt"
        with open(transcript_file, 'w') as f:
            f.write(f"LARGE AUDIO TRANSCRIPTION RESULT\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"File: {file_info['file']}\n")
            f.write(f"Size: {file_info['size_mb']} MB\n")
            f.write(f"Duration: {file_info['duration_min']} minutes\n")
            f.write(f"Language: {language}\n")
            f.write(f"Speakers: {speaker_count}\n")
            f.write(f"Processing Time: {total_time:.1f}s\n")
            f.write(f"Realtime Factor: {realtime_factor:.2f}x\n\n")
            f.write(f"FULL TRANSCRIPTION:\n")
            f.write(f"-" * 20 + "\n")
            f.write(text)
            f.write(f"\n\nSEGMENT BREAKDOWN:\n")
            f.write(f"-" * 20 + "\n")
            for i, seg in enumerate(segments[:20]):  # Show first 20 segments
                start = seg.get('start', 0)
                end = seg.get('end', 0)
                seg_text = seg.get('text', '').strip()
                f.write(f"{i+1}. [{start:.1f}s-{end:.1f}s]: \"{seg_text}\"\n")

        print(f"✅ Results saved:")
        print(f"   📄 JSON: {result_file}")
        print(f"   📝 Transcript: {transcript_file}")

        # Step 5: Success summary
        print(f"\n🎉 LARGE AUDIO TRANSCRIPTION SUCCESSFUL!")
        print(f"✅ Successfully processed {file_info['size_mb']} MB audio file")
        print(f"✅ Generated {len(text)} character transcription")
        print(f"✅ Identified {speaker_count} speakers")
        print(f"✅ Processed at {realtime_factor:.2f}x realtime speed")

        return comprehensive_result

    except Exception as e:
        error_time = time.time() - start_time
        print(f"\n❌ LARGE AUDIO TRANSCRIPTION FAILED after {error_time:.1f}s")
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

        # Save error information
        error_result = {
            "file_info": file_info,
            "error": str(e),
            "processing_time": error_time,
            "success": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        error_file = output_dir / f"large_audio_error_{file_info['file'].replace('.', '_')}.json"
        with open(error_file, 'w') as f:
            json.dump(error_result, f, indent=2, default=str)

        return None

async def main():
    """Main test function."""
    # Find real audio files
    recordings_dir = Path(".cache/recordings")

    if not recordings_dir.exists():
        print("❌ No recordings directory found")
        return False

    # Find .aac files
    audio_files = list(recordings_dir.rglob("*.aac"))

    if not audio_files:
        print("❌ No .aac files found in recordings")
        return False

    print(f"🔍 Found {len(audio_files)} real audio files:")
    for audio_file in audio_files:
        info = get_file_info(audio_file)
        print(f"   📁 {info['file']} ({info['size_mb']} MB, {info['duration_min']} min)")

    # Test with the first audio file
    test_file = audio_files[0]
    print(f"\n🎯 Testing with: {test_file}")

    result = await test_large_audio_transcription(str(test_file))

    return result is not None

if __name__ == "__main__":
    success = asyncio.run(main())

    if success:
        print(f"\n🎉 LARGE REAL AUDIO TEST SUCCESSFUL!")
        print("✅ System validated with real, large audio content")
    else:
        print(f"\n💥 LARGE REAL AUDIO TEST FAILED")

    sys.exit(0 if success else 1)