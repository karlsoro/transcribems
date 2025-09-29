"""Progress tracking MCP tool.

This tool provides real-time progress information for transcription jobs.
"""

import logging
from typing import Dict, Any, Optional

from ..services.progress_service import ProgressService
from ..services.storage_service import StorageService
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize services
progress_service = ProgressService()
storage_service = StorageService()
error_handler = MCPErrorHandler()

async def get_transcription_progress_tool(request: dict) -> dict:
    """MCP tool for getting transcription progress.

    Args:
        request: MCP request containing:
            - job_id: Job ID to get progress for (optional)
            - all_jobs: If True, return all active jobs (optional)

    Returns:
        dict: Progress information
    """
    try:
        job_id = request.get('job_id')
        all_jobs = request.get('all_jobs', False)

        if all_jobs:
            # Return all active jobs
            active_jobs = progress_service.get_all_active_jobs()
            processing_stats = progress_service.get_processing_stats()

            return {
                "success": True,
                "active_jobs": active_jobs,
                "stats": processing_stats
            }

        elif job_id:
            # Return specific job progress
            progress_info = progress_service.get_job_progress(job_id)

            if "error" in progress_info:
                return error_handler.job_not_found(f"Job {job_id} not found in progress tracking")

            # Also try to get job from storage if not in progress service
            job = await storage_service.load_job(job_id)
            if job:
                job_dict = job.to_status_dict()
                progress_info.update({
                    "file_name": job.audio_file.file_name,
                    "file_path": job.audio_file.file_path,
                    "settings": job.settings.dict()
                })

            return {
                "success": True,
                "job": progress_info
            }

        else:
            return error_handler.invalid_parameters("Either job_id or all_jobs=true must be specified")

    except Exception as e:
        logger.error(f"Progress tool error: {e}")
        return error_handler.internal_error(f"Progress retrieval failed: {str(e)}")

get_transcription_progress_tool.__name__ = 'get_transcription_progress_tool'