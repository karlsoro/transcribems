"""
WhisperX service integration for speech recognition and speaker diarization.
"""

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import gc

# Configure audio backend to suppress warnings (no torchcodec dependency)
import os
import warnings
warnings.filterwarnings("ignore", message=".*torchaudio._backend.*deprecated.*")
warnings.filterwarnings("ignore", message=".*torchaudio.*")
os.environ.setdefault('TORCHAUDIO_BACKEND', 'soundfile')

import torch
import whisperx
from whisperx import load_model, load_align_model, load_audio

from src.core.logging import get_logger
from src.services.gpu_service import GPUService


logger = get_logger(__name__)


class WhisperXService:
    """
    WhisperX service for advanced speech recognition with speaker diarization.
    """

    def __init__(
        self,
        model_size: str = "large-v2",
        device: Optional[str] = None,
        compute_type: str = "float16",
        hf_token: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ):
        """
        Initialize WhisperX service.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large, large-v2)
            device: Device to use (cuda, cpu, or auto)
            compute_type: Compute type for inference (float16, float32, int8)
            hf_token: Hugging Face token for speaker diarization model
            progress_callback: Optional async callback for progress updates (progress: float, message: str)
        """
        self.model_size = model_size
        self.compute_type = compute_type
        self.hf_token = hf_token
        self.progress_callback = progress_callback

        # Device setup
        self.gpu_service = GPUService(defer_initialization=True)
        if device == "auto" or device is None:
            self.device = self._select_device()
        else:
            self.device = device

        # Models (loaded lazily)
        self._whisper_model = None
        self._align_model = None
        self._align_metadata = None
        self._diarization_pipeline = None

        logger.info(f"WhisperX service initialized", extra={
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "gpu_available": self.gpu_service.is_gpu_available()
        })

    async def _report_progress(self, progress: float, message: str) -> None:
        """Report progress via callback if available."""
        if self.progress_callback:
            try:
                if asyncio.iscoroutinefunction(self.progress_callback):
                    await self.progress_callback(progress, message)
                else:
                    self.progress_callback(progress, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def _select_device(self) -> str:
        """Select optimal device for processing."""
        try:
            if self.gpu_service.is_gpu_available():
                optimal_gpu = self.gpu_service.select_optimal_device()
                if optimal_gpu:
                    # Use just "cuda" instead of "cuda:0" for ctranslate2 compatibility
                    return "cuda"
        except Exception:
            # If GPU service fails, fall back to CPU
            pass
        return "cpu"

    async def load_models(self, language: str = "en") -> None:
        """
        Load required models for transcription and alignment.

        Args:
            language: Language code for alignment model

        Raises:
            RuntimeError: If model loading fails
        """
        try:
            logger.info("Loading WhisperX models", extra={
                "model_size": self.model_size,
                "language": language,
                "device": self.device
            })

            # Load Whisper model (run in thread to avoid blocking)
            if not self._whisper_model:
                logger.debug("Loading Whisper model")
                self._whisper_model = await asyncio.to_thread(
                    load_model,
                    whisper_arch=self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    language=language if language != "auto" else None
                )
                logger.info("Whisper model loaded successfully")

            # Load alignment model (run in thread to avoid blocking)
            if not self._align_model and language != "auto":
                logger.debug(f"Loading alignment model for language: {language}")
                try:
                    self._align_model, self._align_metadata = await asyncio.to_thread(
                        load_align_model,
                        language_code=language,
                        device=self.device
                    )
                    logger.info("Alignment model loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load alignment model: {e}")
                    self._align_model = None
                    self._align_metadata = None

        except Exception as e:
            logger.error(f"Failed to load WhisperX models: {e}", exc_info=True)
            raise RuntimeError(f"Model loading failed: {str(e)}")

    async def load_diarization_pipeline(self) -> None:
        """
        Load speaker diarization pipeline.

        Raises:
            RuntimeError: If diarization pipeline loading fails
        """
        if not self.hf_token:
            logger.warning("No Hugging Face token provided, speaker diarization disabled")
            return

        try:
            logger.info("Loading speaker diarization pipeline")

            # Import diarization pipeline
            from pyannote.audio import Pipeline

            # Load pipeline in thread to avoid blocking
            self._diarization_pipeline = await asyncio.to_thread(
                Pipeline.from_pretrained,
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )

            # Move to GPU if available
            if self.device.startswith("cuda") and torch.cuda.is_available():
                self._diarization_pipeline.to(torch.device(self.device))

            logger.info("Speaker diarization pipeline loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load diarization pipeline: {e}", exc_info=True)
            self._diarization_pipeline = None
            raise RuntimeError(f"Diarization pipeline loading failed: {str(e)}")

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "auto",
        enable_speaker_diarization: bool = False,
        batch_size: int = 16,
        chunk_length: int = 30
    ) -> Dict[str, Any]:
        """
        Transcribe audio file with optional speaker diarization.

        Args:
            audio_path: Path to audio file
            language: Language code or "auto"
            enable_speaker_diarization: Enable speaker identification
            batch_size: Batch size for processing
            chunk_length: Chunk length in seconds

        Returns:
            Dict containing transcription results

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        start_time = time.time()
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info("Starting audio transcription", extra={
            "audio_file": str(audio_path),
            "language": language,
            "speaker_diarization": enable_speaker_diarization,
            "device": self.device
        })

        try:
            # Load audio (run in thread to avoid blocking)
            await self._report_progress(10, "Loading audio file")
            logger.debug("Loading audio file")
            audio = await asyncio.to_thread(load_audio, str(audio_path))
            audio_duration = len(audio) / 16000  # WhisperX uses 16kHz

            # Load models
            await self._report_progress(20, "Loading AI models")
            await self.load_models(language)

            # Transcribe (run in thread to avoid blocking event loop)
            await self._report_progress(30, "Transcribing audio")
            logger.debug("Starting transcription")
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._whisper_model.transcribe,
                        audio,
                        batch_size=batch_size,
                        chunk_size=chunk_length,
                        language=None if language == "auto" else language
                    ),
                    timeout=3600  # 1 hour timeout
                )
                logger.debug("Transcription completed")
            except asyncio.TimeoutError:
                logger.error("Transcription timed out after 1 hour")
                raise RuntimeError("Transcription timed out")

            detected_language = result.get("language", language)
            await self._report_progress(60, f"Transcription completed (language: {detected_language})")
            logger.info(f"Transcription completed, detected language: {detected_language}")

            # Align transcription (if alignment model available)
            if self._align_model and self._align_metadata:
                await self._report_progress(70, "Aligning transcription")
                logger.debug("Aligning transcription")
                aligned_result = await asyncio.to_thread(
                    whisperx.align,
                    result["segments"],
                    self._align_model,
                    self._align_metadata,
                    audio,
                    self.device,
                    return_char_alignments=False
                )
                # Merge aligned segments back into result dict
                result["segments"] = aligned_result.get("segments", result["segments"])
                if "word_segments" in aligned_result:
                    result["word_segments"] = aligned_result["word_segments"]

            # Speaker diarization using pyannote.audio
            # Note: Requires LD_LIBRARY_PATH set (handled by current server startup)
            speakers = []
            if enable_speaker_diarization:
                await self._report_progress(75, "Identifying speakers")
                logger.debug("Performing speaker diarization with pyannote.audio")
                try:
                    # Load diarization pipeline if not loaded
                    if not self._diarization_pipeline:
                        await self.load_diarization_pipeline()

                    if self._diarization_pipeline:
                        # Run diarization in thread to avoid blocking
                        # Pass audio file path directly to pyannote pipeline
                        diarization_result = await asyncio.to_thread(
                            self._diarization_pipeline,
                            str(audio_path)
                        )

                        logger.debug(f"Diarization completed, type: {type(diarization_result)}")

                        # Convert pyannote annotation to list of speaker segments
                        # This bypasses the buggy WhisperX assign_word_speakers function
                        speaker_segments = []
                        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
                            speaker_segments.append({
                                "start": turn.start,
                                "end": turn.end,
                                "speaker": speaker
                            })

                        logger.debug(f"Found {len(speaker_segments)} speaker segments from diarization")

                        # Assign speakers to transcription segments based on timing overlap
                        # Uses existing _assign_speakers_to_segments method for compatibility
                        result = self._assign_speakers_to_segments(
                            result.get("segments", []),
                            speaker_segments
                        )

                        # Wrap back into result dict
                        result = {"segments": result}

                        # Extract unique speakers from segments
                        speakers_set = set()
                        for segment in result.get("segments", []):
                            if "speaker" in segment and segment["speaker"]:
                                speakers_set.add(segment["speaker"])

                        speakers = list(speakers_set)
                        logger.info(f"Speaker diarization found {len(speakers)} unique speakers: {speakers}")

                        # Count segments with speakers
                        segments_with_speakers = sum(1 for seg in result.get("segments", []) if seg.get("speaker"))
                        logger.info(f"Assigned speakers to {segments_with_speakers}/{len(result.get('segments', []))} segments")
                    else:
                        logger.warning("Diarization pipeline not available, speaker diarization disabled")

                except Exception as e:
                    logger.error(f"Native WhisperX speaker diarization failed: {type(e).__name__}: {str(e)}", exc_info=True)
                    speakers = []

            processing_time = time.time() - start_time
            realtime_factor = audio_duration / processing_time if processing_time > 0 else 0

            # Format segments and extract full text
            await self._report_progress(90, "Formatting results")
            formatted_segments = self._format_segments(result.get("segments", []))
            full_text = " ".join(seg.get("text", "").strip() for seg in formatted_segments if seg.get("text", "").strip())

            # Format response
            response = {
                "text": full_text,  # Add full text field
                "segments": formatted_segments,
                "speakers": speakers,
                "language": detected_language,
                "language_probability": result.get("language_probability"),
                "processing_time": processing_time,
                "audio_duration": audio_duration,
                "realtime_factor": realtime_factor,
                "model_name": self.model_size,
                "device": self.device,
                "gpu_used": self.device.startswith("cuda")
            }

            logger.info("Transcription completed successfully", extra={
                "segments_count": len(response["segments"]),
                "speakers_count": len(speakers),
                "processing_time": processing_time,
                "realtime_factor": realtime_factor
            })

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Transcription failed after {processing_time:.2f}s: {e}",
                        extra={"audio_file": str(audio_path)}, exc_info=True)
            raise RuntimeError(f"Transcription failed: {str(e)}")

        finally:
            # Cleanup GPU memory
            if self.device.startswith("cuda"):
                self.gpu_service.cleanup_memory()

    async def _perform_diarization(
        self,
        audio_path: Path,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform speaker diarization on audio.

        Args:
            audio_path: Path to audio file
            segments: Transcription segments

        Returns:
            Dict containing diarized segments and speaker list
        """
        try:
            # Run diarization
            diarization = self._diarization_pipeline(str(audio_path))

            # Convert diarization to speaker segments
            speaker_segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            # Assign speakers to transcription segments
            diarized_segments = self._assign_speakers_to_segments(
                segments, speaker_segments
            )

            # Get unique speakers
            speakers = list(set(seg.get("speaker") for seg in diarized_segments if seg.get("speaker")))

            return {
                "segments": diarized_segments,
                "speakers": speakers
            }

        except Exception as e:
            logger.warning(f"Speaker diarization failed: {e}")
            return {
                "segments": segments,
                "speakers": []
            }

    def _assign_speakers_to_segments(
        self,
        transcription_segments: List[Dict[str, Any]],
        speaker_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Assign speakers to transcription segments based on timing overlap.

        Args:
            transcription_segments: Segments from transcription
            speaker_segments: Speaker segments from diarization

        Returns:
            List of segments with speaker assignments
        """
        diarized_segments = []

        for segment in transcription_segments:
            segment_start = segment.get("start", 0)
            segment_end = segment.get("end", 0)
            segment_mid = (segment_start + segment_end) / 2

            # Find overlapping speaker
            assigned_speaker = None
            max_overlap = 0

            for speaker_seg in speaker_segments:
                overlap = max(0, min(segment_end, speaker_seg["end"]) -
                            max(segment_start, speaker_seg["start"]))

                if overlap > max_overlap:
                    max_overlap = overlap
                    assigned_speaker = speaker_seg["speaker"]

            # Create new segment with speaker assignment
            new_segment = segment.copy()
            if assigned_speaker:
                new_segment["speaker"] = assigned_speaker

            diarized_segments.append(new_segment)

        return diarized_segments

    def _format_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format segments to consistent structure.

        Args:
            segments: Raw segments from WhisperX

        Returns:
            Formatted segments
        """
        formatted_segments = []

        for segment in segments:
            formatted_segment = {
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
                "text": segment.get("text", "").strip(),
                "confidence": segment.get("confidence"),
                "speaker": segment.get("speaker")
            }

            # Only include segments with text
            if formatted_segment["text"]:
                formatted_segments.append(formatted_segment)

        return formatted_segments

    def get_device_info(self) -> Dict[str, Any]:
        """
        Get information about the processing device.

        Returns:
            Dict containing device information
        """
        device_info = {
            "device_type": "cuda" if self.device.startswith("cuda") else "cpu",
            "device_name": self.device,
            "gpu_available": self.gpu_service.is_gpu_available(),
            "model_size": self.model_size,
            "compute_type": self.compute_type
        }

        if self.device.startswith("cuda") and ":" in self.device:
            try:
                device_id = int(self.device.split(":")[-1])
                gpu_info = self.gpu_service.get_memory_usage(device_id=device_id)
                device_info.update(gpu_info)
            except (ValueError, IndexError):
                # Handle malformed device string
                pass

        return device_info

    def is_gpu_available(self) -> bool:
        """Check if GPU is available for processing."""
        return self.gpu_service.is_gpu_available()

    async def cleanup(self) -> None:
        """Clean up loaded models and free memory."""
        logger.info("Cleaning up WhisperX service")

        # Clear models
        self._whisper_model = None
        self._align_model = None
        self._align_metadata = None
        self._diarization_pipeline = None

        # Force garbage collection
        gc.collect()

        # Clear GPU memory
        if self.device.startswith("cuda"):
            self.gpu_service.cleanup_memory()

        logger.info("WhisperX service cleanup completed")

    def __del__(self):
        """Cleanup on object destruction."""
        try:
            asyncio.create_task(self.cleanup())
        except Exception:
            pass  # Ignore cleanup errors during destruction