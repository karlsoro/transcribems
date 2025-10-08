"""
Template database service for managing template metadata.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from src.core.logging import get_logger
from src.models.template import Template

logger = get_logger(__name__)


class TemplateDatabaseService:
    """Service for managing template metadata in SQLite database."""

    def __init__(self, db_path: str = "template_database.db"):
        """Initialize template database service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database schema."""
        async with self._lock:
            if self._initialized:
                return

            await self._run_sync(self._initialize_sync)
            self._initialized = True
            logger.info("Template database initialized", extra={"db_path": self.db_path})

    def _initialize_sync(self) -> None:
        """Synchronous database initialization."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Create templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    output_format TEXT NOT NULL,
                    version TEXT NOT NULL,
                    required_fields TEXT,
                    optional_fields TEXT,
                    script_path TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_templates_type ON templates(type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_templates_active ON templates(is_active)"
            )

            # Create format_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS format_jobs (
                    id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    template_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER DEFAULT 0,
                    output_file_path TEXT,
                    preview_data TEXT,
                    validation_issues TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES templates(id)
                )
            """)

            # Create indexes for format_jobs
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_format_jobs_status ON format_jobs(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_format_jobs_transcript ON format_jobs(transcript_id)"
            )

            conn.commit()
            logger.info("Database schema created successfully")

        finally:
            conn.close()

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

    async def add_template(self, template: Template) -> None:
        """Add or update a template.

        Args:
            template: Template to add/update
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            await self._run_sync(
                cursor.execute,
                """
                INSERT OR REPLACE INTO templates
                (id, name, description, type, file_path, output_format, version,
                 required_fields, optional_fields, script_path, is_active,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template.id,
                    template.name,
                    template.description,
                    template.type,
                    template.file_path,
                    template.output_format,
                    template.version,
                    json.dumps(template.required_fields),
                    json.dumps(template.optional_fields),
                    template.script_path,
                    template.is_active,
                    template.created_at.isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )

            await self._run_sync(conn.commit)
            logger.info(f"Template added/updated: {template.id}")

    async def get_template(self, template_id: str) -> Optional[Template]:
        """Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template if found, None otherwise
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            await self._run_sync(
                cursor.execute,
                "SELECT * FROM templates WHERE id = ?",
                (template_id,)
            )

            row = await self._run_sync(cursor.fetchone)

            if not row:
                return None

            return self._row_to_template(row)

    async def list_templates(
        self,
        type: Optional[str] = None,
        active_only: bool = True
    ) -> List[Template]:
        """List templates with optional filtering.

        Args:
            type: Filter by template type
            active_only: Only return active templates

        Returns:
            List of templates
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            query = "SELECT * FROM templates WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = ?"
                params.append(True)

            if type:
                query += " AND type = ?"
                params.append(type)

            query += " ORDER BY name"

            await self._run_sync(cursor.execute, query, params)
            rows = await self._run_sync(cursor.fetchall)

            return [self._row_to_template(row) for row in rows]

    async def delete_template(self, template_id: str) -> bool:
        """Delete (deactivate) a template.

        Args:
            template_id: Template to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._get_connection() as conn:
            cursor = await self._run_sync(conn.cursor)

            await self._run_sync(
                cursor.execute,
                "UPDATE templates SET is_active = ?, updated_at = ? WHERE id = ?",
                (False, datetime.utcnow().isoformat(), template_id)
            )

            await self._run_sync(conn.commit)
            affected = cursor.rowcount

            if affected > 0:
                logger.info(f"Template deactivated: {template_id}")
                return True
            return False

    def _row_to_template(self, row: sqlite3.Row) -> Template:
        """Convert database row to Template model.

        Args:
            row: Database row

        Returns:
            Template object
        """
        return Template(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            type=row["type"],
            file_path=row["file_path"],
            output_format=row["output_format"],
            version=row["version"],
            required_fields=json.loads(row["required_fields"]) if row["required_fields"] else [],
            optional_fields=json.loads(row["optional_fields"]) if row["optional_fields"] else [],
            script_path=row["script_path"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


# Global instance
_template_db: Optional[TemplateDatabaseService] = None


async def get_template_db() -> TemplateDatabaseService:
    """Get global template database instance.

    Returns:
        TemplateDatabaseService instance
    """
    global _template_db
    if _template_db is None:
        _template_db = TemplateDatabaseService()
        await _template_db.initialize()
    return _template_db
