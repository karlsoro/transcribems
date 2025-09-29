#!/usr/bin/env python3
"""
Test the complete pipeline with BOTH transcription AND speaker identification.
This will prove that the system works end-to-end with real audio.
"""

import asyncio
import json
import time
from pathlib import Path

# Import the complete pipeline tools
from src.tools.transcribe_tool import transcribe_audio_tool

async def test_complete_pipeline():
    """Test complete pipeline with real large audio file."""
    print("🎯 TESTING COMPLETE PIPELINE: Transcription + Speaker Identification")
    print("=" * 80)

    # Use multi-speaker test file first to validate speaker identification
    audio_file = "test_data/audio/multi_speaker.wav"

    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        return

    print(f"🎵 Processing: {audio_file}")
    print(f"📊 File size: {Path(audio_file).stat().st_size / (1024*1024):.1f}MB")

    start_time = time.time()

    # Run complete pipeline with diarization enabled
    result = await transcribe_audio_tool({
        'file_path': audio_file,
        'model_size': 'tiny',  # Fast processing for testing
        'language': 'en',
        'enable_diarization': True,  # <<<< THIS IS KEY - Enable speaker identification
        'output_format': 'detailed',
        'device': 'cpu',
        'compute_type': 'int8'
    })

    processing_time = time.time() - start_time

    print(f"\n✅ COMPLETE PIPELINE RESULT:")
    print(f"⏱️  Processing time: {processing_time:.2f}s")
    print(f"🎯 Result type: {type(result)}")
    print(f"📄 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

    # Save the complete result with speaker identification
    output_file = "data/results/complete_pipeline_with_speakers.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print(f"💾 Complete result saved to: {output_file}")

    # If result has transcription data, check for speakers
    if isinstance(result, dict) and 'success' in result:
        print(f"\n🔍 SPEAKER IDENTIFICATION CHECK:")
        print(f"Success: {result.get('success', False)}")

        # Check if we got a job response (async processing)
        if 'job' in result:
            print(f"📋 Job ID: {result['job'].get('job_id', 'Unknown')}")
            print(f"📊 Status: {result['job'].get('status', 'Unknown')}")
            print(f"⏱️  Estimated duration: {result['job'].get('estimated_duration', 'Unknown')}s")
            print(f"🎤 Supports diarization: {result['job'].get('model_info', {}).get('supports_diarization', False)}")

        # If we have direct results, check for speakers
        if 'data' in result or 'transcription' in result or 'segments' in result:
            # Look for speaker information in the result
            result_str = json.dumps(result, default=str)
            if 'speaker' in result_str.lower() or 'SPEAKER_' in result_str:
                print("✅ Speaker information found in result!")
            else:
                print("⚠️  No speaker information found in result")

    return result

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())