"""ProgressService for job progress tracking.

This service manages progress tracking for transcription jobs,
including real-time updates and estimation calculations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from ..models.transcription_job import TranscriptionJob
from ..models.types import JobStatus

logger = logging.getLogger(__name__)


class ProgressService:
    """Service for tracking transcription job progress."""

    def __init__(self):
        """Initialize the progress service."""
        self.active_jobs: Dict[str, TranscriptionJob] = {}
        self.progress_callbacks: Dict[str, Callable[[TranscriptionJob], None]] = {}

    def register_job(self, job: TranscriptionJob) -> None:
        """Register a job for progress tracking.

        Args:
            job: TranscriptionJob to track
        """
        self.active_jobs[job.job_id] = job
        logger.debug(f"Registered job for progress tracking: {job.job_id}")

    def unregister_job(self, job_id: str) -> None:
        """Unregister a job from progress tracking.

        Args:
            job_id: Job ID to stop tracking
        """
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
        if job_id in self.progress_callbacks:
            del self.progress_callbacks[job_id]
        logger.debug(f"Unregistered job from progress tracking: {job_id}")

    def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """Get current progress for a job.

        Args:
            job_id: Job ID to get progress for

        Returns:
            Dict[str, Any]: Progress information
        """
        if job_id not in self.active_jobs:
            return {
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": "Job not found in progress tracking"
                }
            }

        job = self.active_jobs[job_id]
        return job.to_status_dict()

    def update_job_progress(self, job_id: str, current_chunk: int, total_chunks: Optional[int] = None) -> None:
        """Update progress for a job.

        Args:
            job_id: Job ID to update
            current_chunk: Current chunk being processed
            total_chunks: Total chunks (if different from stored)
        """
        if job_id not in self.active_jobs:
            logger.warning(f"Attempted to update progress for unknown job: {job_id}")
            return

        job = self.active_jobs[job_id]
        try:
            job.update_progress(current_chunk, total_chunks)

            # Call progress callback if registered
            if job_id in self.progress_callbacks:
                self.progress_callbacks[job_id](job)

            logger.debug(f"Updated progress for job {job_id}: {job.progress:.2f}")

        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {e}")

    def register_progress_callback(self, job_id: str, callback: Callable[[TranscriptionJob], None]) -> None:
        """Register a callback for progress updates.

        Args:
            job_id: Job ID to register callback for
            callback: Function to call on progress updates
        """
        self.progress_callbacks[job_id] = callback
        logger.debug(f"Registered progress callback for job: {job_id}")

    def complete_job(self, job_id: str) -> None:
        """Mark a job as completed.

        Args:
            job_id: Job ID to complete
        """
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            try:
                job.complete_successfully()

                # Final progress callback
                if job_id in self.progress_callbacks:
                    self.progress_callbacks[job_id](job)

                logger.info(f"Job completed: {job_id}")

            except Exception as e:
                logger.error(f"Failed to complete job {job_id}: {e}")

    def fail_job(self, job_id: str, error_message: str) -> None:
        """Mark a job as failed.

        Args:
            job_id: Job ID to fail
            error_message: Error message
        """
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            try:
                job.fail_with_error(error_message)

                # Final progress callback
                if job_id in self.progress_callbacks:
                    self.progress_callbacks[job_id](job)

                logger.info(f"Job failed: {job_id} - {error_message}")

            except Exception as e:
                logger.error(f"Failed to fail job {job_id}: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job if it's still processing.

        Args:
            job_id: Job ID to cancel

        Returns:
            bool: True if successfully cancelled
        """
        if job_id not in self.active_jobs:
            return False

        job = self.active_jobs[job_id]
        success = job.cancel()

        if success:
            # Final progress callback
            if job_id in self.progress_callbacks:
                self.progress_callbacks[job_id](job)

            logger.info(f"Job cancelled: {job_id}")

        return success

    def get_all_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get progress for all active jobs.

        Returns:
            Dict[str, Dict[str, Any]]: Progress info for all jobs
        """
        return {
            job_id: job.to_status_dict()
            for job_id, job in self.active_jobs.items()
        }

    def get_jobs_by_status(self, status: JobStatus) -> Dict[str, TranscriptionJob]:
        """Get all jobs with a specific status.

        Args:
            status: JobStatus to filter by

        Returns:
            Dict[str, TranscriptionJob]: Jobs with the specified status
        """
        return {
            job_id: job
            for job_id, job in self.active_jobs.items()
            if job.status == status
        }

    def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed jobs from memory.

        Args:
            max_age_hours: Maximum age in hours for completed jobs

        Returns:
            int: Number of jobs cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        jobs_to_remove = []

        for job_id, job in self.active_jobs.items():
            if (job.is_terminal_state() and
                job.completed_at and
                job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            self.unregister_job(job_id)

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs from progress tracking")

        return len(jobs_to_remove)

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about currently processing jobs.

        Returns:
            Dict[str, Any]: Processing statistics
        """
        active_count = len([j for j in self.active_jobs.values() if j.is_active()])
        pending_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.PENDING])
        completed_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.COMPLETED])
        failed_count = len([j for j in self.active_jobs.values() if j.status == JobStatus.FAILED])

        return {
            "total_jobs": len(self.active_jobs),
            "active_jobs": active_count,
            "pending_jobs": pending_count,
            "completed_jobs": completed_count,
            "failed_jobs": failed_count,
            "average_progress": sum(j.progress for j in self.active_jobs.values() if j.is_active()) / max(active_count, 1)
        }