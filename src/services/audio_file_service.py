"""AudioFileService for file validation and metadata extraction.

This service handles audio file validation, format detection, metadata extraction,
and state management for the transcription pipeline.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes
import librosa
import soundfile as sf
from mutagen import File as MutagenFile

from ..models.audio_file_mcp import AudioFile
from ..models.types import AudioFileState, SUPPORTED_AUDIO_FORMATS, MAX_FILE_SIZE
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)


class AudioFileService:
    """Service for audio file validation and metadata extraction."""

    def __init__(self):
        """Initialize the audio file service."""
        self.error_handler = MCPErrorHandler()

    async def validate_and_create(self, file_path: str) -> AudioFile:
        """Validate file and create AudioFile instance with metadata.

        Args:
            file_path: Path to the audio file

        Returns:
            AudioFile: Validated audio file with metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or unsupported
        """
        try:
            # Basic validation and creation
            audio_file = AudioFile.from_path(file_path)
            logger.info(f"Created AudioFile for: {audio_file.file_name}")

            # Extract detailed metadata
            await self._extract_audio_metadata(audio_file)

            # Validate audio content
            await self._validate_audio_content(audio_file)

            # Calculate checksum for integrity
            audio_file.calculate_checksum()

            # Transition to analyzed state
            audio_file.transition_state(AudioFileState.ANALYZED)

            # Final validation for processing readiness
            if await self._validate_for_processing(audio_file):
                audio_file.transition_state(AudioFileState.READY)

            logger.info(f"AudioFile ready for processing: {audio_file.file_name}")
            return audio_file

        except Exception as e:
            logger.error(f"Failed to validate audio file {file_path}: {str(e)}")
            raise

    async def _extract_audio_metadata(self, audio_file: AudioFile) -> None:
        """Extract audio metadata using librosa and mutagen.

        Args:
            audio_file: AudioFile instance to update with metadata
        """
        try:
            # Use librosa to get basic audio information
            duration = librosa.get_duration(path=audio_file.file_path)
            audio_file.duration = duration

            # Try to get more detailed info with soundfile
            try:
                info = sf.info(audio_file.file_path)
                audio_file.sample_rate = info.samplerate
                audio_file.channels = info.channels
                logger.debug(f"Extracted metadata: duration={duration:.2f}s, sr={info.samplerate}, ch={info.channels}")
            except Exception as e:
                logger.warning(f"Could not extract detailed metadata with soundfile: {e}")
                # Fallback to librosa
                try:
                    y, sr = librosa.load(audio_file.file_path, sr=None, duration=1.0)  # Load just 1 second for metadata
                    audio_file.sample_rate = sr
                    audio_file.channels = 1 if len(y.shape) == 1 else y.shape[0]
                except Exception as e2:
                    logger.warning(f"Could not extract metadata with librosa: {e2}")

        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            raise ValueError(f"Could not analyze audio file: {e}")

    async def _validate_audio_content(self, audio_file: AudioFile) -> None:
        """Validate that the file contains valid audio content.

        Args:
            audio_file: AudioFile instance to validate
        """
        try:
            # Basic duration check
            if not audio_file.duration or audio_file.duration <= 0:
                raise ValueError("Audio file has no duration or invalid duration")

            # Check minimum duration (0.1 seconds)
            if audio_file.duration < 0.1:
                raise ValueError("Audio file is too short (minimum 0.1 seconds)")

            # Check reasonable maximum duration (24 hours)
            if audio_file.duration > 24 * 3600:
                raise ValueError("Audio file is too long (maximum 24 hours)")

            # Validate sample rate is reasonable
            if audio_file.sample_rate and (audio_file.sample_rate < 8000 or audio_file.sample_rate > 192000):
                raise ValueError(f"Invalid sample rate: {audio_file.sample_rate} Hz")

            # Validate channel count
            if audio_file.channels and (audio_file.channels < 1 or audio_file.channels > 8):
                raise ValueError(f"Invalid channel count: {audio_file.channels}")

        except Exception as e:
            logger.error(f"Audio content validation failed: {e}")
            raise

    async def _validate_for_processing(self, audio_file: AudioFile) -> bool:
        """Validate file is ready for transcription processing.

        Args:
            audio_file: AudioFile instance to validate

        Returns:
            bool: True if ready for processing
        """
        try:
            # Check file still exists and is readable
            path = Path(audio_file.file_path)
            if not path.exists() or not path.is_file():
                raise ValueError("Audio file no longer exists or is not accessible")

            # Verify checksum if available
            if audio_file.checksum and not audio_file.validate_integrity():
                raise ValueError("Audio file integrity check failed")

            # Check we have minimum required metadata
            if not audio_file.duration:
                raise ValueError("Audio file duration not available")

            return True

        except Exception as e:
            logger.error(f"Processing validation failed: {e}")
            audio_file.transition_state(AudioFileState.ERROR)
            return False

    async def batch_validate(self, file_paths: List[str]) -> Dict[str, Any]:
        """Validate multiple audio files concurrently.

        Args:
            file_paths: List of file paths to validate

        Returns:
            Dict containing successful validations and errors
        """
        if len(file_paths) > 10:
            raise ValueError("Batch size cannot exceed 10 files")

        results = {
            "valid_files": [],
            "invalid_files": [],
            "total_duration": 0.0
        }

        # Process files concurrently
        tasks = []
        for file_path in file_paths:
            task = asyncio.create_task(self._validate_single_file(file_path))
            tasks.append(task)

        # Wait for all validations to complete
        validation_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for file_path, result in zip(file_paths, validation_results):
            if isinstance(result, Exception):
                results["invalid_files"].append({
                    "file_path": file_path,
                    "error": str(result)
                })
            else:
                results["valid_files"].append(result)
                if result.duration:
                    results["total_duration"] += result.duration

        logger.info(f"Batch validation completed: {len(results['valid_files'])} valid, {len(results['invalid_files'])} invalid")
        return results

    async def _validate_single_file(self, file_path: str) -> AudioFile:
        """Validate a single file for batch processing.

        Args:
            file_path: Path to the file to validate

        Returns:
            AudioFile: Validated audio file
        """
        return await self.validate_and_create(file_path)

    def get_estimated_processing_time(self, audio_file: AudioFile) -> float:
        """Estimate processing time for an audio file.

        Args:
            audio_file: AudioFile to estimate processing time for

        Returns:
            float: Estimated processing time in seconds
        """
        if not audio_file.duration:
            return 60.0  # Default estimate

        # Base estimate: ~0.2x realtime for GPU, ~1.0x for CPU
        # This is conservative and can be adjusted based on benchmarks
        base_multiplier = 0.2  # Assuming GPU processing

        # Adjust for file characteristics
        duration_factor = 1.0
        if audio_file.duration > 3600:  # > 1 hour
            duration_factor = 1.2
        elif audio_file.duration > 1800:  # > 30 minutes
            duration_factor = 1.1

        # Adjust for quality/complexity
        quality_factor = 1.0
        if audio_file.sample_rate and audio_file.sample_rate > 44100:
            quality_factor = 1.1
        if audio_file.channels and audio_file.channels > 2:
            quality_factor *= 1.1

        estimated_time = audio_file.duration * base_multiplier * duration_factor * quality_factor

        # Add overhead for speaker diarization
        estimated_time *= 1.3

        # Minimum processing time
        return max(estimated_time, 5.0)

    def calculate_chunk_count(self, audio_file: AudioFile, chunk_length_seconds: int = 30) -> int:
        """Calculate number of chunks for processing.

        Args:
            audio_file: AudioFile to process
            chunk_length_seconds: Length of each chunk in seconds

        Returns:
            int: Number of chunks needed
        """
        if not audio_file.duration:
            return 1

        import math
        return max(1, math.ceil(audio_file.duration / chunk_length_seconds))

    async def cleanup_temp_files(self, audio_file: AudioFile) -> None:
        """Clean up any temporary files associated with audio processing.

        Args:
            audio_file: AudioFile to clean up
        """
        # This would clean up any temporary files created during processing
        # For now, just log the cleanup
        logger.debug(f"Cleaning up temporary files for: {audio_file.file_name}")

    def is_format_supported(self, file_path: str) -> bool:
        """Check if audio format is supported.

        Args:
            file_path: Path to check

        Returns:
            bool: True if format is supported
        """
        try:
            path = Path(file_path)
            format_ext = path.suffix[1:].upper() if path.suffix else ""
            return format_ext in SUPPORTED_AUDIO_FORMATS
        except Exception:
            return False

    def get_mime_type(self, file_path: str) -> Optional[str]:
        """Get MIME type for audio file.

        Args:
            file_path: Path to the file

        Returns:
            Optional[str]: MIME type or None
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type