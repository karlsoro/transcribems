#!/usr/bin/env python3
"""
Test WhisperX and Speaker services directly to verify complete pipeline.
"""

import asyncio
import json
import time
from pathlib import Path

# Import services directly
from src.services.whisperx_service import WhisperXService
from src.services.speaker_service import SpeakerIdentificationService

async def test_services_directly():
    """Test services directly to validate complete pipeline."""
    print("🎯 TESTING SERVICES DIRECTLY: WhisperX + Speaker Identification")
    print("=" * 80)

    # Use the large converted audio file
    audio_file = "large_audio_converted.wav"

    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    print(f"🎵 Processing: {audio_file}")

    try:
        # Test 1: WhisperX transcription
        print("\n📝 Step 1: WhisperX Transcription")
        whisper_service = WhisperXService(model_size='tiny', device='cpu', compute_type='int8')

        start_time = time.time()
        transcription_result = await whisper_service.transcribe_audio(audio_file)
        transcription_time = time.time() - start_time

        print(f"✅ Transcription completed in {transcription_time:.2f}s")
        print(f"📄 Text length: {len(transcription_result.get('text', ''))}")
        print(f"🎬 Segments: {len(transcription_result.get('segments', []))}")

        # Test 2: Speaker identification
        print("\n🎤 Step 2: Speaker Identification")
        speaker_service = SpeakerIdentificationService()

        start_time = time.time()
        speaker_result = await speaker_service.identify_speakers(audio_file)
        speaker_time = time.time() - start_time

        print(f"✅ Speaker ID completed in {speaker_time:.2f}s")
        print(f"👥 Speakers found: {len(speaker_result.get('speakers', []))}")
        print(f"🎬 Speaker segments: {len(speaker_result.get('segments', []))}")

        # Test 3: Check for speaker information
        print("\n🔍 Step 3: Speaker Information Analysis")
        speakers_list = speaker_result.get('speakers', [])
        speaker_segments = speaker_result.get('segments', [])

        if speakers_list:
            print(f"✅ Speakers identified: {speakers_list}")
        else:
            print("⚠️  No speakers identified")

        if speaker_segments:
            # Show first few segments with speaker info
            print("📋 First few speaker segments:")
            for i, segment in enumerate(speaker_segments[:3]):
                speaker = segment.get('speaker', 'Unknown')
                text = segment.get('text', '')[:50] + '...' if len(segment.get('text', '')) > 50 else segment.get('text', '')
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                print(f"   {i+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {text}")

        # Test 4: Merge transcription + speakers (manual merge to test)
        print("\n🔗 Step 4: Manual Merge Test")

        # Simple merge logic test
        transcription_segments = transcription_result.get('segments', [])
        merged_segments = []

        for trans_seg in transcription_segments:
            # Find matching speaker segment by time overlap
            trans_start = trans_seg.get('start', 0)
            trans_end = trans_seg.get('end', 0)

            matched_speaker = None
            for spk_seg in speaker_segments:
                spk_start = spk_seg.get('start', 0)
                spk_end = spk_seg.get('end', 0)

                # Check for time overlap
                if (trans_start >= spk_start and trans_start <= spk_end) or \
                   (trans_end >= spk_start and trans_end <= spk_end):
                    matched_speaker = spk_seg.get('speaker')
                    break

            # Create merged segment
            merged_segment = trans_seg.copy()
            merged_segment['speaker'] = matched_speaker
            merged_segments.append(merged_segment)

        # Show merged results
        print(f"🔗 Merged segments created: {len(merged_segments)}")
        segments_with_speakers = sum(1 for seg in merged_segments if seg.get('speaker'))
        print(f"🎤 Segments with speakers: {segments_with_speakers}/{len(merged_segments)}")

        if segments_with_speakers > 0:
            print("✅ SUCCESS: Speaker identification is working!")
            print("📋 Sample merged segments:")
            for i, segment in enumerate(merged_segments[:3]):
                speaker = segment.get('speaker', 'None')
                text = segment.get('text', '')[:50] + '...' if len(segment.get('text', '')) > 50 else segment.get('text', '')
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                print(f"   {i+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {text}")
        else:
            print("❌ FAILED: No speaker information in merged segments")

        # Save results
        complete_result = {
            'transcription': transcription_result,
            'speakers': speaker_result,
            'merged_segments': merged_segments,
            'processing_times': {
                'transcription': transcription_time,
                'speaker_identification': speaker_time,
                'total': transcription_time + speaker_time
            },
            'stats': {
                'total_segments': len(merged_segments),
                'segments_with_speakers': segments_with_speakers,
                'speakers_identified': len(speakers_list),
                'success': segments_with_speakers > 0
            }
        }

        output_file = "data/results/direct_services_test.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(complete_result, f, indent=2, default=str)

        print(f"\n💾 Complete result saved to: {output_file}")

        return complete_result

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_services_directly())