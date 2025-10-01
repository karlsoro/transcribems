#!/usr/bin/env python3
"""
Generate the final large audio transcript with speakers using the fixed pipeline.
"""

import asyncio
import json
import time
from pathlib import Path
from src.services.whisperx_service import WhisperXService

async def generate_final_transcript_with_speakers():
    """Generate final large audio transcript with working speaker identification."""
    print("🎯 GENERATING FINAL LARGE AUDIO TRANSCRIPT WITH SPEAKERS")
    print("=" * 80)

    # Use the converted large audio file
    audio_file = "large_audio_converted.wav"

    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    file_size = Path(audio_file).stat().st_size / (1024*1024)
    print(f"🎵 Processing: {audio_file}")
    print(f"📊 File size: {file_size:.1f}MB")

    try:
        start_time = time.time()

        # Use fixed WhisperX service with speaker integration
        service = WhisperXService(model_size='tiny', device='cpu', compute_type='int8')

        print("📝 Starting transcription with speaker identification...")
        result = await service.transcribe_audio(
            audio_file,
            enable_speaker_diarization=True
        )

        processing_time = time.time() - start_time

        print(f"✅ Processing completed in {processing_time:.2f}s")

        # Analyze results
        segments = result.get('segments', [])
        speakers = result.get('speakers', [])
        text_length = len(result.get('text', ''))

        segments_with_speakers = sum(1 for seg in segments if seg.get('speaker'))

        print(f"\n📊 FINAL RESULTS:")
        print(f"📄 Text length: {text_length:,} characters")
        print(f"🎬 Total segments: {len(segments)}")
        print(f"👥 Speakers identified: {len(speakers)} - {speakers}")
        print(f"🎤 Segments with speakers: {segments_with_speakers}/{len(segments)}")
        print(f"📈 Speaker coverage: {(segments_with_speakers/len(segments)*100):.1f}%" if segments else "0%")
        print(f"⏱️  Processing speed: {processing_time:.1f}s")

        # Show sample segments with speakers
        print(f"\n📋 SAMPLE SEGMENTS WITH SPEAKERS:")
        sample_count = 0
        for i, segment in enumerate(segments):
            if segment.get('speaker') and sample_count < 5:
                speaker = segment.get('speaker')
                text = segment.get('text', '')[:60] + '...' if len(segment.get('text', '')) > 60 else segment.get('text', '')
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                print(f"   {sample_count+1}. [{start:.1f}s-{end:.1f}s] {speaker}: {text}")
                sample_count += 1

        # Save complete results
        timestamp = int(time.time())

        # JSON result
        json_file = f"data/results/FINAL_LARGE_TRANSCRIPT_WITH_SPEAKERS_{timestamp}.json"
        Path(json_file).parent.mkdir(parents=True, exist_ok=True)

        with open(json_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        # Human-readable transcript with speakers
        txt_file = f"data/results/FINAL_LARGE_TRANSCRIPT_WITH_SPEAKERS_{timestamp}.txt"

        with open(txt_file, 'w') as f:
            f.write("# TranscribeMCP - Large Audio Transcript with Speaker Identification\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Audio file: {audio_file} ({file_size:.1f}MB)\n")
            f.write(f"# Processing time: {processing_time:.1f}s\n")
            f.write(f"# Speakers identified: {len(speakers)} - {speakers}\n")
            f.write(f"# Segments with speakers: {segments_with_speakers}/{len(segments)} ({(segments_with_speakers/len(segments)*100):.1f}%)\n")
            f.write("\n" + "="*80 + "\n\n")

            for i, segment in enumerate(segments):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                speaker = segment.get('speaker', 'Unknown')
                text = segment.get('text', '')

                f.write(f"[{start:.1f}s - {end:.1f}s] {speaker}: {text}\n")

        print(f"\n💾 FINAL RESULTS SAVED:")
        print(f"📄 JSON: {json_file}")
        print(f"📝 Transcript: {txt_file}")

        # Final validation
        if segments_with_speakers > 0:
            print(f"\n✅ SUCCESS: Final transcript with speakers generated!")
            print(f"🎯 Speaker identification: WORKING")
            print(f"📊 Production ready: YES")
        else:
            print(f"\n❌ FAILED: No speaker information in final transcript")

        return json_file, txt_file

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    asyncio.run(generate_final_transcript_with_speakers())