"""
Format job storage service for managing format job state.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from src.core.logging import get_logger
from src.models.template import FormatJob, ValidationIssue

logger = get_logger(__name__)


class FormatJobStorageService:
    """Service for managing format job persistence."""

    def __init__(self, db_path: str = "template_database.db"):
        """Initialize format job storage service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database schema (uses same DB as templates)."""
        async with self._lock:
            if self._initialized:
                return
            self._initialized = True
            logger.info("FormatJobStorageService initialized")

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous database operation in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    @asynccontextmanager
    async def _get_connection(self):
        """Get database connection context manager."""
        conn = await self._run_sync(sqlite3.connect, self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            await self._run_sync(conn.close)

    async def save_job(self, job: FormatJob) -> None:
        """Save or update a format job.

        Args:
            job: FormatJob to save
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            # Serialize complex fields
            preview_data = json.dumps(job.preview_data) if job.preview_data else None
            validation_issues = json.dumps([issue.dict() for issue in job.validation_issues])

            await self._run_sync(
                cursor.execute,
                """
                INSERT OR REPLACE INTO format_jobs
                (id, transcript_id, template_id, status, progress,
                 output_file_path, preview_data, validation_issues,
                 error_message, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.transcript_id,
                    job.template_id,
                    job.status,
                    job.progress,
                    job.output_file_path,
                    preview_data,
                    validation_issues,
                    job.error_message,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )

            await self._run_sync(conn.commit)
            logger.debug(f"Format job saved: {job.id}, status: {job.status}")

    async def get_job(self, job_id: str) -> Optional[FormatJob]:
        """Get format job by ID.

        Args:
            job_id: Job identifier

        Returns:
            FormatJob if found, None otherwise
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            await self._run_sync(
                cursor.execute,
                "SELECT * FROM format_jobs WHERE id = ?",
                (job_id,)
            )

            row = await self._run_sync(cursor.fetchone)

            if not row:
                return None

            return self._row_to_job(row)

    async def list_jobs(
        self,
        transcript_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[FormatJob]:
        """List format jobs with optional filtering.

        Args:
            transcript_id: Filter by transcript ID
            status: Filter by status
            limit: Maximum number of jobs to return

        Returns:
            List of format jobs
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            query = "SELECT * FROM format_jobs WHERE 1=1"
            params = []

            if transcript_id:
                query += " AND transcript_id = ?"
                params.append(transcript_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            await self._run_sync(cursor.execute, query, params)
            rows = await self._run_sync(cursor.fetchall)

            return [self._row_to_job(row) for row in rows]

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: int,
        error_message: Optional[str] = None
    ) -> bool:
        """Update job status and progress.

        Args:
            job_id: Job identifier
            status: New status
            progress: Progress percentage
            error_message: Optional error message

        Returns:
            True if updated, False if not found
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            await self._run_sync(
                cursor.execute,
                """
                UPDATE format_jobs
                SET status = ?, progress = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, progress, error_message, datetime.utcnow().isoformat(), job_id)
            )

            await self._run_sync(conn.commit)
            return cursor.rowcount > 0

    def _row_to_job(self, row: sqlite3.Row) -> FormatJob:
        """Convert database row to FormatJob model.

        Args:
            row: Database row

        Returns:
            FormatJob object
        """
        # Deserialize validation issues
        validation_issues = []
        if row["validation_issues"]:
            issues_data = json.loads(row["validation_issues"])
            validation_issues = [ValidationIssue(**issue) for issue in issues_data]

        # Deserialize preview data
        preview_data = None
        if row["preview_data"]:
            preview_data = json.loads(row["preview_data"])

        return FormatJob(
            id=row["id"],
            transcript_id=row["transcript_id"],
            template_id=row["template_id"],
            status=row["status"],
            progress=row["progress"],
            output_file_path=row["output_file_path"],
            preview_data=preview_data,
            validation_issues=validation_issues,
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


# Global instance
_format_job_storage: Optional[FormatJobStorageService] = None


async def get_format_job_storage() -> FormatJobStorageService:
    """Get global format job storage instance.

    Returns:
        FormatJobStorageService instance
    """
    global _format_job_storage
    if _format_job_storage is None:
        _format_job_storage = FormatJobStorageService()
        await _format_job_storage.initialize()
    return _format_job_storage
