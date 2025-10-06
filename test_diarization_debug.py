"""
Debug script to test speaker diarization with detailed error reporting.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Fix cuDNN library path BEFORE importing torch/whisperx
cudnn_path = Path(sys.prefix) / "lib" / "python3.12" / "site-packages" / "nvidia" / "cudnn" / "lib"
if cudnn_path.exists():
    current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if str(cudnn_path) not in current_ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{cudnn_path}:{current_ld_path}"
        print(f"Set LD_LIBRARY_PATH to include: {cudnn_path}")

from src.core.config import get_settings
from src.services.whisperx_service import WhisperXService

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_diarization():
    settings = get_settings()

    print(f"\n=== Configuration ===")
    print(f"HF_TOKEN loaded: {settings.HF_TOKEN is not None}")
    print(f"Token preview: {settings.HF_TOKEN[:15] if settings.HF_TOKEN else 'None'}...")
    print(f"Model: {settings.WHISPER_MODEL}")
    print(f"Device: {settings.DEVICE}")

    # Find test audio file
    audio_file = Path("uploads/a46f7aad-5765-4b45-a1b8-ce6a6f7e79f9.wav")
    if not audio_file.exists():
        audio_file = Path("uploads").glob("*.wav")
        audio_file = next(audio_file, None)
        if not audio_file:
            print("ERROR: No audio file found in uploads/")
            return

    print(f"\n=== Testing with: {audio_file} ===")

    # Create service
    service = WhisperXService(
        model_size="base",  # Use smaller model for testing
        device=settings.DEVICE,
        hf_token=settings.HF_TOKEN
    )

    try:
        print("\n=== Starting transcription with diarization ===")
        result = await service.transcribe_audio(
            audio_path=str(audio_file),
            language="en",
            enable_speaker_diarization=True,
            batch_size=8,
            chunk_length=30
        )

        print(f"\n=== Results ===")
        print(f"Speakers found: {result['speakers']}")
        print(f"Number of segments: {len(result['segments'])}")
        print(f"Segments with speakers: {sum(1 for s in result['segments'] if s.get('speaker'))}")

        # Show first few segments with speakers
        print(f"\n=== Sample segments ===")
        for i, seg in enumerate(result['segments'][:5]):
            speaker = seg.get('speaker', 'NO_SPEAKER')
            text = seg.get('text', '')[:50]
            print(f"[{i}] {speaker}: {text}...")

    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print(f"Exception repr: {repr(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_diarization())
