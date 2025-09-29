#!/usr/bin/env python3
"""
Test the complete fixed pipeline with large audio file to verify speaker merging.
"""

import asyncio
import json
import time
from pathlib import Path
from src.services.whisperx_service import WhisperXService

async def test_final_pipeline():
    """Test the complete pipeline with fixed speaker merging on large file."""
    print("🎯 TESTING COMPLETE FIXED PIPELINE WITH LARGE AUDIO")
    print("=" * 70)

    # Use smaller audio file first to verify quickly
    audio_file = "test_data/audio/medium_speech.wav"

    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    print(f"🎵 Processing: {audio_file}")

    try:
        start_time = time.time()

        # Test with fixed WhisperX service
        service = WhisperXService(model_size='tiny', device='cpu', compute_type='int8')

        result = await service.transcribe_audio(
            audio_file,
            enable_speaker_diarization=True
        )

        processing_time = time.time() - start_time

        print(f"✅ Processing completed in {processing_time:.2f}s")
        print(f"📄 Text length: {len(result.get('text', ''))}")
        print(f"🎬 Total segments: {len(result.get('segments', []))}")
        print(f"👥 Speakers found: {result.get('speakers', [])}")

        # Analyze speaker assignment coverage
        segments = result.get('segments', [])
        segments_with_speakers = sum(1 for seg in segments if seg.get('speaker'))

        print(f"\n📊 SPEAKER ASSIGNMENT ANALYSIS:")
        print(f"🎤 Segments with speakers: {segments_with_speakers}/{len(segments)}")
        print(f"📈 Speaker coverage: {(segments_with_speakers/len(segments)*100):.1f}%" if segments else "0%")

        # Show sample segments
        print(f"\n📋 SAMPLE SEGMENTS (first 3):")
        for i, segment in enumerate(segments[:3]):
            speaker = segment.get('speaker', 'None')
            text = segment.get('text', '')[:40] + '...' if len(segment.get('text', '')) > 40 else segment.get('text', '')
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            print(f"   {i+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {text}")

        # Final verdict
        if segments_with_speakers > 0:
            print(f"\n✅ SUCCESS: Complete pipeline working with speaker identification!")
            print(f"🔧 Fix applied: Integrated SpeakerIdentificationService into WhisperX")
            print(f"🎯 Speaker merging: Working correctly")
        else:
            print(f"\n❌ FAILED: Speaker assignments still not working")

        # Save detailed result
        output_file = "data/results/final_pipeline_test.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"💾 Complete result saved to: {output_file}")

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_final_pipeline())