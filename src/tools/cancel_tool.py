"""Cancellation MCP tool.

This tool allows cancelling in-progress transcription jobs.
"""

import logging
from typing import Dict, Any

from ..services.progress_service import ProgressService
from ..services.transcription_service import TranscriptionService
from ..services.storage_service import StorageService
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize services
progress_service = ProgressService()
transcription_service = TranscriptionService()
storage_service = StorageService()
error_handler = MCPErrorHandler()

async def cancel_transcription_tool(request: dict) -> dict:
    """MCP tool for cancelling transcription jobs.

    Args:
        request: MCP request containing:
            - job_id: Job ID to cancel
            - reason: Cancellation reason (optional)

    Returns:
        dict: Cancellation result
    """
    try:
        job_id = request.get('job_id')
        if not job_id:
            return error_handler.invalid_parameters("job_id parameter is required")

        reason = request.get('reason', "Cancelled by user")

        # Try to cancel in progress service first
        success = progress_service.cancel_job(job_id)

        if not success:
            # Job might not be in progress service, try to load from storage
            job = await storage_service.load_job(job_id)
            if not job:
                return error_handler.job_not_found(f"Job {job_id} not found")

            # Check if job can be cancelled
            if not job.is_active():
                return {
                    "success": False,
                    "error": {
                        "code": "CANNOT_CANCEL",
                        "message": f"Job {job_id} cannot be cancelled (status: {job.status.value})",
                        "current_status": job.status.value
                    }
                }

            # Try to cancel via transcription service
            success = await transcription_service.cancel_transcription(job)

        if success:
            # Load job to get updated status
            job = await storage_service.load_job(job_id)
            if job:
                # Update storage with cancelled status
                job.error_message = reason
                await storage_service.save_job(job)
                await storage_service.update_history(job)

            return {
                "success": True,
                "message": f"Job {job_id} has been cancelled",
                "job_id": job_id,
                "reason": reason
            }
        else:
            return {
                "success": False,
                "error": {
                    "code": "CANCELLATION_FAILED",
                    "message": f"Failed to cancel job {job_id}. It may have already completed or failed."
                }
            }

    except Exception as e:
        logger.error(f"Cancel tool error: {e}")
        return error_handler.internal_error(f"Cancellation failed: {str(e)}")

cancel_transcription_tool.__name__ = 'cancel_transcription_tool'