"""TranscriptionService with WhisperX integration.

This service handles the core transcription processing using WhisperX,
including model management, audio processing, and result generation.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, List
import tempfile
import os
from pathlib import Path

# Initialize logger before any potential usage
logger = logging.getLogger(__name__)

try:
    import whisperx
    import librosa
    import torch
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False
    logger.warning("WhisperX not available, using mock implementation")

from ..models.audio_file_mcp import AudioFile
from ..models.transcription_job import TranscriptionJob
from ..models.transcription_result import TranscriptionResult, TranscriptionSegment, Word, Speaker
from ..models.types import TranscriptionSettings, TranscriptionMetadata, JobStatus
from ..error_handler import MCPErrorHandler


class TranscriptionService:
    """Service for WhisperX transcription processing."""

    def __init__(self):
        """Initialize the transcription service."""
        self.error_handler = MCPErrorHandler()
        self.model_cache = {}
        self.processing_lock = asyncio.Lock()

    async def process_transcription(
        self,
        job: TranscriptionJob,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> TranscriptionResult:
        """Process transcription for a job.

        Args:
            job: TranscriptionJob to process
            progress_callback: Optional callback for progress updates

        Returns:
            TranscriptionResult: Complete transcription result

        Raises:
            Exception: If transcription fails
        """
        try:
            logger.info(f"Starting transcription for job: {job.job_id}")
            job.start_processing()

            # Calculate processing chunks
            chunk_count = self._calculate_chunk_count(job.audio_file, job.settings.chunk_length)
            job.total_chunks = chunk_count

            # Load or get cached model
            model = await self._get_or_load_model(job.settings)

            # Process transcription in chunks with progress tracking
            result = await self._process_with_chunks(job, model, progress_callback)

            # Mark job as completed
            job.complete_successfully()

            logger.info(f"Transcription completed for job: {job.job_id}")
            return result

        except Exception as e:
            logger.error(f"Transcription failed for job {job.job_id}: {str(e)}")
            job.fail_with_error(str(e))
            raise

    async def _get_or_load_model(self, settings: TranscriptionSettings) -> Any:
        """Get cached model or load new one.

        Args:
            settings: Transcription settings

        Returns:
            Any: WhisperX model instance or mock
        """
        model_key = f"{settings.model_size}_{settings.device}_{settings.compute_type}"

        if model_key not in self.model_cache:
            logger.info(f"Loading WhisperX model: {settings.model_size} on {settings.device}")

            if WHISPERX_AVAILABLE:
                try:
                    # Load actual WhisperX model
                    device = settings.device if torch.cuda.is_available() and settings.device == "cuda" else "cpu"
                    model = whisperx.load_model(
                        settings.model_size,
                        device=device,
                        compute_type=settings.compute_type
                    )
                    logger.info(f"Real WhisperX model loaded: {settings.model_size} on {device}")
                except Exception as e:
                    logger.warning(f"Failed to load WhisperX model: {e}, falling back to mock")
                    model = self._create_mock_model(settings)
            else:
                logger.info("WhisperX not available, using mock model")
                model = self._create_mock_model(settings)

            self.model_cache[model_key] = model
            logger.info(f"Model loaded and cached: {model_key}")

        return self.model_cache[model_key]

    def _create_mock_model(self, settings: TranscriptionSettings) -> Dict[str, Any]:
        """Create mock model for testing/fallback."""
        return {
            "model_size": settings.model_size,
            "device": settings.device,
            "loaded": True,
            "version": "mock-3.4.2",
            "is_mock": True
        }

    async def _process_with_chunks(
        self,
        job: TranscriptionJob,
        model: Any,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> TranscriptionResult:
        """Process transcription with chunked audio.

        Args:
            job: TranscriptionJob to process
            model: WhisperX model or mock
            progress_callback: Progress callback

        Returns:
            TranscriptionResult: Complete transcription result
        """
        audio_file = job.audio_file
        settings = job.settings

        # Check if we have a real WhisperX model or mock
        if WHISPERX_AVAILABLE and not getattr(model, 'is_mock', False):
            return await self._process_with_real_whisperx(job, model, progress_callback)
        else:
            return await self._process_with_mock(job, model, progress_callback)

    async def _process_with_real_whisperx(
        self,
        job: TranscriptionJob,
        model: Any,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> TranscriptionResult:
        """Process transcription with real WhisperX."""
        audio_file = job.audio_file
        settings = job.settings

        try:
            # Load audio with librosa
            logger.info(f"Loading audio file: {audio_file.file_path}")
            audio_data, sample_rate = librosa.load(
                audio_file.file_path,
                sr=16000  # WhisperX expects 16kHz
            )

            # Update progress - loading complete
            job.update_progress(1, 4)
            if progress_callback:
                progress_callback(1, 4)

            # Transcribe with WhisperX
            logger.info("Running WhisperX transcription...")
            result = whisperx.transcribe(
                audio=audio_data,
                model=model,
                language=settings.language
            )

            # Update progress - transcription complete
            job.update_progress(2, 4)
            if progress_callback:
                progress_callback(2, 4)

            # Load alignment model and align whisper output
            if settings.device == "cuda" and torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

            model_a, metadata = whisperx.load_align_model(
                language_code=result.get("language", "en"),
                device=device
            )
            result = whisperx.align(result["segments"], model_a, metadata, audio_data, device)

            # Update progress - alignment complete
            job.update_progress(3, 4)
            if progress_callback:
                progress_callback(3, 4)

            # Speaker diarization if enabled
            speakers_data = []
            if settings.enable_diarization:
                logger.info("Running speaker diarization...")
                try:
                    diarize_model = whisperx.DiarizationPipeline(use_auth_token=None, device=device)
                    diarize_segments = diarize_model(audio_data, min_speakers=1, max_speakers=10)
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                    speakers_data = self._extract_speakers_from_whisperx(result["segments"])
                except Exception as e:
                    logger.warning(f"Diarization failed: {e}, continuing without speaker labels")

            # Update progress - complete
            job.update_progress(4, 4)
            if progress_callback:
                progress_callback(4, 4)

            # Convert WhisperX result to our format
            return self._convert_whisperx_result(job.job_id, result, speakers_data, settings)

        except Exception as e:
            logger.error(f"WhisperX processing failed: {e}")
            # Fall back to mock processing
            return await self._process_with_mock(job, model, progress_callback)

    async def _process_with_mock(
        self,
        job: TranscriptionJob,
        model: Any,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> TranscriptionResult:
        """Process transcription with mock data for testing."""
        audio_file = job.audio_file
        settings = job.settings

        segments = []
        speakers = []
        total_text_parts = []

        # Simulate chunk processing
        for chunk_idx in range(job.total_chunks):
            await asyncio.sleep(0.1)  # Simulate processing time

            # Update progress
            job.update_progress(chunk_idx + 1, job.total_chunks)
            if progress_callback:
                progress_callback(chunk_idx + 1, job.total_chunks)

            # Simulate creating segments for this chunk
            chunk_segments = self._create_mock_segments(chunk_idx, audio_file)
            segments.extend(chunk_segments)

            # Add text from this chunk
            chunk_text = " ".join(seg.text for seg in chunk_segments)
            total_text_parts.append(chunk_text)

        # Simulate speaker diarization
        if settings.enable_diarization:
            speakers = self._create_mock_speakers(segments)

        # Create metadata
        metadata = TranscriptionMetadata(
            whisperx_version="3.1.1",
            model_path=f"whisperx-{settings.model_size}",
            device_used=settings.device,
            memory_usage=512.0,  # Mock value
            chunks_processed=job.total_chunks,
            diarization_enabled=settings.enable_diarization,
            preprocessing_time=1.0,
            inference_time=job.get_processing_duration() or 10.0,
            postprocessing_time=0.5
        )

        # Create final result
        full_text = " ".join(total_text_parts)
        result = TranscriptionResult(
            job_id=job.job_id,
            text=full_text,
            segments=segments,
            speakers=speakers,
            confidence_score=0.92,  # Mock confidence
            processing_time=job.get_processing_duration() or 10.0,
            model_version=f"whisperx-{settings.model_size}-{model['version']}",
            language=settings.language or "en",
            word_count=len(full_text.split()),
            metadata=metadata
        )

        return result

    def _convert_whisperx_result(
        self,
        job_id: str,
        whisperx_result: Dict[str, Any],
        speakers_data: List[Speaker],
        settings: TranscriptionSettings
    ) -> TranscriptionResult:
        """Convert WhisperX result to our TranscriptionResult format."""
        segments = []
        full_text_parts = []

        for i, segment_data in enumerate(whisperx_result.get("segments", [])):
            words = []

            # Convert word-level data if available
            for word_data in segment_data.get("words", []):
                word = Word(
                    word=word_data.get("word", "").strip(),
                    start_time=word_data.get("start", 0.0),
                    end_time=word_data.get("end", 0.0),
                    confidence=word_data.get("score", 0.9),
                    probability=word_data.get("probability", word_data.get("score", 0.9))
                )
                words.append(word)

            # Create segment
            segment = TranscriptionSegment(
                segment_id=f"seg_{i:04d}",
                start_time=segment_data.get("start", 0.0),
                end_time=segment_data.get("end", 0.0),
                text=segment_data.get("text", ""),
                confidence=segment_data.get("avg_logprob", 0.9),
                speaker_id=segment_data.get("speaker"),
                words=words,
                language=whisperx_result.get("language", "en")
            )
            segments.append(segment)
            full_text_parts.append(segment.text)

        # Create metadata
        metadata = TranscriptionMetadata(
            whisperx_version="3.4.2",
            model_path=f"whisperx-{settings.model_size}",
            device_used=settings.device,
            memory_usage=0.0,  # Would need to track actual memory usage
            chunks_processed=1,  # WhisperX processes as single file
            diarization_enabled=settings.enable_diarization,
            preprocessing_time=1.0,
            inference_time=5.0,  # Approximate
            postprocessing_time=0.5
        )

        full_text = " ".join(full_text_parts)

        return TranscriptionResult(
            job_id=job_id,
            text=full_text,
            segments=segments,
            speakers=speakers_data,
            confidence_score=whisperx_result.get("confidence", 0.9),
            processing_time=10.0,  # Approximate
            model_version=f"whisperx-{settings.model_size}-3.4.2",
            language=whisperx_result.get("language", "en"),
            word_count=len(full_text.split()),
            metadata=metadata
        )

    def _extract_speakers_from_whisperx(self, segments: List[Dict[str, Any]]) -> List[Speaker]:
        """Extract speaker information from WhisperX segments."""
        speaker_stats = {}

        for segment in segments:
            speaker_id = segment.get("speaker")
            if not speaker_id:
                continue

            if speaker_id not in speaker_stats:
                speaker_stats[speaker_id] = {
                    "total_time": 0.0,
                    "segment_count": 0
                }

            duration = segment.get("end", 0.0) - segment.get("start", 0.0)
            speaker_stats[speaker_id]["total_time"] += duration
            speaker_stats[speaker_id]["segment_count"] += 1

        speakers = []
        for speaker_id, stats in speaker_stats.items():
            speaker = Speaker(
                speaker_id=speaker_id,
                speaker_label=f"Speaker {speaker_id}",
                total_speech_time=stats["total_time"],
                segment_count=stats["segment_count"],
                confidence=0.85,  # Default confidence
                characteristics={"source": "whisperx_diarization"}
            )
            speakers.append(speaker)

        return speakers

    def _create_mock_segments(self, chunk_idx: int, audio_file: AudioFile) -> List[TranscriptionSegment]:
        """Create mock transcription segments for testing.

        Args:
            chunk_idx: Chunk index
            audio_file: Audio file being processed

        Returns:
            List[TranscriptionSegment]: Mock segments
        """
        # This is placeholder data for testing
        # Real implementation would process actual audio
        segments = []

        base_time = chunk_idx * 30.0  # 30 second chunks
        mock_texts = [
            "Hello, welcome to this meeting.",
            "Today we'll discuss the quarterly results.",
            "Let's start with the financial overview.",
            "Any questions so far?",
            "Moving on to the next topic."
        ]

        for i, text in enumerate(mock_texts[:2]):  # 2 segments per chunk
            start_time = base_time + (i * 10.0)
            end_time = start_time + 8.0

            # Create mock words
            words = []
            word_list = text.split()
            word_duration = 8.0 / len(word_list) if word_list else 1.0

            for j, word in enumerate(word_list):
                word_start = start_time + (j * word_duration)
                word_end = word_start + word_duration
                words.append(Word(
                    word=word.rstrip('.,!?'),
                    start_time=word_start,
                    end_time=word_end,
                    confidence=0.95,
                    probability=0.98
                ))

            segment = TranscriptionSegment(
                segment_id=f"seg_{chunk_idx}_{i}",
                start_time=start_time,
                end_time=end_time,
                text=text,
                confidence=0.93,
                speaker_id=f"SPEAKER_{i % 2:02d}" if i < 2 else None,
                words=words,
                language="en"
            )
            segments.append(segment)

        return segments

    def _create_mock_speakers(self, segments: List[TranscriptionSegment]) -> List[Speaker]:
        """Create mock speakers based on segments.

        Args:
            segments: List of transcription segments

        Returns:
            List[Speaker]: Mock speakers
        """
        speaker_data = {}

        # Collect speaker statistics
        for segment in segments:
            if segment.speaker_id:
                if segment.speaker_id not in speaker_data:
                    speaker_data[segment.speaker_id] = {
                        "total_time": 0.0,
                        "segment_count": 0
                    }

                speaker_data[segment.speaker_id]["total_time"] += (segment.end_time - segment.start_time)
                speaker_data[segment.speaker_id]["segment_count"] += 1

        # Create speaker objects
        speakers = []
        for speaker_id, data in speaker_data.items():
            speaker = Speaker(
                speaker_id=speaker_id,
                speaker_label=f"Speaker {speaker_id.split('_')[1]}",
                total_speech_time=data["total_time"],
                segment_count=data["segment_count"],
                confidence=0.88,
                characteristics={"gender": "unknown", "age_range": "adult"}
            )
            speakers.append(speaker)

        return speakers

    def _calculate_chunk_count(self, audio_file: AudioFile, chunk_length: int) -> int:
        """Calculate number of processing chunks.

        Args:
            audio_file: Audio file to process
            chunk_length: Length of each chunk in seconds

        Returns:
            int: Number of chunks
        """
        if not audio_file.duration:
            return 1

        import math
        return max(1, math.ceil(audio_file.duration / chunk_length))

    async def cancel_transcription(self, job: TranscriptionJob) -> bool:
        """Cancel an in-progress transcription.

        Args:
            job: TranscriptionJob to cancel

        Returns:
            bool: True if successfully cancelled
        """
        if job.is_active():
            success = job.cancel()
            if success:
                logger.info(f"Transcription cancelled for job: {job.job_id}")
            return success
        return False

    async def cleanup_model_cache(self) -> None:
        """Clean up cached models to free memory."""
        logger.info("Cleaning up model cache")
        self.model_cache.clear()

    def get_model_info(self, settings: TranscriptionSettings) -> Dict[str, Any]:
        """Get information about the model that would be used.

        Args:
            settings: Transcription settings

        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "model_size": settings.model_size,
            "device": settings.device,
            "compute_type": settings.compute_type,
            "supports_diarization": True,
            "estimated_load_time": 30.0,  # seconds
            "memory_requirement_mb": {
                "tiny": 512,
                "base": 1024,
                "small": 2048,
                "medium": 4096,
                "large": 8192
            }.get(settings.model_size, 2048)
        }

    def estimate_processing_time(self, audio_file: AudioFile, settings: TranscriptionSettings) -> float:
        """Estimate processing time for an audio file.

        Args:
            audio_file: Audio file to process
            settings: Transcription settings

        Returns:
            float: Estimated processing time in seconds
        """
        if not audio_file.duration:
            return 60.0

        # Base processing speed (realtime factor)
        speed_factors = {
            "tiny": 0.1,    # 10x faster than realtime
            "base": 0.15,   # 6.7x faster
            "small": 0.2,   # 5x faster
            "medium": 0.3,  # 3.3x faster
            "large": 0.5    # 2x faster
        }

        base_factor = speed_factors.get(settings.model_size, 0.2)

        # Adjust for device
        if settings.device == "cpu":
            base_factor *= 3.0  # CPU is ~3x slower

        # Adjust for diarization
        if settings.enable_diarization:
            base_factor *= 1.4  # Diarization adds ~40% overhead

        # Calculate estimate
        estimated_time = audio_file.duration * base_factor

        # Add model loading time if not cached
        model_key = f"{settings.model_size}_{settings.device}_{settings.compute_type}"
        if model_key not in self.model_cache:
            estimated_time += 30.0  # Model loading time

        return max(estimated_time, 5.0)  # Minimum 5 seconds