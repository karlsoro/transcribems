"""Batch transcription MCP tool.

This tool handles batch transcription of multiple audio files
with shared settings and progress tracking.
"""

import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path

from ..services.audio_file_service import AudioFileService
from ..services.transcription_service import TranscriptionService
from ..services.progress_service import ProgressService
from ..services.storage_service import StorageService
from ..models.transcription_job import TranscriptionJob
from ..models.types import TranscriptionSettings
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize services
audio_service = AudioFileService()
transcription_service = TranscriptionService()
progress_service = ProgressService()
storage_service = StorageService()
error_handler = MCPErrorHandler()

async def batch_transcribe_tool(request: dict) -> dict:
    """MCP tool for batch audio transcription.

    Args:
        request: MCP request containing:
            - file_paths: List of audio file paths
            - model_size: WhisperX model size for all files
            - language: Language code (optional, auto-detect if None)
            - enable_diarization: Enable speaker diarization
            - output_format: Output format preference
            - device: Processing device (cpu, cuda)
            - compute_type: Compute type (int8, int16, float16, float32)
            - max_concurrent: Maximum concurrent jobs (default 3)

    Returns:
        dict: Batch job status and information
    """
    try:
        file_paths = request.get('file_paths', [])
        if not file_paths:
            return error_handler.invalid_parameters("file_paths parameter is required")

        if len(file_paths) > 10:
            return error_handler.invalid_parameters("Maximum 10 files allowed for batch processing")

        max_concurrent = min(request.get('max_concurrent', 3), 5)  # Cap at 5 for resource management

        # Create shared transcription settings
        settings = TranscriptionSettings(
            model_size=request.get('model_size', 'base'),
            language=request.get('language'),
            enable_diarization=request.get('enable_diarization', True),
            output_format=request.get('output_format', 'detailed'),
            device=request.get('device', 'cpu'),
            compute_type=request.get('compute_type', 'int8'),
            chunk_length=request.get('chunk_length', 30),
            beam_size=request.get('beam_size', 5),
            temperature=request.get('temperature', 0.0)
        )

        # Validate all files first
        logger.info(f"Validating {len(file_paths)} files for batch processing")
        validation_results = await audio_service.batch_validate(file_paths)

        if not validation_results['valid_files']:
            return {
                "success": False,
                "error": {
                    "code": "NO_VALID_FILES",
                    "message": "No valid audio files found",
                    "validation_errors": validation_results['invalid_files']
                }
            }

        # Create jobs for valid files
        jobs = []
        for audio_file in validation_results['valid_files']:
            job = TranscriptionJob(
                audio_file=audio_file,
                settings=settings
            )
            jobs.append(job)

            # Register job for progress tracking
            progress_service.register_job(job)

            # Save job to storage
            await storage_service.save_job(job)
            await storage_service.update_history(job)

        # Start batch processing with concurrency limit
        batch_id = f"batch_{jobs[0].job_id[:8]}_{len(jobs)}files"
        logger.info(f"Starting batch processing: {batch_id} with {len(jobs)} jobs")

        # Process jobs in batches with concurrency control
        asyncio.create_task(_process_batch_async(jobs, max_concurrent, batch_id))

        # Prepare response
        job_statuses = []
        total_estimated_time = 0.0

        for job in jobs:
            job_status = job.to_status_dict()
            estimated_time = transcription_service.estimate_processing_time(job.audio_file, settings)
            job_status["estimated_duration"] = estimated_time
            total_estimated_time += estimated_time
            job_statuses.append(job_status)

        response = {
            "success": True,
            "batch_id": batch_id,
            "total_jobs": len(jobs),
            "valid_files": len(validation_results['valid_files']),
            "invalid_files": len(validation_results['invalid_files']),
            "total_duration": validation_results['total_duration'],
            "estimated_processing_time": total_estimated_time / max_concurrent,  # Adjusted for concurrency
            "max_concurrent": max_concurrent,
            "jobs": job_statuses
        }

        # Include validation errors if any
        if validation_results['invalid_files']:
            response["validation_errors"] = validation_results['invalid_files']

        return response

    except Exception as e:
        logger.error(f"Batch transcription tool error: {e}")
        return error_handler.internal_error(f"Batch transcription failed: {str(e)}")

async def _process_batch_async(jobs: List[TranscriptionJob], max_concurrent: int, batch_id: str) -> None:
    """Process batch of transcription jobs with concurrency control.

    Args:
        jobs: List of TranscriptionJob instances
        max_concurrent: Maximum concurrent jobs
        batch_id: Batch identifier for logging
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_single_job(job: TranscriptionJob) -> None:
        async with semaphore:
            try:
                # Progress callback
                def progress_callback(current: int, total: int) -> None:
                    progress_service.update_job_progress(job.job_id, current, total)

                # Process transcription
                result = await transcription_service.process_transcription(job, progress_callback)

                # Save result
                await storage_service.save_result(result)
                await storage_service.save_job(job)
                await storage_service.update_history(job)

                # Complete job in progress service
                progress_service.complete_job(job.job_id)

                logger.info(f"Batch job completed: {job.job_id} (batch: {batch_id})")

            except Exception as e:
                # Mark job as failed
                progress_service.fail_job(job.job_id, str(e))
                await storage_service.save_job(job)
                await storage_service.update_history(job)
                logger.error(f"Batch job failed: {job.job_id} (batch: {batch_id}) - {e}")

    # Start all jobs concurrently with semaphore control
    tasks = [process_single_job(job) for job in jobs]
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(f"Batch processing completed: {batch_id}")

batch_transcribe_tool.__name__ = 'batch_transcribe_tool'