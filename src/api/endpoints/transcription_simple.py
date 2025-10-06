"""
Simplified FastAPI endpoints for audio transcription without Celery dependency.
This provides a REST API interface for testing and simple deployments.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import aiofiles

from src.models.audio_file import AudioFile
from src.services.whisperx_service import WhisperXService
from src.services.job_storage import get_job_storage
from src.core.logging import get_logger
from src.core.config import get_settings


logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["transcription"])
settings = get_settings()
job_storage = get_job_storage()


@router.post("/transcribe", response_model=Dict[str, Any])
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("auto", description="Language code (auto for detection)"),
    enable_speaker_diarization: bool = Form(True, description="Enable speaker identification"),
    model_size: str = Form("base", description="WhisperX model size")
) -> JSONResponse:
    """
    Upload and transcribe an audio file with speaker identification.

    This is a simplified synchronous endpoint for testing without Celery.
    For production use, use the MCP server with async job processing.

    Args:
        file: Uploaded audio file
        language: Language code or 'auto' for detection
        enable_speaker_diarization: Whether to identify speakers
        model_size: WhisperX model size

    Returns:
        JSON response with job ID and status URL
    """
    job_id = str(uuid.uuid4())

    logger.info("Audio transcription request received", extra={
        "job_id": job_id,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "language": language,
        "speaker_diarization": enable_speaker_diarization,
        "model_size": model_size
    })

    try:
        # Validate file format
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": f"Unsupported audio format: {file.content_type}",
                    "supported_formats": list(AudioFile.SUPPORTED_FORMATS)
                }
            )

        # Save uploaded file
        upload_path = await _save_uploaded_file(file, job_id)

        # Create AudioFile instance for validation
        try:
            audio_file = AudioFile.from_upload(str(upload_path), file.filename)
        except ValueError as e:
            logger.error("Audio file validation failed", extra={
                "job_id": job_id,
                "error": str(e)
            })
            upload_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=422,
                detail={"error": str(e)}
            )

        # Initialize job in persistent storage
        await job_storage.create_job({
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "progress_message": "Job queued",
            "original_filename": file.filename,
            "audio_file_path": str(upload_path),
            "language": language,
            "enable_speaker_diarization": enable_speaker_diarization,
            "model_size": model_size,
            "estimated_processing_time": audio_file.get_estimated_processing_time()
        })

        # Start transcription in background
        asyncio.create_task(_process_transcription(
            job_id=job_id,
            audio_file_path=str(upload_path),
            language=language,
            enable_speaker_diarization=enable_speaker_diarization,
            model_size=model_size
        ))

        logger.info("Transcription job queued", extra={
            "job_id": job_id,
            "file_path": str(upload_path)
        })

        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "message": "Transcription job started",
                "status_url": f"/v1/jobs/{job_id}",
                "estimated_processing_time": audio_file.get_estimated_processing_time()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Transcription request failed", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error during transcription setup"}
        )


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(job_id: str) -> JSONResponse:
    """
    Get the status and results of a transcription job.

    Args:
        job_id: Unique job identifier

    Returns:
        JSON response with job status and results
    """
    logger.info("Job status request", extra={"job_id": job_id})

    job = await job_storage.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job not found: {job_id}"}
        )

    job_data = job

    return JSONResponse(content=job_data)


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str) -> JSONResponse:
    """
    Cancel a transcription job.

    Args:
        job_id: Unique job identifier

    Returns:
        JSON response confirming cancellation
    """
    logger.info("Job cancellation request", extra={"job_id": job_id})

    job = await job_storage.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job not found: {job_id}"}
        )

    job_data = job
    current_status = job_data.get("status")

    if current_status in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Cannot cancel job in status: {current_status}"}
        )

    # Update status to cancelled
    job_data["status"] = "cancelled"
    job = job_data

    logger.info("Job cancelled", extra={"job_id": job_id})

    return JSONResponse(content={
        "job_id": job_id,
        "message": "Job cancelled successfully",
        "status": "cancelled"
    })


@router.get("/jobs/{job_id}/download")
async def download_transcription(job_id: str) -> JSONResponse:
    """
    Download the transcription results.

    Args:
        job_id: Unique job identifier

    Returns:
        File response with transcription results
    """
    logger.info("Transcription download request", extra={"job_id": job_id})

    job = await job_storage.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Job not found: {job_id}"}
        )

    job_data = job

    if job_data.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail={"error": f"Job not completed. Current status: {job_data.get('status')}"}
        )

    output_file_path = job_data.get("output_file")
    if not output_file_path or not Path(output_file_path).exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "Transcription file not found"}
        )

    return JSONResponse(content={
        "job_id": job_id,
        "download_url": f"/v1/files/{job_id}/transcription.json",
        "file_size": Path(output_file_path).stat().st_size,
        "format": "json"
    })


async def _save_uploaded_file(file: UploadFile, job_id: str) -> Path:
    """
    Save uploaded file to upload directory.

    Args:
        file: Uploaded file
        job_id: Job identifier for unique naming

    Returns:
        Path to saved file
    """
    try:
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix
        upload_filename = f"{job_id}{file_extension}"
        upload_path = upload_dir / upload_filename

        async with aiofiles.open(upload_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):
                await f.write(chunk)

        logger.debug("File saved successfully", extra={
            "job_id": job_id,
            "upload_path": str(upload_path)
        })

        return upload_path

    except Exception as e:
        logger.error("Failed to save uploaded file", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)
        raise RuntimeError(f"Failed to save uploaded file: {str(e)}")


async def _process_transcription(
    job_id: str,
    audio_file_path: str,
    language: str = "auto",
    enable_speaker_diarization: bool = True,
    model_size: str = "base"
) -> None:
    """
    Process transcription job asynchronously.

    Args:
        job_id: Unique job identifier
        audio_file_path: Path to audio file
        language: Language code or 'auto'
        enable_speaker_diarization: Enable speaker identification
        model_size: WhisperX model size
    """
    try:
        # Update status to processing
        await job_storage.update_job(job_id, {
            "status": "processing",
            "progress": 5,
            "progress_message": "Initializing transcription"
        })

        logger.info("Starting transcription processing", extra={"job_id": job_id})

        # Progress callback
        async def progress_callback(progress: float, message: str):
            await job_storage.update_progress(job_id, progress, message)

        # Initialize WhisperX service with progress tracking
        whisperx_service = WhisperXService(
            model_size=model_size,
            device=settings.DEVICE,
            hf_token=settings.HF_TOKEN,
            progress_callback=progress_callback
        )

        # Run transcription
        # WhisperX needs a language code for alignment models, default to "en" for auto-detection
        lang_code = "en" if language == "auto" else language
        result = await whisperx_service.transcribe_audio(
            audio_path=audio_file_path,
            language=lang_code,
            enable_speaker_diarization=enable_speaker_diarization
        )

        # Save results
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get original filename from job
        job_data = await job_storage.get_job(job_id)
        original_filename = job_data.get("original_filename", "unknown.wav") if job_data else "unknown.wav"

        # Add metadata to result
        result["metadata"] = {
            "original_filename": original_filename,
            "job_id": job_id,
            "language": result.get("language", language)
        }

        output_file = output_dir / f"{job_id}_transcription.json"

        import json
        async with aiofiles.open(output_file, 'w') as f:
            await f.write(json.dumps(result, indent=2))

        # Update job status
        await job_storage.update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "progress_message": "Transcription completed",
            "result": result,
            "output_file": str(output_file),
            "segments_count": len(result.get("segments", [])),
            "speakers_count": len(result.get("speakers", []))
        })

        # Cleanup
        await whisperx_service.cleanup()

        logger.info("Transcription completed successfully", extra={"job_id": job_id})

    except Exception as e:
        logger.error("Transcription processing failed", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)

        await job_storage.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__
        })


def _is_valid_language_code(language: str) -> bool:
    """Validate language code."""
    valid_languages = {
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
        'ar', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi', 'he', 'hi',
        'th', 'vi', 'uk', 'cs', 'hu', 'ro', 'bg', 'hr', 'sk', 'sl'
    }
    return language.lower() in valid_languages
