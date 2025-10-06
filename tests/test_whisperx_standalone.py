"""
Standalone WhisperX transcription test with extensive debugging and logging.
This script validates the transcribe routine outside the web server context.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_whisperx_standalone.log')
    ]
)
logger = logging.getLogger(__name__)

# Suppress audio backend warnings
import warnings
warnings.filterwarnings("ignore", message=".*torchaudio.*")
warnings.filterwarnings("ignore", message=".*TorchAudio.*")
os.environ.setdefault('TORCHAUDIO_BACKEND', 'soundfile')

def test_whisperx_transcription():
    """Test WhisperX transcription with the same parameters as web server."""

    # Test file path
    test_audio_file = project_root / "test_data" / "large_audio_converted.wav"

    logger.info("=" * 80)
    logger.info("STANDALONE WHISPERX TRANSCRIPTION TEST")
    logger.info("=" * 80)
    logger.info(f"Test audio file: {test_audio_file}")
    logger.info(f"File exists: {test_audio_file.exists()}")

    if not test_audio_file.exists():
        logger.error(f"Test file not found: {test_audio_file}")
        return False

    # Get file info
    file_size = test_audio_file.stat().st_size
    logger.info(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")

    # Load environment configuration
    logger.info("\n" + "=" * 80)
    logger.info("LOADING ENVIRONMENT CONFIGURATION")
    logger.info("=" * 80)

    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded .env from: {env_file}")
    else:
        logger.warning(f".env file not found at: {env_file}")

    # Get HF token
    hf_token = os.getenv('HF_TOKEN')
    logger.info(f"HF_TOKEN present: {bool(hf_token)}")
    if hf_token:
        logger.info(f"HF_TOKEN length: {len(hf_token)}")

    # Test parameters (matching web server defaults)
    language = "en"  # Using "en" like the fixed web server code
    enable_diarization = True

    logger.info(f"Language: {language}")
    logger.info(f"Enable speaker diarization: {enable_diarization}")

    # Import WhisperX service
    logger.info("\n" + "=" * 80)
    logger.info("IMPORTING WHISPERX SERVICE")
    logger.info("=" * 80)

    start_import = time.time()
    from src.services.whisperx_service import WhisperXService
    import_duration = time.time() - start_import
    logger.info(f"WhisperXService import completed in {import_duration:.2f}s")

    # Initialize service
    logger.info("\n" + "=" * 80)
    logger.info("INITIALIZING WHISPERX SERVICE")
    logger.info("=" * 80)

    start_init = time.time()
    service = WhisperXService()
    init_duration = time.time() - start_init
    logger.info(f"WhisperXService initialization completed in {init_duration:.2f}s")

    # Load models
    logger.info("\n" + "=" * 80)
    logger.info("LOADING WHISPERX MODELS")
    logger.info("=" * 80)

    start_load = time.time()
    try:
        import asyncio
        asyncio.run(service.load_models())
        load_duration = time.time() - start_load
        logger.info(f"Models loaded successfully in {load_duration:.2f}s")
        logger.info(f"Device: {service.device}")
        logger.info(f"Compute type: {service.compute_type}")
    except Exception as e:
        logger.error(f"Failed to load models: {e}", exc_info=True)
        return False

    # Run transcription
    logger.info("\n" + "=" * 80)
    logger.info("STARTING TRANSCRIPTION")
    logger.info("=" * 80)

    start_transcribe = time.time()
    try:
        logger.info("Calling model.transcribe()...")
        logger.info(f"Parameters: audio_file={test_audio_file}, language={language}")

        # Run transcription with same async pattern as web server
        result = asyncio.run(service.transcribe_audio(
            audio_path=str(test_audio_file),
            language=language,
            enable_speaker_diarization=enable_diarization
        ))

        transcribe_duration = time.time() - start_transcribe
        logger.info(f"Transcription completed in {transcribe_duration:.2f}s ({transcribe_duration / 60:.2f} minutes)")

        # Log results
        logger.info("\n" + "=" * 80)
        logger.info("TRANSCRIPTION RESULTS")
        logger.info("=" * 80)

        if result:
            logger.info(f"Result keys: {result.keys()}")

            if 'segments' in result:
                segment_count = len(result['segments'])
                logger.info(f"Segments count: {segment_count}")

                if segment_count > 0:
                    logger.info(f"First segment: {result['segments'][0]}")
                    logger.info(f"Last segment: {result['segments'][-1]}")

            if 'text' in result:
                text_length = len(result['text'])
                logger.info(f"Transcribed text length: {text_length} characters")
                logger.info(f"First 200 chars: {result['text'][:200]}")

            if 'language' in result:
                logger.info(f"Detected language: {result['language']}")

            # Speaker diarization info
            speaker_segments = [s for s in result.get('segments', []) if 'speaker' in s]
            if speaker_segments:
                unique_speakers = set(s['speaker'] for s in speaker_segments)
                logger.info(f"Speaker diarization: {len(unique_speakers)} unique speakers")
                logger.info(f"Speakers: {sorted(unique_speakers)}")
            else:
                logger.info("No speaker diarization data found")
        else:
            logger.warning("Transcription returned None/empty result")

        # Total time
        total_duration = time.time() - start_import
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total test duration: {total_duration:.2f}s ({total_duration / 60:.2f} minutes)")
        logger.info(f"  - Import: {import_duration:.2f}s")
        logger.info(f"  - Initialization: {init_duration:.2f}s")
        logger.info(f"  - Model loading: {load_duration:.2f}s")
        logger.info(f"  - Transcription: {transcribe_duration:.2f}s")
        logger.info("Test PASSED ✅")

        return True

    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")

        # Log timing even on failure
        transcribe_duration = time.time() - start_transcribe
        logger.info(f"Failed after {transcribe_duration:.2f}s")

        logger.info("Test FAILED ❌")
        return False


if __name__ == "__main__":
    logger.info("Starting standalone WhisperX transcription test...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Project root: {project_root}")

    success = test_whisperx_transcription()

    if success:
        logger.info("\n✅ Standalone test completed successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Standalone test failed")
        sys.exit(1)
