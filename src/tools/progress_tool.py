"""Progress tracking MCP tool for GPU-enhanced transcription.

This tool provides real-time progress information for GPU-accelerated transcription jobs
with performance metrics and system status.
"""

import logging
from typing import Dict, Any, Optional

from ..services.mcp_transcription_adapter import MCPTranscriptionAdapter
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize GPU-enhanced services
transcription_adapter = MCPTranscriptionAdapter()
error_handler = MCPErrorHandler()

async def get_transcription_progress_tool(request: dict) -> dict:
    """MCP tool for getting GPU-enhanced transcription progress.

    Args:
        request: MCP request containing:
            - job_id: Job ID to get progress for (optional)
            - all_jobs: If True, return all active jobs (optional)

    Returns:
        dict: Progress information with GPU performance metrics
    """
    try:
        job_id = request.get('job_id')
        all_jobs = request.get('all_jobs', False)

        if all_jobs:
            # Return all jobs and system info
            jobs_info = transcription_adapter.list_jobs()
            system_info = transcription_adapter.get_system_info()

            return {
                "success": True,
                "jobs": jobs_info["jobs"],
                "total_count": jobs_info["total_count"],
                "system_info": system_info
            }

        elif job_id:
            # Return specific job progress
            progress_info = transcription_adapter.get_job_progress(job_id)

            if progress_info.get("status") == "not_found":
                return error_handler.job_not_found(f"Job {job_id} not found in progress tracking")

            return {
                "success": True,
                "job_id": job_id,
                "progress": progress_info
            }

        else:
            return error_handler.invalid_parameters("Either job_id or all_jobs=true must be specified")

    except Exception as e:
        logger.error(f"Progress tool error: {e}")
        return error_handler.internal_error(f"Progress retrieval failed: {str(e)}")

get_transcription_progress_tool.__name__ = 'get_transcription_progress_tool'