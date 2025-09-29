#!/usr/bin/env python3
"""
Test the fixed WhisperX service with proper speaker assignment.
"""

import asyncio
import json
from pathlib import Path
from src.services.whisperx_service import WhisperXService

async def test_fixed_whisperx():
    """Test fixed WhisperX service with proper speaker merging."""
    print("🔧 TESTING FIXED WHISPERX SERVICE")
    print("=" * 60)

    # Use small test file first
    audio_file = "test_data/audio/multi_speaker.wav"

    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    print(f"🎵 Processing: {audio_file}")

    try:
        # Test with fixed WhisperX service
        service = WhisperXService(model_size='tiny', device='cpu', compute_type='int8')

        result = await service.transcribe_audio(
            audio_file,
            enable_speaker_diarization=True
        )

        print(f"✅ Processing completed")
        print(f"📄 Text: {result.get('text', '')}")
        print(f"🎬 Segments: {len(result.get('segments', []))}")

        # Check for speaker information in segments
        segments_with_speakers = 0
        speakers_found = set()

        for i, segment in enumerate(result.get('segments', [])[:5]):  # Check first 5
            speaker = segment.get('speaker')
            if speaker:
                segments_with_speakers += 1
                speakers_found.add(speaker)

            print(f"   {i+1}. [{segment.get('start', 0):.1f}s-{segment.get('end', 0):.1f}s] "
                  f"Speaker: {speaker or 'None'} | Text: {segment.get('text', '')[:30]}...")

        print(f"\n📊 Results:")
        print(f"👥 Speakers found: {list(speakers_found) if speakers_found else 'None'}")
        print(f"🎤 Segments with speakers: {segments_with_speakers}/{len(result.get('segments', []))}")

        if segments_with_speakers > 0:
            print("✅ SUCCESS: WhisperX speaker assignment is working!")
        else:
            print("❌ FAILED: No speaker assignments found")

        # Save result
        output_file = "data/results/fixed_whisperx_test.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"💾 Result saved to: {output_file}")

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_fixed_whisperx())