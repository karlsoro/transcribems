"""
Speaker database service for storing and managing speaker embeddings and identities.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import numpy as np

from src.core.logging import get_logger

logger = get_logger(__name__)


class SpeakerDatabaseService:
    """
    Service for managing speaker database with embeddings and confidence scores.

    Uses SQLite for development/standalone deployment. Can be extended to PostgreSQL
    with pgvector for production use.
    """

    def __init__(self, db_path: str = "speaker_database.db"):
        """
        Initialize speaker database service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._connection = None
        self._lock = asyncio.Lock()

        logger.info(f"SpeakerDatabaseService initialized", extra={
            "db_path": str(self.db_path)
        })

    async def initialize(self) -> None:
        """
        Initialize database schema.
        """
        async with self._lock:
            await asyncio.to_thread(self._initialize_sync)

    def _initialize_sync(self) -> None:
        """
        Synchronous database initialization.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create speakers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speakers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)

        # Create speaker_embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speaker_embeddings (
                id TEXT PRIMARY KEY,
                speaker_id TEXT NOT NULL,
                embedding TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                source_file TEXT,
                audio_segment_start REAL,
                audio_segment_end REAL,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE CASCADE
            )
        """)

        # Create speaker_identifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speaker_identifications (
                id TEXT PRIMARY KEY,
                speaker_id TEXT NOT NULL,
                embedding_id TEXT NOT NULL,
                transcription_id TEXT,
                segment_id TEXT,
                similarity_score REAL,
                identification_type TEXT CHECK (identification_type IN ('automatic', 'manual')),
                verified INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (speaker_id) REFERENCES speakers(id) ON DELETE CASCADE,
                FOREIGN KEY (embedding_id) REFERENCES speaker_embeddings(id) ON DELETE CASCADE
            )
        """)

        # Create confidence_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_history (
                id TEXT PRIMARY KEY,
                embedding_id TEXT NOT NULL,
                old_confidence REAL NOT NULL,
                new_confidence REAL NOT NULL,
                reason TEXT CHECK (reason IN ('correct', 'incorrect', 'manual_verify', 'manual_reject')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (embedding_id) REFERENCES speaker_embeddings(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_speaker_embeddings_speaker_id ON speaker_embeddings(speaker_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_speaker_identifications_speaker_id ON speaker_identifications(speaker_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_speaker_identifications_transcription ON speaker_identifications(transcription_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence_history_embedding_id ON confidence_history(embedding_id)")

        conn.commit()
        conn.close()

        logger.info("Database schema initialized")

    async def create_speaker(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new speaker profile.

        Args:
            name: Speaker name
            metadata: Optional metadata

        Returns:
            Speaker ID
        """
        speaker_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        async with self._lock:
            await asyncio.to_thread(
                self._create_speaker_sync,
                speaker_id,
                name,
                now,
                metadata or {}
            )

        logger.info(f"Created speaker: {name} (id={speaker_id})")
        return speaker_id

    def _create_speaker_sync(
        self,
        speaker_id: str,
        name: str,
        now: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Synchronous speaker creation."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO speakers (id, name, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (speaker_id, name, now, now, json.dumps(metadata)))

        conn.commit()
        conn.close()

    async def add_embedding(
        self,
        speaker_id: str,
        embedding: np.ndarray,
        confidence: float = 0.5,
        source_file: Optional[str] = None,
        segment_start: Optional[float] = None,
        segment_end: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an embedding to a speaker profile.

        Args:
            speaker_id: Speaker ID
            embedding: 512-dimensional embedding
            confidence: Initial confidence score
            source_file: Source audio file path
            segment_start: Audio segment start time
            segment_end: Audio segment end time
            metadata: Optional metadata

        Returns:
            Embedding ID
        """
        embedding_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        # Convert embedding to JSON
        embedding_json = json.dumps(embedding.tolist())

        async with self._lock:
            await asyncio.to_thread(
                self._add_embedding_sync,
                embedding_id,
                speaker_id,
                embedding_json,
                confidence,
                source_file,
                segment_start,
                segment_end,
                now,
                metadata or {}
            )

        logger.debug(f"Added embedding to speaker {speaker_id} (embedding_id={embedding_id})")
        return embedding_id

    def _add_embedding_sync(
        self,
        embedding_id: str,
        speaker_id: str,
        embedding_json: str,
        confidence: float,
        source_file: Optional[str],
        segment_start: Optional[float],
        segment_end: Optional[float],
        now: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Synchronous embedding addition."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO speaker_embeddings
            (id, speaker_id, embedding, confidence, source_file,
             audio_segment_start, audio_segment_end, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            embedding_id, speaker_id, embedding_json, confidence,
            source_file, segment_start, segment_end, now, json.dumps(metadata)
        ))

        conn.commit()
        conn.close()

    async def get_all_embeddings(self) -> List[Dict[str, Any]]:
        """
        Get all speaker embeddings with metadata.

        Returns:
            List of embedding dicts with speaker_id, embedding, and metadata
        """
        async with self._lock:
            return await asyncio.to_thread(self._get_all_embeddings_sync)

    def _get_all_embeddings_sync(self) -> List[Dict[str, Any]]:
        """Synchronous get all embeddings."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.id, e.speaker_id, e.embedding, e.confidence,
                e.source_file, e.audio_segment_start, e.audio_segment_end,
                s.name, e.metadata
            FROM speaker_embeddings e
            JOIN speakers s ON e.speaker_id = s.id
            ORDER BY e.confidence DESC
        """)

        embeddings = []
        for row in cursor.fetchall():
            embeddings.append({
                'embedding_id': row[0],
                'speaker_id': row[1],
                'embedding': np.array(json.loads(row[2])),
                'confidence': row[3],
                'source_file': row[4],
                'audio_segment_start': row[5],
                'audio_segment_end': row[6],
                'speaker_name': row[7],
                'metadata': json.loads(row[8] or '{}')
            })

        conn.close()
        return embeddings

    async def get_speaker_embeddings(self, speaker_id: str) -> List[Dict[str, Any]]:
        """
        Get all embeddings for a specific speaker.

        Args:
            speaker_id: Speaker ID

        Returns:
            List of embedding dicts
        """
        async with self._lock:
            return await asyncio.to_thread(self._get_speaker_embeddings_sync, speaker_id)

    def _get_speaker_embeddings_sync(self, speaker_id: str) -> List[Dict[str, Any]]:
        """Synchronous get speaker embeddings."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, embedding, confidence, source_file,
                   audio_segment_start, audio_segment_end, metadata
            FROM speaker_embeddings
            WHERE speaker_id = ?
            ORDER BY confidence DESC
        """, (speaker_id,))

        embeddings = []
        for row in cursor.fetchall():
            embeddings.append({
                'embedding_id': row[0],
                'speaker_id': speaker_id,
                'embedding': np.array(json.loads(row[1])),
                'confidence': row[2],
                'source_file': row[3],
                'audio_segment_start': row[4],
                'audio_segment_end': row[5],
                'metadata': json.loads(row[6] or '{}')
            })

        conn.close()
        return embeddings

    async def record_identification(
        self,
        speaker_id: str,
        embedding_id: str,
        similarity_score: float,
        identification_type: str,
        transcription_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        verified: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record a speaker identification.

        Args:
            speaker_id: Identified speaker ID
            embedding_id: Embedding ID used for identification
            similarity_score: Similarity score
            identification_type: 'automatic' or 'manual'
            transcription_id: Optional transcription ID
            segment_id: Optional segment ID
            verified: Whether identification is verified
            metadata: Optional metadata

        Returns:
            Identification ID
        """
        identification_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        async with self._lock:
            await asyncio.to_thread(
                self._record_identification_sync,
                identification_id,
                speaker_id,
                embedding_id,
                transcription_id,
                segment_id,
                similarity_score,
                identification_type,
                verified,
                now,
                metadata or {}
            )

        logger.debug(f"Recorded {identification_type} identification: speaker={speaker_id}, similarity={similarity_score:.3f}")
        return identification_id

    def _record_identification_sync(
        self,
        identification_id: str,
        speaker_id: str,
        embedding_id: str,
        transcription_id: Optional[str],
        segment_id: Optional[str],
        similarity_score: float,
        identification_type: str,
        verified: bool,
        now: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Synchronous record identification."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO speaker_identifications
            (id, speaker_id, embedding_id, transcription_id, segment_id,
             similarity_score, identification_type, verified, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            identification_id, speaker_id, embedding_id, transcription_id,
            segment_id, similarity_score, identification_type,
            1 if verified else 0, now, json.dumps(metadata)
        ))

        conn.commit()
        conn.close()

    async def update_confidence(
        self,
        embedding_id: str,
        new_confidence: float,
        reason: str
    ) -> None:
        """
        Update embedding confidence score.

        Args:
            embedding_id: Embedding ID
            new_confidence: New confidence score
            reason: Reason for update ('correct', 'incorrect', 'manual_verify', 'manual_reject')
        """
        async with self._lock:
            await asyncio.to_thread(
                self._update_confidence_sync,
                embedding_id,
                new_confidence,
                reason
            )

        logger.debug(f"Updated confidence for embedding {embedding_id}: reason={reason}, new_confidence={new_confidence:.3f}")

    def _update_confidence_sync(
        self,
        embedding_id: str,
        new_confidence: float,
        reason: str
    ) -> None:
        """Synchronous confidence update."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Get current confidence
        cursor.execute("SELECT confidence FROM speaker_embeddings WHERE id = ?", (embedding_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        old_confidence = row[0]

        # Update confidence
        cursor.execute("""
            UPDATE speaker_embeddings
            SET confidence = ?
            WHERE id = ?
        """, (new_confidence, embedding_id))

        # Record history
        history_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO confidence_history
            (id, embedding_id, old_confidence, new_confidence, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (history_id, embedding_id, old_confidence, new_confidence, reason, now))

        conn.commit()
        conn.close()

    async def get_speaker_by_id(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get speaker information by ID.

        Args:
            speaker_id: Speaker ID

        Returns:
            Speaker dict or None if not found
        """
        async with self._lock:
            return await asyncio.to_thread(self._get_speaker_by_id_sync, speaker_id)

    def _get_speaker_by_id_sync(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous get speaker by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, created_at, updated_at, metadata
            FROM speakers
            WHERE id = ?
        """, (speaker_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'metadata': json.loads(row[4] or '{}')
            }
        return None

    async def list_speakers(self) -> List[Dict[str, Any]]:
        """
        List all speakers.

        Returns:
            List of speaker dicts
        """
        async with self._lock:
            return await asyncio.to_thread(self._list_speakers_sync)

    def _list_speakers_sync(self) -> List[Dict[str, Any]]:
        """Synchronous list speakers."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.id, s.name, s.created_at, s.updated_at, s.metadata,
                COUNT(e.id) as embedding_count,
                AVG(e.confidence) as avg_confidence
            FROM speakers s
            LEFT JOIN speaker_embeddings e ON s.id = e.speaker_id
            GROUP BY s.id
            ORDER BY s.name
        """)

        speakers = []
        for row in cursor.fetchall():
            speakers.append({
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'metadata': json.loads(row[4] or '{}'),
                'embedding_count': row[5] or 0,
                'avg_confidence': row[6] or 0.0
            })

        conn.close()
        return speakers

    async def delete_speaker(self, speaker_id: str) -> bool:
        """
        Delete a speaker and all associated data.

        Args:
            speaker_id: Speaker ID

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            return await asyncio.to_thread(self._delete_speaker_sync, speaker_id)

    def _delete_speaker_sync(self, speaker_id: str) -> bool:
        """Synchronous speaker deletion."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM speakers WHERE id = ?", (speaker_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted speaker {speaker_id}")

        return deleted
