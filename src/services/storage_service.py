"""StorageService for file-based persistence.

This service handles JSON-based storage for transcription jobs,
results, and history management.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import aiofiles

from ..models.transcription_job import TranscriptionJob
from ..models.transcription_result import TranscriptionResult
from ..models.types import JobStatus

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file-based JSON persistence."""

    def __init__(self, data_dir: str = "transcribems_data"):
        """Initialize the storage service.

        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = Path(data_dir)
        self.jobs_dir = self.data_dir / "jobs"
        self.results_dir = self.data_dir / "results"
        self.history_file = self.data_dir / "history.json"

        # Create directories
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.data_dir.mkdir(exist_ok=True)
        self.jobs_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)

    async def save_job(self, job: TranscriptionJob) -> None:
        """Save a transcription job to storage.

        Args:
            job: TranscriptionJob to save
        """
        try:
            job_file = self.jobs_dir / f"{job.job_id}.json"
            job_data = job.dict()

            async with aiofiles.open(job_file, 'w') as f:
                await f.write(json.dumps(job_data, indent=2, default=str))

            logger.debug(f"Saved job to storage: {job.job_id}")

        except Exception as e:
            logger.error(f"Failed to save job {job.job_id}: {e}")
            raise

    async def load_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """Load a transcription job from storage.

        Args:
            job_id: Job ID to load

        Returns:
            Optional[TranscriptionJob]: Loaded job or None if not found
        """
        try:
            job_file = self.jobs_dir / f"{job_id}.json"

            if not job_file.exists():
                return None

            async with aiofiles.open(job_file, 'r') as f:
                job_data = json.loads(await f.read())

            # Reconstruct job from data
            job = TranscriptionJob.parse_obj(job_data)
            logger.debug(f"Loaded job from storage: {job_id}")
            return job

        except Exception as e:
            logger.error(f"Failed to load job {job_id}: {e}")
            return None

    async def save_result(self, result: TranscriptionResult) -> None:
        """Save a transcription result to storage.

        Args:
            result: TranscriptionResult to save
        """
        try:
            result_file = self.results_dir / f"{result.job_id}.json"
            result_data = result.dict()

            async with aiofiles.open(result_file, 'w') as f:
                await f.write(json.dumps(result_data, indent=2, default=str))

            logger.debug(f"Saved result to storage: {result.job_id}")

        except Exception as e:
            logger.error(f"Failed to save result {result.job_id}: {e}")
            raise

    async def load_result(self, job_id: str) -> Optional[TranscriptionResult]:
        """Load a transcription result from storage.

        Args:
            job_id: Job ID to load result for

        Returns:
            Optional[TranscriptionResult]: Loaded result or None if not found
        """
        try:
            result_file = self.results_dir / f"{job_id}.json"

            if not result_file.exists():
                return None

            async with aiofiles.open(result_file, 'r') as f:
                result_data = json.loads(await f.read())

            # Reconstruct result from data
            result = TranscriptionResult.parse_obj(result_data)
            logger.debug(f"Loaded result from storage: {job_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to load result {job_id}: {e}")
            return None

    async def update_history(self, job: TranscriptionJob) -> None:
        """Update transcription history with job information.

        Args:
            job: TranscriptionJob to add to history
        """
        try:
            # Load existing history
            history = await self._load_history()

            # Create history entry
            history_entry = {
                "job_id": job.job_id,
                "file_path": job.audio_file.file_path,
                "file_name": job.audio_file.file_name,
                "status": job.status.value,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "duration": job.audio_file.duration,
                "processing_time": job.get_processing_duration(),
                "model_size": job.settings.model_size,
                "language": job.settings.language,
                "error_message": job.error_message
            }

            # Update or add entry
            existing_index = None
            for i, entry in enumerate(history.get("jobs", [])):
                if entry["job_id"] == job.job_id:
                    existing_index = i
                    break

            if existing_index is not None:
                history["jobs"][existing_index] = history_entry
            else:
                if "jobs" not in history:
                    history["jobs"] = []
                history["jobs"].insert(0, history_entry)  # Add to beginning

            # Keep only last 1000 entries
            if len(history["jobs"]) > 1000:
                history["jobs"] = history["jobs"][:1000]

            # Update metadata
            history["total_count"] = len(history["jobs"])
            history["last_updated"] = datetime.utcnow().isoformat()

            # Save updated history
            await self._save_history(history)

        except Exception as e:
            logger.error(f"Failed to update history for job {job.job_id}: {e}")

    async def get_history(self, limit: int = 10, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get transcription history.

        Args:
            limit: Maximum number of entries to return
            status_filter: Optional status filter

        Returns:
            Dict[str, Any]: History data
        """
        try:
            history = await self._load_history()
            jobs = history.get("jobs", [])

            # Apply status filter
            if status_filter:
                jobs = [job for job in jobs if job.get("status") == status_filter]

            # Apply limit
            jobs = jobs[:limit]

            return {
                "jobs": jobs,
                "total_count": len(history.get("jobs", [])),
                "filtered_count": len(jobs)
            }

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {"jobs": [], "total_count": 0, "filtered_count": 0}

    async def _load_history(self) -> Dict[str, Any]:
        """Load history from file.

        Returns:
            Dict[str, Any]: History data
        """
        try:
            if not self.history_file.exists():
                return {"jobs": [], "total_count": 0}

            async with aiofiles.open(self.history_file, 'r') as f:
                return json.loads(await f.read())

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return {"jobs": [], "total_count": 0}

    async def _save_history(self, history: Dict[str, Any]) -> None:
        """Save history to file.

        Args:
            history: History data to save
        """
        async with aiofiles.open(self.history_file, 'w') as f:
            await f.write(json.dumps(history, indent=2, default=str))

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job and its result from storage.

        Args:
            job_id: Job ID to delete

        Returns:
            bool: True if successfully deleted
        """
        try:
            job_file = self.jobs_dir / f"{job_id}.json"
            result_file = self.results_dir / f"{job_id}.json"

            deleted = False
            if job_file.exists():
                job_file.unlink()
                deleted = True

            if result_file.exists():
                result_file.unlink()
                deleted = True

            if deleted:
                logger.info(f"Deleted job from storage: {job_id}")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False

    async def cleanup_old_jobs(self, max_age_days: int = 30) -> int:
        """Clean up old job files.

        Args:
            max_age_days: Maximum age in days for job files

        Returns:
            int: Number of files cleaned up
        """
        try:
            cutoff_time = datetime.utcnow().timestamp() - (max_age_days * 24 * 3600)
            cleanup_count = 0

            # Clean up job files
            for job_file in self.jobs_dir.glob("*.json"):
                if job_file.stat().st_mtime < cutoff_time:
                    job_file.unlink()
                    cleanup_count += 1

            # Clean up result files
            for result_file in self.results_dir.glob("*.json"):
                if result_file.stat().st_mtime < cutoff_time:
                    result_file.unlink()
                    cleanup_count += 1

            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} old files")

            return cleanup_count

        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dict[str, Any]: Storage statistics
        """
        try:
            job_files = list(self.jobs_dir.glob("*.json"))
            result_files = list(self.results_dir.glob("*.json"))

            # Calculate total size
            total_size = sum(f.stat().st_size for f in job_files + result_files)
            if self.history_file.exists():
                total_size += self.history_file.stat().st_size

            return {
                "job_files": len(job_files),
                "result_files": len(result_files),
                "total_size_bytes": total_size,
                "data_directory": str(self.data_dir)
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "job_files": 0,
                "result_files": 0,
                "total_size_bytes": 0,
                "data_directory": str(self.data_dir)
            }