#!/usr/bin/env python3
"""
Working transcription test script.
This script demonstrates the complete working transcription pipeline.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append('src')

from services.whisperx_service import WhisperXService
from services.speaker_service import SpeakerIdentificationService

async def test_complete_pipeline():
    """Test the complete working transcription + speaker identification pipeline."""
    print("🚀 TESTING COMPLETE WORKING TRANSCRIPTION PIPELINE")
    print("=" * 70)

    # Initialize services
    print("📋 Initializing services...")
    whisper_service = WhisperXService(model_size='tiny', device='cpu', compute_type='int8')
    speaker_service = SpeakerIdentificationService()

    # Test audio file
    audio_file = "test_data/audio/multi_speaker.wav"
    print(f"🎵 Processing: {audio_file}")

    start_time = time.time()

    try:
        # Step 1: Transcribe audio
        print("\n📝 Step 1: Transcribing audio...")
        transcription_result = await whisper_service.transcribe_audio(audio_file)

        print(f"✅ Transcription completed:")
        print(f"   📄 Text: \"{transcription_result.get('text', '')}\"")
        print(f"   📊 Segments: {len(transcription_result.get('segments', []))}")
        print(f"   🕐 Duration: {transcription_result.get('audio_duration', 0):.1f}s")

        # Step 2: Identify speakers
        print("\n👥 Step 2: Identifying speakers...")
        speaker_result = await speaker_service.identify_speakers(audio_file)

        print(f"✅ Speaker identification completed:")
        print(f"   👤 Speakers found: {speaker_result.get('speaker_count', 0)}")
        print(f"   🎭 Speaker list: {speaker_result.get('speakers', [])}")
        print(f"   📍 Speaker segments: {len(speaker_result.get('segments', []))}")

        # Step 3: Combine results
        print("\n🔄 Step 3: Combining transcription and speaker data...")

        combined_result = {
            "audio_file": audio_file,
            "transcription": {
                "text": transcription_result.get("text", ""),
                "language": transcription_result.get("language", ""),
                "segments": transcription_result.get("segments", [])
            },
            "speakers": {
                "count": speaker_result.get("speaker_count", 0),
                "speakers": speaker_result.get("speakers", []),
                "segments": speaker_result.get("segments", [])
            },
            "metadata": {
                "processing_time": time.time() - start_time,
                "audio_duration": transcription_result.get("audio_duration", 0),
                "model_used": transcription_result.get("model_name", ""),
                "device": transcription_result.get("device", ""),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }

        # Step 4: Save results
        print("\n💾 Step 4: Saving results...")

        # Ensure output directory exists
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save complete result
        result_file = output_dir / "complete_transcription_result.json"
        with open(result_file, 'w') as f:
            json.dump(combined_result, f, indent=2, default=str)

        # Save text file
        text_file = output_dir / "transcription_output.txt"
        with open(text_file, 'w') as f:
            f.write(f"Audio File: {audio_file}\n")
            f.write(f"Transcription: {combined_result['transcription']['text']}\n")
            f.write(f"Language: {combined_result['transcription']['language']}\n")
            f.write(f"Speakers: {combined_result['speakers']['count']}\n")
            f.write(f"Processing Time: {combined_result['metadata']['processing_time']:.2f}s\n\n")

            f.write("DETAILED SEGMENTS:\n")
            f.write("-" * 40 + "\n")
            for i, seg in enumerate(combined_result['transcription']['segments']):
                start = seg.get('start', 0)
                end = seg.get('end', 0)
                text = seg.get('text', '').strip()
                f.write(f"{i+1}. [{start:.2f}s-{end:.2f}s]: \"{text}\"\n")

        print(f"✅ Results saved:")
        print(f"   📄 JSON: {result_file}")
        print(f"   📝 Text: {text_file}")

        # Step 5: Summary
        total_time = time.time() - start_time
        print(f"\n🎯 PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"📊 Summary:")
        print(f"   ✅ Transcription: Working")
        print(f"   ✅ Speaker ID: Working")
        print(f"   ✅ File Output: Working")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        print(f"   📄 Transcribed Text: \"{combined_result['transcription']['text']}\"")

        return combined_result

    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function."""
    result = await test_complete_pipeline()

    if result:
        print(f"\n🎉 SUCCESS: Complete transcription pipeline is WORKING!")
        return True
    else:
        print(f"\n💥 FAILURE: Pipeline is broken")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)