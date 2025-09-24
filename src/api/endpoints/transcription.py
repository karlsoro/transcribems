"""
FastAPI endpoints for audio transcription.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import aiofiles

from src.models.audio_file import AudioFile
from src.models.transcription import Transcription, ProcessingStatus
from src.services.whisperx_service import WhisperXService
from src.tasks.transcription_tasks import transcribe_audio_task
from src.core.logging import get_logger
from src.core.config import get_settings


logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["transcription"])
settings = get_settings()


@router.post("/transcribe", response_model=Dict[str, Any])
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("auto", description="Language code (auto for detection)"),
    enable_speaker_diarization: bool = Form(True, description="Enable speaker identification"),
    model_size: str = Form("large-v2", description="WhisperX model size")
) -> JSONResponse:
    """
    Upload and transcribe an audio file with speaker identification.

    Args:
        background_tasks: FastAPI background tasks
        file: Uploaded audio file
        language: Language code or 'auto' for detection
        enable_speaker_diarization: Whether to identify speakers
        model_size: WhisperX model size

    Returns:
        JSON response with job ID and status URL

    Raises:
        HTTPException: If file validation or processing setup fails
    """
    job_id = str(uuid.uuid4())

    logger.info("Audio transcription request received", extra={
        "job_id": job_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "language": language,
        "speaker_diarization": enable_speaker_diarization,
        "model_size": model_size
    })

    try:
        # Validate file format
        if not file.content_type or not file.content_type.startswith('audio/'):
            logger.warning("Invalid file format", extra={
                "job_id": job_id,
                "content_type": file.content_type
            })
            raise HTTPException(
                status_code=422,
                detail={
                    "error": f"Unsupported audio format: {file.content_type}",
                    "supported_formats": list(AudioFile.SUPPORTED_FORMATS)
                }
            )

        # Validate file size
        if hasattr(file, 'size') and file.size > AudioFile.MAX_FILE_SIZE:
            logger.warning("File too large", extra={
                "job_id": job_id,
                "file_size": file.size,
                "max_size": AudioFile.MAX_FILE_SIZE
            })
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File too large: {file.size} bytes. Maximum: {AudioFile.MAX_FILE_SIZE} bytes"
                }
            )

        # Validate language parameter
        if language != "auto" and not _is_valid_language_code(language):
            raise HTTPException(
                status_code=422,
                detail={"error": f"Invalid language code: {language}"}
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
            # Cleanup uploaded file
            upload_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=422,
                detail={"error": str(e)}
            )

        # Create transcription job
        transcription_job = Transcription.create_job(
            job_id=job_id,
            audio_file_path=str(upload_path),
            original_filename=file.filename
        )

        # Queue background transcription task
        background_tasks.add_task(
            transcribe_audio_task,
            job_id=job_id,
            audio_file_path=str(upload_path),
            language=language,
            enable_speaker_diarization=enable_speaker_diarization,
            model_size=model_size
        )

        logger.info("Transcription job queued", extra={
            "job_id": job_id,
            "file_path": str(upload_path),
            "estimated_processing_time": audio_file.get_estimated_processing_time()
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

    Raises:
        HTTPException: If job not found
    """
    logger.info("Job status request", extra={"job_id": job_id})

    try:
        # In a real implementation, this would query a database or cache
        # For now, we'll implement a simple file-based approach
        job_file_path = _get_job_file_path(job_id)

        if not job_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail={"error": f"Job not found: {job_id}"}
            )

        # Load job data
        with open(job_file_path, 'r') as f:
            import json
            job_data = json.load(f)

        logger.debug("Job status retrieved", extra={
            "job_id": job_id,
            "status": job_data.get("status")
        })

        return JSONResponse(content=job_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve job status"}
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str) -> JSONResponse:
    """
    Cancel a transcription job.

    Args:
        job_id: Unique job identifier

    Returns:
        JSON response confirming cancellation

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    logger.info("Job cancellation request", extra={"job_id": job_id})

    try:
        job_file_path = _get_job_file_path(job_id)

        if not job_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail={"error": f"Job not found: {job_id}"}
            )

        # Load current job data
        with open(job_file_path, 'r') as f:
            import json
            job_data = json.load(f)

        current_status = job_data.get("status")

        # Check if job can be cancelled
        if current_status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Cannot cancel job in status: {current_status}"}
            )

        # Update status to cancelled
        from datetime import datetime
        job_data["status"] = ProcessingStatus.CANCELLED
        job_data["completed_at"] = datetime.utcnow().isoformat()

        # Save updated job data
        with open(job_file_path, 'w') as f:
            json.dump(job_data, f, indent=2)

        logger.info("Job cancelled", extra={"job_id": job_id})

        return JSONResponse(content={
            "job_id": job_id,
            "message": "Job cancelled successfully",
            "status": ProcessingStatus.CANCELLED
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel job", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to cancel job"}
        )


@router.get("/jobs/{job_id}/download")
async def download_transcription(job_id: str) -> JSONResponse:
    """
    Download the transcription results.

    Args:
        job_id: Unique job identifier

    Returns:
        File response with transcription results

    Raises:
        HTTPException: If job not found or not completed
    """
    logger.info("Transcription download request", extra={"job_id": job_id})

    try:
        job_file_path = _get_job_file_path(job_id)

        if not job_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail={"error": f"Job not found: {job_id}"}
            )

        # Load job data
        with open(job_file_path, 'r') as f:
            import json
            job_data = json.load(f)

        if job_data.get("status") != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Job not completed. Current status: {job_data.get('status')}"}
            )

        output_file_path = job_data.get("output_file_path")
        if not output_file_path or not Path(output_file_path).exists():
            raise HTTPException(
                status_code=404,
                detail={"error": "Transcription file not found"}
            )

        # Return file download URL or direct file response
        return JSONResponse(content={
            "job_id": job_id,
            "download_url": f"/v1/files/{job_id}/transcription.json",
            "file_size": Path(output_file_path).stat().st_size,
            "format": "json"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to prepare download", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to prepare transcription download"}
        )


async def _save_uploaded_file(file: UploadFile, job_id: str) -> Path:
    """
    Save uploaded file to upload directory.

    Args:
        file: Uploaded file
        job_id: Job identifier for unique naming

    Returns:
        Path to saved file

    Raises:
        RuntimeError: If file save fails
    """
    try:
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        upload_filename = f"{job_id}{file_extension}"
        upload_path = upload_dir / upload_filename

        # Save file
        async with aiofiles.open(upload_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                await f.write(chunk)

        logger.debug("File saved successfully", extra={
            "job_id": job_id,
            "upload_path": str(upload_path),
            "file_size": upload_path.stat().st_size
        })

        return upload_path

    except Exception as e:
        logger.error("Failed to save uploaded file", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)
        raise RuntimeError(f"Failed to save uploaded file: {str(e)}")


def _get_job_file_path(job_id: str) -> Path:
    """Get the file path for storing job data."""
    jobs_dir = Path(settings.OUTPUT_DIR) / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir / f"{job_id}.json"


def _is_valid_language_code(language: str) -> bool:
    """
    Validate language code.

    Args:
        language: Language code to validate

    Returns:
        bool: True if valid language code
    """
    # Common language codes supported by WhisperX
    valid_languages = {
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
        'ar', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi', 'he', 'hi',
        'th', 'vi', 'uk', 'cs', 'hu', 'ro', 'bg', 'hr', 'sk', 'sl'
    }
    return language.lower() in valid_languages