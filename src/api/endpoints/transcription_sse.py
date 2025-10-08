"""
Server-Sent Events (SSE) endpoint for real-time transcription progress updates.
Based on proven working implementation from test_sse.py
"""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.services.job_storage import get_job_storage
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["transcription"])


async def event_generator(job_id: str) -> AsyncGenerator[bytes, None]:
    """
    Generate Server-Sent Events for job progress.

    CRITICAL: Must yield bytes, not strings, for proper streaming.
    """
    job_storage = get_job_storage()
    last_progress = -1
    last_status = None

    logger.info(f"SSE stream started for job {job_id}")

    try:
        iteration = 0
        while True:
            iteration += 1

            try:
                job = await job_storage.get_job(job_id)
            except Exception as e:
                logger.error(f"SSE: Failed to get job {job_id}: {e}", exc_info=True)
                error_data = json.dumps({"error": f"Failed to get job: {str(e)}"})
                yield f"event: error\ndata: {error_data}\n\n".encode('utf-8')
                break

            if not job:
                logger.error(f"SSE: Job {job_id} not found at iteration {iteration}")
                error_data = json.dumps({"error": "Job not found"})
                yield f"event: error\ndata: {error_data}\n\n".encode('utf-8')
                break

            status = job.get("status")
            progress = job.get("progress", 0)
            progress_message = job.get("progress_message", "")

            # Log every 10 iterations for debugging
            if iteration % 10 == 0:
                logger.debug(f"SSE iteration {iteration} for {job_id}: status={status}, progress={progress}%")

            # Send on first iteration OR when values change
            should_send = (iteration == 1) or (progress != last_progress) or (status != last_status)

            if should_send:
                data = json.dumps({
                    "job_id": job_id,
                    "status": status,
                    "progress": progress,
                    "message": progress_message
                })

                logger.info(f"SSE: Sending progress for {job_id}: {progress}% - {status} - {progress_message}")

                try:
                    yield f"event: progress\ndata: {data}\n\n".encode('utf-8')
                except (ConnectionResetError, BrokenPipeError) as e:
                    logger.warning(f"SSE: Client disconnected for job {job_id}: {e}")
                    break

                last_progress = progress
                last_status = status

            # Terminal states
            if status in ["completed", "failed"]:
                try:
                    if status == "completed":
                        result_data = json.dumps({
                            "job_id": job_id,
                            "status": status,
                            "progress": 100,
                            "message": "Transcription completed",
                            "result": job.get("result"),
                            "output_file": job.get("output_file"),
                            "segments_count": job.get("segments_count"),
                            "speakers_count": job.get("speakers_count")
                        })
                        yield f"event: completed\ndata: {result_data}\n\n".encode('utf-8')
                    else:
                        error_data = json.dumps({
                            "job_id": job_id,
                            "status": status,
                            "error": job.get("error"),
                            "error_type": job.get("error_type")
                        })
                        yield f"event: failed\ndata: {error_data}\n\n".encode('utf-8')
                except (ConnectionResetError, BrokenPipeError) as e:
                    logger.warning(f"SSE: Client disconnected before receiving final status for job {job_id}: {e}")

                logger.info(f"SSE stream ended for job {job_id} with status: {status}")
                break

            # Send heartbeat every 10 iterations (5 seconds) to keep connection alive
            if iteration % 10 == 0:
                try:
                    yield ": heartbeat\n\n".encode('utf-8')
                except (ConnectionResetError, BrokenPipeError) as e:
                    logger.warning(f"SSE: Client disconnected during heartbeat for job {job_id}: {e}")
                    break

            # Poll every 500ms
            await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled for job {job_id}")
        raise
    except Exception as e:
        logger.error(f"SSE stream error for job {job_id}: {e}", exc_info=True)
        error_msg = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_msg}\n\n".encode('utf-8')


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Stream job progress updates via Server-Sent Events.
    """
    job_storage = get_job_storage()
    job = await job_storage.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return StreamingResponse(
        event_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
