"""
MCP Transcription Adapter for GPU-Enhanced SimpleWhisperXCLI.

This adapter bridges the MCP framework with our GPU-enhanced SimpleWhisperXCLI service,
providing job management, progress tracking, and result formatting for MCP tools.
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from .simple_whisperx_cli import SimpleWhisperXCLI
from ..models.transcription_job import TranscriptionJob
from ..models.transcription_result import TranscriptionResult, TranscriptionSegment, Speaker
from ..models.types import TranscriptionSettings, JobStatus

logger = logging.getLogger(__name__)


class MCPTranscriptionAdapter:
    """
    Adapter that bridges MCP framework with GPU-enhanced SimpleWhisperXCLI.

    Provides:
    - Job management and tracking
    - Progress callbacks
    - Result transformation
    - Error handling
    - GPU/CPU automatic detection
    """

    def __init__(self):
        """Initialize the MCP adapter."""
        self.whisperx_cli = SimpleWhisperXCLI()
        self.active_jobs: Dict[str, TranscriptionJob] = {}
        self.job_results: Dict[str, Dict[str, Any]] = {}
        self.job_progress: Dict[str, Dict[str, Any]] = {}

        logger.info(f"MCP Transcription Adapter initialized")
        logger.info(f"GPU available: {self.whisperx_cli._gpu_available}")

    async def transcribe_audio(
        self,
        file_path: str,
        settings: TranscriptionSettings,
        progress_callback: Optional[Callable] = None
    ) -> TranscriptionJob:
        """
        Start a transcription job using the GPU-enhanced service.

        Args:
            file_path: Path to audio file
            settings: Transcription settings from MCP
            progress_callback: Optional progress callback

        Returns:
            TranscriptionJob with job_id and initial status
        """

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create job object
        job = TranscriptionJob(
            job_id=job_id,
            file_path=file_path,
            settings=settings,
            status=JobStatus.PENDING,
            created_at=datetime.now()
        )

        # Store job
        self.active_jobs[job_id] = job
        self.job_progress[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Job created, waiting to start"
        }

        # Start processing asynchronously
        asyncio.create_task(self._process_transcription_async(job, progress_callback))

        logger.info(f"Transcription job created: {job_id} for file: {file_path}")
        return job

    async def _process_transcription_async(
        self,
        job: TranscriptionJob,
        progress_callback: Optional[Callable] = None
    ) -> None:
        """
        Process transcription asynchronously using SimpleWhisperXCLI.

        Args:
            job: TranscriptionJob to process
            progress_callback: Optional progress callback
        """
        job_id = job.job_id

        try:
            # Update status to processing
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
            self.job_progress[job_id] = {
                "status": "processing",
                "progress": 0.1,
                "message": "Starting transcription..."
            }

            if progress_callback:
                progress_callback(1, 10)

            logger.info(f"Starting transcription for job {job_id}")

            # Map MCP settings to SimpleWhisperXCLI parameters
            model_mapping = {
                "tiny": "tiny",
                "base": "base",
                "small": "small",
                "medium": "medium",
                "large": "large-v2"  # Use best version
            }

            model = model_mapping.get(job.settings.model_size, "base")

            # Update progress
            self.job_progress[job_id]["progress"] = 0.2
            self.job_progress[job_id]["message"] = f"Using model: {model}, GPU: {self.whisperx_cli._gpu_available}"

            if progress_callback:
                progress_callback(2, 10)

            # Call our GPU-enhanced service
            result = await self.whisperx_cli.transcribe_audio(
                audio_path=job.file_path,
                model=model,
                language=job.settings.language if job.settings.language else "en",
                enable_diarization=job.settings.enable_diarization,
                timeout_minutes=60,  # Extended timeout for large files
                # Let service auto-detect optimal GPU/CPU settings
            )

            # Update progress
            self.job_progress[job_id]["progress"] = 0.9
            self.job_progress[job_id]["message"] = "Processing results..."

            if progress_callback:
                progress_callback(9, 10)

            if result.get("success", False):
                # Transform result to MCP format
                mcp_result = self._transform_result_to_mcp(result, job)

                # Store result
                self.job_results[job_id] = mcp_result

                # Update job status
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.processing_time = result.get("processing_time_seconds", 0)

                # Final progress update
                self.job_progress[job_id] = {
                    "status": "completed",
                    "progress": 1.0,
                    "message": f"Completed successfully in {job.processing_time:.1f}s"
                }

                if progress_callback:
                    progress_callback(10, 10)

                logger.info(f"Transcription completed successfully: {job_id}")
                logger.info(f"Processing time: {job.processing_time:.1f}s, Device: {result.get('device_used')}")

            else:
                # Handle failure
                error_msg = result.get("error", "Unknown transcription error")
                raise Exception(error_msg)

        except Exception as e:
            # Handle errors
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()

            self.job_progress[job_id] = {
                "status": "failed",
                "progress": 0.0,
                "message": f"Failed: {str(e)}"
            }

            logger.error(f"Transcription failed for job {job_id}: {e}")

        finally:
            # Clean up active job (keep result and progress for retrieval)
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]

    def _transform_result_to_mcp(self, whisperx_result: Dict[str, Any], job: TranscriptionJob) -> Dict[str, Any]:
        """
        Transform SimpleWhisperXCLI result to MCP format.

        Args:
            whisperx_result: Result from SimpleWhisperXCLI
            job: Original job information

        Returns:
            Dict in MCP format
        """

        # Extract segments and transform to MCP format
        segments = []
        whisperx_segments = whisperx_result.get("segments", [])

        for i, seg in enumerate(whisperx_segments):
            mcp_segment = TranscriptionSegment(
                segment_id=f"seg_{i:04d}",
                start_time=seg.get("start", 0.0),
                end_time=seg.get("end", 0.0),
                text=seg.get("text", "").strip(),
                confidence=seg.get("avg_logprob", 0.0),
                speaker_id=seg.get("speaker", "SPEAKER_00")
            )
            segments.append(mcp_segment)

        # Extract speaker information
        speakers = []
        unique_speakers = set()

        for seg in whisperx_segments:
            speaker_id = seg.get("speaker")
            if speaker_id and speaker_id not in unique_speakers:
                unique_speakers.add(speaker_id)

                # Calculate speaker statistics
                speaker_segments = [s for s in whisperx_segments if s.get("speaker") == speaker_id]
                total_time = sum(s.get("end", 0) - s.get("start", 0) for s in speaker_segments)

                speaker = Speaker(
                    speaker_id=speaker_id,
                    speaker_label=speaker_id,  # Could be enhanced with names
                    total_speech_time=total_time,
                    segment_count=len(speaker_segments),
                    confidence=0.8  # Default confidence for diarization
                )
                speakers.append(speaker)

        # Create MCP result
        mcp_result = {
            "job_id": job.job_id,
            "status": "completed",
            "result": {
                "text": whisperx_result.get("text", ""),
                "confidence_score": self._calculate_average_confidence(whisperx_segments),
                "language": whisperx_result.get("language_detected", "en"),
                "processing_time": whisperx_result.get("processing_time_seconds", 0),
                "word_count": len(whisperx_result.get("text", "").split()),
                "segments": [seg.__dict__ for seg in segments],
                "speakers": [spk.__dict__ for spk in speakers],
                "metadata": {
                    "whisperx_version": "3.4.2",
                    "model_size": job.settings.model_size,
                    "device_used": whisperx_result.get("device_used", "unknown"),
                    "gpu_available": whisperx_result.get("gpu_available", False),
                    "realtime_factor": whisperx_result.get("realtime_factor", 0.0),
                    "file_size_mb": whisperx_result.get("file_size_mb", 0.0),
                    "audio_duration": whisperx_result.get("audio_duration_seconds", 0.0),
                    "diarization_enabled": job.settings.enable_diarization,
                    "chunks_processed": len(whisperx_segments)
                }
            }
        }

        return mcp_result

    def _calculate_average_confidence(self, segments: list) -> float:
        """Calculate average confidence score from segments."""
        if not segments:
            return 0.0

        confidences = [seg.get("avg_logprob", 0.0) for seg in segments]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """
        Get progress information for a job.

        Args:
            job_id: Job identifier

        Returns:
            Progress information dict
        """
        return self.job_progress.get(job_id, {
            "status": "not_found",
            "progress": 0.0,
            "message": "Job not found"
        })

    def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result for a completed job.

        Args:
            job_id: Job identifier

        Returns:
            Job result or None if not found/completed
        """
        return self.job_results.get(job_id)

    def list_jobs(self, limit: int = 10, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        List recent jobs.

        Args:
            limit: Maximum number of jobs to return
            status_filter: Filter by status

        Returns:
            Jobs list and metadata
        """
        all_jobs = []

        # Add active jobs
        for job in self.active_jobs.values():
            all_jobs.append({
                "job_id": job.job_id,
                "file_path": job.file_path,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            })

        # Add completed jobs from progress tracking
        for job_id, progress in self.job_progress.items():
            if job_id not in self.active_jobs:
                all_jobs.append({
                    "job_id": job_id,
                    "file_path": "unknown",  # Could be stored separately
                    "status": progress["status"],
                    "progress": progress["progress"]
                })

        # Apply status filter
        if status_filter:
            all_jobs = [job for job in all_jobs if job["status"] == status_filter]

        # Sort by creation time (newest first) and limit
        all_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        limited_jobs = all_jobs[:limit]

        return {
            "jobs": limited_jobs,
            "total_count": len(all_jobs)
        }

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running job.

        Args:
            job_id: Job identifier

        Returns:
            Cancellation result
        """
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()

            self.job_progress[job_id] = {
                "status": "cancelled",
                "progress": 0.0,
                "message": "Cancelled by user"
            }

            del self.active_jobs[job_id]

            return {
                "job_id": job_id,
                "status": "cancelled",
                "message": "Job cancelled successfully"
            }
        else:
            return {
                "job_id": job_id,
                "status": "not_found",
                "message": "Job not found or already completed"
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information including GPU status."""
        return {
            "gpu_available": self.whisperx_cli._gpu_available,
            "active_jobs": len(self.active_jobs),
            "total_jobs_tracked": len(self.job_progress),
            "service_type": "GPU-Enhanced SimpleWhisperXCLI"
        }