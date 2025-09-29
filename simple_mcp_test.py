#!/usr/bin/env python3
"""
Simple MCP test that directly uses the working WhisperX service.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, '.')

from src.services.whisperx_service import WhisperXService
from src.services.speaker_service import SpeakerIdentificationService

async def simple_mcp_transcribe(file_path: str, **kwargs) -> dict:
    """Simple MCP-style transcription function."""

    # Extract parameters
    model_size = kwargs.get('model_size', 'tiny')
    device = kwargs.get('device', 'cpu')
    compute_type = kwargs.get('compute_type', 'int8')
    enable_diarization = kwargs.get('enable_diarization', True)

    print(f"🎵 Transcribing: {file_path}")
    print(f"⚙️  Model: {model_size}, Device: {device}, Diarization: {enable_diarization}")

    try:
        # Initialize services
        whisper_service = WhisperXService(
            model_size=model_size,
            device=device,
            compute_type=compute_type
        )

        # Transcribe
        transcription_result = await whisper_service.transcribe_audio(file_path)

        # Get speaker information if enabled
        speakers_result = None
        if enable_diarization:
            speaker_service = SpeakerIdentificationService()
            speakers_result = await speaker_service.identify_speakers(file_path)

        # Format MCP response
        mcp_response = {
            "success": True,
            "job_id": f"simple_test_{int(asyncio.get_event_loop().time())}",
            "status": "completed",
            "audio_file": file_path,
            "transcription": {
                "text": transcription_result.get("text", ""),
                "language": transcription_result.get("language", ""),
                "segments": transcription_result.get("segments", [])
            },
            "speakers": speakers_result if speakers_result else {"count": 0, "speakers": []},
            "metadata": {
                "model_size": model_size,
                "device": device,
                "processing_time": transcription_result.get("processing_time", 0),
                "audio_duration": transcription_result.get("audio_duration", 0)
            }
        }

        return mcp_response

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "job_id": None,
            "status": "failed"
        }

async def test_simple_mcp():
    """Test the simple MCP function."""
    print("🔌 TESTING SIMPLE MCP TRANSCRIPTION")
    print("=" * 60)

    # Test parameters
    test_file = "test_data/audio/short_speech.wav"

    # Test the function
    result = await simple_mcp_transcribe(
        file_path=test_file,
        model_size="tiny",
        device="cpu",
        compute_type="int8",
        enable_diarization=True
    )

    print(f"\n📊 MCP RESULT:")
    print(f"✅ Success: {result.get('success', False)}")

    if result.get('success'):
        print(f"📄 Text: \"{result['transcription']['text']}\"")
        print(f"🗣️  Language: {result['transcription']['language']}")
        print(f"👥 Speakers: {result['speakers'].get('count', 0)}")
        print(f"⏱️  Time: {result['metadata']['processing_time']:.2f}s")

        # Save result
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)

        result_file = output_dir / "simple_mcp_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"💾 Saved to: {result_file}")

    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

    return result.get('success', False)

if __name__ == "__main__":
    success = asyncio.run(test_simple_mcp())

    if success:
        print(f"\n🎉 SIMPLE MCP TEST SUCCESSFUL!")
        print("✅ Ready for integration with Claude Desktop")
    else:
        print(f"\n💥 SIMPLE MCP TEST FAILED")

    sys.exit(0 if success else 1)