"""Transcribe audio MCP tool.

This tool handles audio file transcription using WhisperX.
It validates files, processes them through the transcription service,
and returns job status information.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..services.audio_file_service import AudioFileService
from ..services.transcription_service import TranscriptionService
from ..services.progress_service import ProgressService
from ..services.storage_service import StorageService
from ..models.transcription_job import TranscriptionJob
from ..models.types import TranscriptionSettings, JobStatus
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize services
audio_service = AudioFileService()
transcription_service = TranscriptionService()
progress_service = ProgressService()
storage_service = StorageService()
error_handler = MCPErrorHandler()

async def transcribe_audio_tool(request: dict) -> dict:
    """MCP tool for audio transcription.

    Args:
        request: MCP request containing:
            - file_path: Path to audio file
            - model_size: WhisperX model size (tiny, base, small, medium, large)
            - language: Language code (optional, auto-detect if None)
            - enable_diarization: Enable speaker diarization
            - output_format: Output format preference
            - device: Processing device (cpu, cuda)
            - compute_type: Compute type (int8, int16, float16, float32)

    Returns:
        dict: Job status and information
    """
    try:
        # Extract parameters
        file_path = request.get('file_path')
        if not file_path:
            return error_handler.file_not_found("file_path parameter is required")

        # Validate file exists
        if not Path(file_path).exists():
            return error_handler.file_not_found(f"Audio file not found: {file_path}")

        # Create transcription settings
        settings = TranscriptionSettings(
            model_size=request.get('model_size', 'base'),
            language=request.get('language'),  # None for auto-detect
            enable_diarization=request.get('enable_diarization', True),
            output_format=request.get('output_format', 'detailed'),
            device=request.get('device', 'cpu'),
            compute_type=request.get('compute_type', 'int8'),
            chunk_length=request.get('chunk_length', 30),
            beam_size=request.get('beam_size', 5),
            temperature=request.get('temperature', 0.0)
        )

        # Validate and create audio file
        try:
            audio_file = await audio_service.validate_and_create(file_path)
            logger.info(f"Audio file validated: {audio_file.file_name}")
        except ValueError as e:
            return error_handler.invalid_file(str(e))
        except FileNotFoundError as e:
            return error_handler.file_not_found(str(e))

        # Create transcription job
        job = TranscriptionJob(
            audio_file=audio_file,
            settings=settings
        )

        # Register job for progress tracking
        progress_service.register_job(job)

        # Save job to storage
        await storage_service.save_job(job)

        # Update history
        await storage_service.update_history(job)

        # Start transcription asynchronously
        asyncio.create_task(_process_transcription_async(job))

        # Return job status
        job_status = job.to_status_dict()
        job_status.update({
            "estimated_duration": transcription_service.estimate_processing_time(audio_file, settings),
            "model_info": transcription_service.get_model_info(settings)
        })

        return {
            "success": True,
            "job": job_status
        }

    except Exception as e:
        logger.error(f"Transcription tool error: {e}")
        return error_handler.internal_error(f"Transcription failed: {str(e)}")

async def _process_transcription_async(job: TranscriptionJob) -> None:
    """Process transcription asynchronously.

    Args:
        job: TranscriptionJob to process
    """
    try:
        # Progress callback
        def progress_callback(current: int, total: int) -> None:
            progress_service.update_job_progress(job.job_id, current, total)

        # Process transcription
        result = await transcription_service.process_transcription(job, progress_callback)

        # Save result
        await storage_service.save_result(result)

        # Update job and history
        await storage_service.save_job(job)
        await storage_service.update_history(job)

        # Complete job in progress service
        progress_service.complete_job(job.job_id)

        logger.info(f"Transcription completed successfully: {job.job_id}")

    except Exception as e:
        # Mark job as failed
        progress_service.fail_job(job.job_id, str(e))

        # Update storage
        await storage_service.save_job(job)
        await storage_service.update_history(job)

        logger.error(f"Transcription failed: {job.job_id} - {e}")

# Set function name for tests
transcribe_audio_tool.__name__ = 'transcribe_audio_tool'