"""
Persistent job storage service for transcription jobs.
Stores job metadata and results in JSON files for persistence across server restarts.
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import aiofiles
from src.core.logging import get_logger
from src.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class JobStorage:
    """Persistent job storage using JSON files."""

    def __init__(self, storage_dir: str = "job_storage"):
        """Initialize job storage."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

        # In-memory cache for fast access
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False

        logger.info(f"Job storage initialized at {self.storage_dir}")

    async def _ensure_cache_loaded(self) -> None:
        """Load all jobs into cache if not already loaded."""
        if self._cache_loaded:
            return

        async with self._lock:
            if self._cache_loaded:
                return

            # Load all job files
            for job_file in self.storage_dir.glob("*.json"):
                try:
                    async with aiofiles.open(job_file, 'r') as f:
                        content = await f.read()
                        job_data = json.loads(content)
                        job_id = job_data.get("job_id")
                        if job_id:
                            self._cache[job_id] = job_data
                except Exception as e:
                    logger.error(f"Failed to load job file {job_file}: {e}")

            self._cache_loaded = True
            logger.info(f"Loaded {len(self._cache)} jobs into cache")

    def _get_job_file_path(self, job_id: str) -> Path:
        """Get the file path for a job."""
        return self.storage_dir / f"{job_id}.json"

    async def create_job(self, job_data: Dict[str, Any]) -> None:
        """
        Create a new job entry.

        Args:
            job_data: Job metadata dictionary
        """
        await self._ensure_cache_loaded()

        job_id = job_data.get("job_id")
        if not job_id:
            raise ValueError("job_data must contain 'job_id'")

        # Add timestamps
        job_data["created_at"] = datetime.utcnow().isoformat()
        job_data["updated_at"] = datetime.utcnow().isoformat()

        async with self._lock:
            # Update cache
            self._cache[job_id] = job_data

            # Write to file
            job_file = self._get_job_file_path(job_id)
            async with aiofiles.open(job_file, 'w') as f:
                await f.write(json.dumps(job_data, indent=2))

        logger.info(f"Created job {job_id}")

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job data by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data dictionary or None if not found
        """
        await self._ensure_cache_loaded()
        return self._cache.get(job_id)

    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """
        Update job data.

        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update
        """
        await self._ensure_cache_loaded()

        async with self._lock:
            if job_id not in self._cache:
                logger.warning(f"Attempted to update non-existent job {job_id}")
                return

            # Update cache
            self._cache[job_id].update(updates)
            self._cache[job_id]["updated_at"] = datetime.utcnow().isoformat()

            # Write to file
            job_file = self._get_job_file_path(job_id)
            async with aiofiles.open(job_file, 'w') as f:
                await f.write(json.dumps(self._cache[job_id], indent=2))

        logger.debug(f"Updated job {job_id}")

    async def update_progress(self, job_id: str, progress: float, message: str = None) -> None:
        """
        Update job progress.

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        updates = {"progress": progress}
        if message:
            updates["progress_message"] = message

        await self.update_job(job_id, updates)

    async def delete_job(self, job_id: str) -> None:
        """
        Delete a job.

        Args:
            job_id: Job identifier
        """
        await self._ensure_cache_loaded()

        async with self._lock:
            # Remove from cache
            if job_id in self._cache:
                del self._cache[job_id]

            # Delete file
            job_file = self._get_job_file_path(job_id)
            if job_file.exists():
                job_file.unlink()

        logger.info(f"Deleted job {job_id}")

    async def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of job data dictionaries
        """
        await self._ensure_cache_loaded()

        jobs = list(self._cache.values())

        if status:
            jobs = [j for j in jobs if j.get("status") == status]

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jobs

    async def cleanup_old_jobs(self, retention_hours: int = 48) -> int:
        """
        Clean up jobs older than retention period.

        Args:
            retention_hours: Hours to retain completed/failed jobs

        Returns:
            Number of jobs deleted
        """
        await self._ensure_cache_loaded()

        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        deleted_count = 0

        jobs_to_delete = []
        for job_id, job_data in self._cache.items():
            status = job_data.get("status")
            created_at = job_data.get("created_at")

            # Only delete completed/failed jobs
            if status not in ["completed", "failed"]:
                continue

            # Check age
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if created_time < cutoff_time:
                    jobs_to_delete.append(job_id)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid created_at timestamp for job {job_id}")

        # Delete old jobs
        for job_id in jobs_to_delete:
            await self.delete_job(job_id)
            deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old jobs")

        return deleted_count


# Global job storage instance
_job_storage: Optional[JobStorage] = None


def get_job_storage() -> JobStorage:
    """Get the global job storage instance."""
    global _job_storage
    if _job_storage is None:
        _job_storage = JobStorage()
    return _job_storage
