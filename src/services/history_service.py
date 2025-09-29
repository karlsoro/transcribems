"""HistoryService for transcription history management.

This service provides high-level operations for managing transcription
history, including filtering, searching, and statistics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .storage_service import StorageService
from ..models.transcription_job import TranscriptionJob
from ..models.types import JobStatus

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing transcription history."""

    def __init__(self, storage_service: StorageService):
        """Initialize the history service.

        Args:
            storage_service: StorageService instance for persistence
        """
        self.storage = storage_service

    async def get_history(
        self,
        limit: int = 10,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get transcription history with filtering options.

        Args:
            limit: Maximum number of entries to return
            status_filter: Optional status filter
            date_from: Optional start date filter
            date_to: Optional end date filter

        Returns:
            Dict[str, Any]: Filtered history data
        """
        try:
            # Get base history from storage
            history = await self.storage.get_history(limit=1000, status_filter=None)
            jobs = history.get("jobs", [])

            # Apply additional filters
            filtered_jobs = self._apply_filters(jobs, status_filter, date_from, date_to)

            # Sort by start time (most recent first)
            filtered_jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)

            # Apply limit
            result_jobs = filtered_jobs[:limit]

            # Enhance job data
            enhanced_jobs = []
            for job in result_jobs:
                enhanced_job = await self._enhance_job_data(job)
                enhanced_jobs.append(enhanced_job)

            return {
                "jobs": enhanced_jobs,
                "total_count": history.get("total_count", 0),
                "filtered_count": len(filtered_jobs),
                "returned_count": len(enhanced_jobs)
            }

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {
                "jobs": [],
                "total_count": 0,
                "filtered_count": 0,
                "returned_count": 0
            }

    async def get_job_summary(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get summary information for a specific job.

        Args:
            job_id: Job ID to get summary for

        Returns:
            Optional[Dict[str, Any]]: Job summary or None if not found
        """
        try:
            # Load job from storage
            job = await self.storage.load_job(job_id)
            if not job:
                return None

            # Load result if available
            result = await self.storage.load_result(job_id)

            summary = {
                "job_id": job.job_id,
                "file_name": job.audio_file.file_name,
                "file_path": job.audio_file.file_path,
                "file_size": job.audio_file.file_size,
                "duration": job.audio_file.duration,
                "status": job.status.value,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "processing_time": job.get_processing_duration(),
                "progress": job.progress,
                "settings": {
                    "model_size": job.settings.model_size,
                    "language": job.settings.language,
                    "enable_diarization": job.settings.enable_diarization
                }
            }

            # Add result information if available
            if result:
                summary.update({
                    "word_count": result.word_count,
                    "confidence_score": result.confidence_score,
                    "speaker_count": len(result.speakers),
                    "segment_count": len(result.segments)
                })

            # Add error information if failed
            if job.status == JobStatus.FAILED and job.error_message:
                summary["error_message"] = job.error_message

            return summary

        except Exception as e:
            logger.error(f"Failed to get job summary for {job_id}: {e}")
            return None

    async def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get transcription statistics for the last N days.

        Args:
            days: Number of days to include in statistics

        Returns:
            Dict[str, Any]: Statistics data
        """
        try:
            # Get recent history
            date_from = datetime.utcnow() - timedelta(days=days)
            history = await self.get_history(
                limit=1000,
                date_from=date_from
            )

            jobs = history.get("jobs", [])

            # Calculate statistics
            stats = {
                "period_days": days,
                "total_jobs": len(jobs),
                "completed_jobs": 0,
                "failed_jobs": 0,
                "processing_jobs": 0,
                "total_duration": 0.0,
                "total_processing_time": 0.0,
                "average_confidence": 0.0,
                "total_words": 0,
                "model_usage": {},
                "language_usage": {},
                "format_usage": {},
                "daily_counts": {}
            }

            confidence_scores = []

            for job in jobs:
                # Status counts
                status = job.get("status", "unknown")
                if status == "completed":
                    stats["completed_jobs"] += 1
                elif status == "failed":
                    stats["failed_jobs"] += 1
                elif status == "processing":
                    stats["processing_jobs"] += 1

                # Duration and processing time
                if job.get("duration"):
                    stats["total_duration"] += job["duration"]

                if job.get("processing_time"):
                    stats["total_processing_time"] += job["processing_time"]

                # Model usage
                model = job.get("model_size", "unknown")
                stats["model_usage"][model] = stats["model_usage"].get(model, 0) + 1

                # Language usage
                language = job.get("language") or "auto"
                stats["language_usage"][language] = stats["language_usage"].get(language, 0) + 1

                # Add additional stats from results if available
                if status == "completed":
                    result = await self.storage.load_result(job["job_id"])
                    if result:
                        if result.confidence_score:
                            confidence_scores.append(result.confidence_score)
                        if result.word_count:
                            stats["total_words"] += result.word_count

                # Daily counts
                started_date = job.get("started_at")
                if started_date:
                    try:
                        date_key = started_date[:10]  # YYYY-MM-DD
                        stats["daily_counts"][date_key] = stats["daily_counts"].get(date_key, 0) + 1
                    except (TypeError, IndexError):
                        pass

            # Calculate averages
            if confidence_scores:
                stats["average_confidence"] = sum(confidence_scores) / len(confidence_scores)

            if stats["completed_jobs"] > 0:
                stats["average_processing_time"] = stats["total_processing_time"] / stats["completed_jobs"]
                stats["average_duration"] = stats["total_duration"] / stats["completed_jobs"]

            # Success rate
            if stats["total_jobs"] > 0:
                stats["success_rate"] = stats["completed_jobs"] / stats["total_jobs"]

            return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    async def search_history(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search transcription history by filename or content.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            Dict[str, Any]: Search results
        """
        try:
            # Get all history (we'll filter in memory for simplicity)
            history = await self.storage.get_history(limit=1000)
            jobs = history.get("jobs", [])

            # Simple search implementation
            query_lower = query.lower()
            matching_jobs = []

            for job in jobs:
                # Search in filename
                file_name = job.get("file_name", "").lower()
                if query_lower in file_name:
                    job["match_type"] = "filename"
                    matching_jobs.append(job)
                    continue

                # Could extend to search in transcription text
                # This would require loading results, which is more expensive

            # Sort by relevance (exact matches first)
            matching_jobs.sort(key=lambda x: x.get("file_name", "").lower().startswith(query_lower), reverse=True)

            return {
                "query": query,
                "jobs": matching_jobs[:limit],
                "total_matches": len(matching_jobs)
            }

        except Exception as e:
            logger.error(f"Failed to search history: {e}")
            return {"query": query, "jobs": [], "total_matches": 0}

    def _apply_filters(
        self,
        jobs: List[Dict[str, Any]],
        status_filter: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Apply filters to job list.

        Args:
            jobs: List of jobs to filter
            status_filter: Status filter
            date_from: Start date filter
            date_to: End date filter

        Returns:
            List[Dict[str, Any]]: Filtered jobs
        """
        filtered = jobs

        # Status filter
        if status_filter:
            filtered = [job for job in filtered if job.get("status") == status_filter]

        # Date filters
        if date_from or date_to:
            date_filtered = []
            for job in filtered:
                job_date_str = job.get("started_at")
                if not job_date_str:
                    continue

                try:
                    job_date = datetime.fromisoformat(job_date_str.replace('Z', '+00:00'))

                    if date_from and job_date < date_from:
                        continue
                    if date_to and job_date > date_to:
                        continue

                    date_filtered.append(job)
                except (ValueError, TypeError):
                    continue

            filtered = date_filtered

        return filtered

    async def _enhance_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance job data with additional computed fields.

        Args:
            job: Base job data

        Returns:
            Dict[str, Any]: Enhanced job data
        """
        enhanced = job.copy()

        # Add relative time
        started_at = job.get("started_at")
        if started_at:
            try:
                started_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                time_ago = datetime.utcnow() - started_time.replace(tzinfo=None)
                enhanced["time_ago"] = self._format_time_ago(time_ago)
            except (ValueError, TypeError):
                pass

        # Add duration formatted
        duration = job.get("duration")
        if duration:
            enhanced["duration_formatted"] = self._format_duration(duration)

        # Add processing time formatted
        processing_time = job.get("processing_time")
        if processing_time:
            enhanced["processing_time_formatted"] = self._format_duration(processing_time)

        return enhanced

    def _format_time_ago(self, delta: timedelta) -> str:
        """Format time delta as human readable string.

        Args:
            delta: Time delta

        Returns:
            str: Formatted string
        """
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds as human readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            str: Formatted duration
        """
        if seconds >= 3600:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        elif seconds >= 60:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            return f"{int(seconds)}s"