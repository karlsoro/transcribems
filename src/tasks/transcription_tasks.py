"""
Background tasks for audio transcription processing using Celery.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from celery import Celery
from celery.utils.log import get_task_logger

from src.core.config import get_settings
from src.models.transcription import Transcription, ProcessingStatus, TranscriptionMetadata
from src.models.audio_file import AudioFile
from src.services.whisperx_service import WhisperXService
from src.core.logging import setup_logging


# Initialize settings and logging
settings = get_settings()
setup_logging(
    log_dir=settings.LOG_DIR,
    log_level=settings.LOG_LEVEL
)

# Create Celery app
celery_app = Celery(
    "transcribe_mcp",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(settings.get_celery_config())

# Get Celery logger
logger = get_task_logger(__name__)


@celery_app.task(bind=True, name="transcribe_audio")
def transcribe_audio_task(
    self,
    job_id: str,
    audio_file_path: str,
    language: str = "auto",
    enable_speaker_diarization: bool = True,
    model_size: str = "large-v2"
) -> Dict[str, Any]:
    """
    Background task to transcribe audio file.

    Args:
        self: Celery task instance
        job_id: Unique job identifier
        audio_file_path: Path to audio file
        language: Language code or 'auto'
        enable_speaker_diarization: Enable speaker identification
        model_size: WhisperX model size

    Returns:
        Dict with transcription results
    """
    logger.info("Starting transcription task", extra={
        "job_id": job_id,
        "audio_file": audio_file_path,
        "language": language,
        "speaker_diarization": enable_speaker_diarization,
        "model_size": model_size
    })

    # Create transcription job instance
    transcription = Transcription.create_job(
        job_id=job_id,
        audio_file_path=audio_file_path,
        original_filename=Path(audio_file_path).name
    )

    try:
        # Update job status to processing
        transcription.update_status(ProcessingStatus.PROCESSING)
        _save_job_data(job_id, transcription)

        # Update task progress
        self.update_state(state="PROCESSING", meta={
            "job_id": job_id,
            "stage": "initializing",
            "progress": 0.1
        })

        # Validate audio file
        logger.info("Validating audio file", extra={"job_id": job_id})
        audio_file = AudioFile.from_upload(audio_file_path, Path(audio_file_path).name)

        if not audio_file.is_valid_for_transcription():
            raise ValueError("Audio file is not valid for transcription")

        # Initialize WhisperX service
        logger.info("Initializing WhisperX service", extra={
            "job_id": job_id,
            "model_size": model_size
        })

        whisperx_service = WhisperXService(
            model_size=model_size,
            device=settings.DEVICE,
            hf_token=settings.HF_TOKEN
        )

        # Update progress
        self.update_state(state="PROCESSING", meta={
            "job_id": job_id,
            "stage": "loading_models",
            "progress": 0.2
        })

        # Run transcription
        logger.info("Starting audio transcription", extra={"job_id": job_id})
        start_time = time.time()

        # Use asyncio to run the async transcription
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            transcription_result = loop.run_until_complete(
                whisperx_service.transcribe_audio(
                    audio_path=audio_file_path,
                    language=language,
                    enable_speaker_diarization=enable_speaker_diarization
                )
            )
        finally:
            loop.close()

        processing_time = time.time() - start_time

        # Update progress
        self.update_state(state="PROCESSING", meta={
            "job_id": job_id,
            "stage": "processing_results",
            "progress": 0.8
        })

        # Process transcription results
        logger.info("Processing transcription results", extra={
            "job_id": job_id,
            "segments_count": len(transcription_result["segments"]),
            "speakers_count": len(transcription_result["speakers"]),
            "processing_time": processing_time
        })

        # Convert results to our models
        transcription = _convert_results_to_transcription(
            transcription, transcription_result, processing_time
        )

        # Generate output files
        output_dir = Path(settings.OUTPUT_DIR) / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON transcription
        json_path = output_dir / f"{job_id}_transcription.json"
        transcription.to_json_file(str(json_path))

        # Save subtitle file
        subtitle_path = output_dir / f"{job_id}_subtitles.srt"
        transcription.to_subtitle_file(str(subtitle_path))

        # Update progress
        self.update_state(state="PROCESSING", meta={
            "job_id": job_id,
            "stage": "finalizing",
            "progress": 0.95
        })

        # Update final status
        transcription.update_status(ProcessingStatus.COMPLETED)
        _save_job_data(job_id, transcription)

        # Cleanup WhisperX service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(whisperx_service.cleanup())
        finally:
            loop.close()

        logger.info("Transcription completed successfully", extra={
            "job_id": job_id,
            "processing_time": processing_time,
            "output_files": [str(json_path), str(subtitle_path)]
        })

        # Final progress update
        self.update_state(state="SUCCESS", meta={
            "job_id": job_id,
            "stage": "completed",
            "progress": 1.0,
            "result": {
                "segments_count": len(transcription.segments),
                "speakers_count": len(transcription.speakers),
                "processing_time": processing_time,
                "output_file": str(json_path),
                "subtitle_file": str(subtitle_path)
            }
        })

        return {
            "job_id": job_id,
            "status": "completed",
            "segments_count": len(transcription.segments),
            "speakers_count": len(transcription.speakers),
            "processing_time": processing_time,
            "output_file": str(json_path)
        }

    except Exception as e:
        logger.error("Transcription task failed", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)

        # Update job status to failed
        transcription.update_status(ProcessingStatus.FAILED, error_message=str(e))
        transcription.error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "stage": getattr(self, 'current_stage', 'unknown')
        }
        _save_job_data(job_id, transcription)

        # Update task state
        self.update_state(state="FAILURE", meta={
            "job_id": job_id,
            "error": str(e),
            "error_type": type(e).__name__
        })

        # Re-raise the exception for Celery
        raise


def _convert_results_to_transcription(
    transcription: Transcription,
    results: Dict[str, Any],
    processing_time: float
) -> Transcription:
    """
    Convert WhisperX results to Transcription model.

    Args:
        transcription: Base transcription instance
        results: Results from WhisperX service
        processing_time: Processing time in seconds

    Returns:
        Updated Transcription instance
    """
    from src.models.transcription import SpeechSegment, Speaker

    # Convert segments
    segments = []
    for segment_data in results["segments"]:
        segment = SpeechSegment(
            start_time=segment_data["start"],
            end_time=segment_data["end"],
            text=segment_data["text"],
            speaker=segment_data.get("speaker"),
            confidence=segment_data.get("confidence"),
            language=results.get("language")
        )
        segments.append(segment)

    transcription.segments = segments

    # Convert speakers
    speakers = []
    speaker_stats = transcription.get_speaker_statistics()

    for speaker_id in results["speakers"]:
        speaker_info = speaker_stats.get(speaker_id, {})
        speaker = Speaker(
            speaker_id=speaker_id,
            segments_count=speaker_info.get("segments_count", 0),
            total_speaking_time=speaker_info.get("total_time", 0.0)
        )
        speakers.append(speaker)

    transcription.speakers = speakers

    # Generate full text
    transcription.generate_full_text(include_speakers=True, include_timestamps=False)

    # Create metadata
    metadata = TranscriptionMetadata(
        model_name=results["model_name"],
        language=results["language"],
        language_probability=results.get("language_probability"),
        processing_time_seconds=processing_time,
        gpu_used=results["gpu_used"],
        device_name=results["device"],
        speaker_diarization_enabled=len(results["speakers"]) > 0,
        realtime_factor=results.get("realtime_factor")
    )

    transcription.metadata = metadata

    return transcription


def _save_job_data(job_id: str, transcription: Transcription) -> None:
    """
    Save job data to file for status tracking.

    Args:
        job_id: Job identifier
        transcription: Transcription instance
    """
    try:
        jobs_dir = Path(settings.OUTPUT_DIR) / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)

        job_file = jobs_dir / f"{job_id}.json"

        # Convert transcription to dict for JSON serialization
        job_data = transcription.dict()

        # Add additional status information
        job_data["last_updated"] = datetime.utcnow().isoformat()

        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2, default=str)

        logger.debug("Job data saved", extra={
            "job_id": job_id,
            "file_path": str(job_file)
        })

    except Exception as e:
        logger.error("Failed to save job data", extra={
            "job_id": job_id,
            "error": str(e)
        }, exc_info=True)


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files_task() -> Dict[str, Any]:
    """
    Background task to cleanup old files.

    Returns:
        Dict with cleanup results
    """
    logger.info("Starting file cleanup task")

    try:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=settings.RETAIN_UPLOADS_DAYS)
        cleaned_count = 0

        # Cleanup upload files
        upload_dir = Path(settings.UPLOAD_DIR)
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        cleaned_count += 1

        # Cleanup old transcription files if configured
        if settings.CLEANUP_AFTER_PROCESSING:
            output_dir = Path(settings.OUTPUT_DIR)
            if output_dir.exists():
                for job_dir in output_dir.iterdir():
                    if job_dir.is_dir():
                        dir_time = datetime.fromtimestamp(job_dir.stat().st_mtime)
                        if dir_time < cutoff_date:
                            import shutil
                            shutil.rmtree(job_dir)
                            cleaned_count += 1

        logger.info(f"File cleanup completed: {cleaned_count} files/directories removed")

        return {
            "status": "completed",
            "files_cleaned": cleaned_count,
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as e:
        logger.error(f"File cleanup task failed: {e}", exc_info=True)
        raise


# Register periodic cleanup task (runs daily)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
celery_app.conf.timezone = 'UTC'


if __name__ == "__main__":
    # Start Celery worker
    celery_app.start()