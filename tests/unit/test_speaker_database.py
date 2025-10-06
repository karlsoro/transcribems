"""
Unit tests for speaker database service.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path

from src.services.speaker_database_service import SpeakerDatabaseService


@pytest.fixture
async def db_service():
    """Create temporary database service."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    service = SpeakerDatabaseService(db_path=db_path)
    await service.initialize()

    yield service

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_create_speaker(db_service):
    """Test creating a speaker."""
    speaker_id = await db_service.create_speaker(
        name="John Doe",
        metadata={"role": "presenter"}
    )

    assert speaker_id is not None
    assert len(speaker_id) > 0

    # Verify speaker was created
    speaker = await db_service.get_speaker_by_id(speaker_id)
    assert speaker is not None
    assert speaker['name'] == "John Doe"
    assert speaker['metadata']['role'] == "presenter"


@pytest.mark.asyncio
async def test_add_embedding(db_service):
    """Test adding an embedding to a speaker."""
    # Create speaker
    speaker_id = await db_service.create_speaker(name="Jane Smith")

    # Create dummy embedding
    embedding = np.random.rand(512)

    # Add embedding
    embedding_id = await db_service.add_embedding(
        speaker_id=speaker_id,
        embedding=embedding,
        confidence=0.8,
        source_file="test.wav",
        segment_start=0.0,
        segment_end=5.0
    )

    assert embedding_id is not None

    # Verify embedding was added
    embeddings = await db_service.get_speaker_embeddings(speaker_id)
    assert len(embeddings) == 1
    assert embeddings[0]['confidence'] == 0.8
    assert embeddings[0]['source_file'] == "test.wav"
    assert np.allclose(embeddings[0]['embedding'], embedding)


@pytest.mark.asyncio
async def test_get_all_embeddings(db_service):
    """Test getting all embeddings."""
    # Create two speakers with embeddings
    speaker1_id = await db_service.create_speaker(name="Speaker 1")
    speaker2_id = await db_service.create_speaker(name="Speaker 2")

    embedding1 = np.random.rand(512)
    embedding2 = np.random.rand(512)

    await db_service.add_embedding(speaker1_id, embedding1, confidence=0.9)
    await db_service.add_embedding(speaker2_id, embedding2, confidence=0.7)

    # Get all embeddings
    all_embeddings = await db_service.get_all_embeddings()

    assert len(all_embeddings) == 2
    assert all_embeddings[0]['confidence'] == 0.9  # Sorted by confidence DESC
    assert all_embeddings[1]['confidence'] == 0.7


@pytest.mark.asyncio
async def test_record_identification(db_service):
    """Test recording a speaker identification."""
    # Create speaker and embedding
    speaker_id = await db_service.create_speaker(name="Test Speaker")
    embedding = np.random.rand(512)
    embedding_id = await db_service.add_embedding(speaker_id, embedding)

    # Record identification
    identification_id = await db_service.record_identification(
        speaker_id=speaker_id,
        embedding_id=embedding_id,
        similarity_score=0.92,
        identification_type="automatic",
        transcription_id="trans-123",
        segment_id="seg-456",
        verified=True
    )

    assert identification_id is not None
    assert len(identification_id) > 0


@pytest.mark.asyncio
async def test_update_confidence(db_service):
    """Test updating embedding confidence."""
    # Create speaker and embedding
    speaker_id = await db_service.create_speaker(name="Test Speaker")
    embedding = np.random.rand(512)
    embedding_id = await db_service.add_embedding(
        speaker_id, embedding, confidence=0.5
    )

    # Update confidence
    await db_service.update_confidence(
        embedding_id=embedding_id,
        new_confidence=0.9,
        reason="correct"
    )

    # Verify confidence was updated
    embeddings = await db_service.get_speaker_embeddings(speaker_id)
    assert embeddings[0]['confidence'] == 0.9


@pytest.mark.asyncio
async def test_list_speakers(db_service):
    """Test listing all speakers."""
    # Create multiple speakers
    await db_service.create_speaker(name="Alice")
    await db_service.create_speaker(name="Bob")
    await db_service.create_speaker(name="Charlie")

    # List speakers
    speakers = await db_service.list_speakers()

    assert len(speakers) == 3
    names = [s['name'] for s in speakers]
    assert "Alice" in names
    assert "Bob" in names
    assert "Charlie" in names


@pytest.mark.asyncio
async def test_delete_speaker(db_service):
    """Test deleting a speaker."""
    # Create speaker with embedding
    speaker_id = await db_service.create_speaker(name="To Delete")
    embedding = np.random.rand(512)
    await db_service.add_embedding(speaker_id, embedding)

    # Delete speaker
    deleted = await db_service.delete_speaker(speaker_id)
    assert deleted is True

    # Verify speaker is gone
    speaker = await db_service.get_speaker_by_id(speaker_id)
    assert speaker is None

    # Verify embeddings are gone (cascade delete)
    embeddings = await db_service.get_speaker_embeddings(speaker_id)
    assert len(embeddings) == 0


@pytest.mark.asyncio
async def test_confidence_history(db_service):
    """Test that confidence history is recorded."""
    # Create speaker and embedding
    speaker_id = await db_service.create_speaker(name="Test Speaker")
    embedding = np.random.rand(512)
    embedding_id = await db_service.add_embedding(
        speaker_id, embedding, confidence=0.5
    )

    # Update confidence multiple times
    await db_service.update_confidence(embedding_id, 0.7, "correct")
    await db_service.update_confidence(embedding_id, 0.9, "correct")
    await db_service.update_confidence(embedding_id, 0.6, "incorrect")

    # Final confidence should be 0.6
    embeddings = await db_service.get_speaker_embeddings(speaker_id)
    assert embeddings[0]['confidence'] == 0.6
