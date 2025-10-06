"""
Unit tests for speaker embedding service.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

from src.services.speaker_embedding_service import SpeakerEmbeddingService


@pytest.fixture
def mock_embedding_service():
    """Create mock embedding service."""
    service = SpeakerEmbeddingService(device="cpu", hf_token=None)
    # Mock the model loading
    service._embedding_model = Mock()
    service._inference = Mock()
    return service


def test_cosine_similarity():
    """Test cosine similarity calculation."""
    # Identical vectors
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([1, 0, 0])
    similarity = SpeakerEmbeddingService.cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.001

    # Orthogonal vectors
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([0, 1, 0])
    similarity = SpeakerEmbeddingService.cosine_similarity(vec1, vec2)
    assert abs(similarity - 0.0) < 0.001

    # Opposite vectors
    vec1 = np.array([1, 0, 0])
    vec2 = np.array([-1, 0, 0])
    similarity = SpeakerEmbeddingService.cosine_similarity(vec1, vec2)
    assert abs(similarity - (-1.0)) < 0.001


def test_calculate_confidence_from_similarity():
    """Test confidence calculation from similarity."""
    # High similarity -> high confidence
    confidence = SpeakerEmbeddingService.calculate_confidence_from_similarity(0.90)
    assert confidence == 0.95

    # Good similarity -> good confidence
    confidence = SpeakerEmbeddingService.calculate_confidence_from_similarity(0.80)
    assert confidence == 0.85

    # Medium similarity -> medium confidence
    confidence = SpeakerEmbeddingService.calculate_confidence_from_similarity(0.70)
    assert confidence == 0.70

    # Low similarity -> low confidence
    confidence = SpeakerEmbeddingService.calculate_confidence_from_similarity(0.62)
    assert confidence == 0.60

    # Very low similarity -> very low confidence
    confidence = SpeakerEmbeddingService.calculate_confidence_from_similarity(0.50)
    assert confidence == 0.50


def test_get_confidence_level():
    """Test confidence level labeling."""
    assert SpeakerEmbeddingService.get_confidence_level(0.95) == 'high'
    assert SpeakerEmbeddingService.get_confidence_level(0.80) == 'medium'
    assert SpeakerEmbeddingService.get_confidence_level(0.65) == 'low'
    assert SpeakerEmbeddingService.get_confidence_level(0.50) == 'very_low'


@pytest.mark.asyncio
async def test_find_best_match():
    """Test finding best matching speaker."""
    service = SpeakerEmbeddingService(device="cpu")

    query_embedding = np.array([1.0, 0.0, 0.0] + [0.0] * 509)  # 512-dim

    candidates = [
        {
            'speaker_id': 'speaker-1',
            'embedding': np.array([0.9, 0.1, 0.0] + [0.0] * 509),  # High similarity
            'metadata': {'name': 'Alice'}
        },
        {
            'speaker_id': 'speaker-2',
            'embedding': np.array([0.5, 0.5, 0.0] + [0.0] * 509),  # Medium similarity
            'metadata': {'name': 'Bob'}
        },
        {
            'speaker_id': 'speaker-3',
            'embedding': np.array([0.0, 1.0, 0.0] + [0.0] * 509),  # Low similarity
            'metadata': {'name': 'Charlie'}
        }
    ]

    # Find best match
    match = await service.find_best_match(query_embedding, candidates, threshold=0.6)

    assert match is not None
    speaker_id, similarity, metadata = match
    assert speaker_id == 'speaker-1'
    assert similarity > 0.9
    assert metadata['name'] == 'Alice'


@pytest.mark.asyncio
async def test_find_best_match_no_match():
    """Test when no match exceeds threshold."""
    service = SpeakerEmbeddingService(device="cpu")

    query_embedding = np.array([1.0, 0.0, 0.0] + [0.0] * 509)

    candidates = [
        {
            'speaker_id': 'speaker-1',
            'embedding': np.array([0.0, 1.0, 0.0] + [0.0] * 509),  # Low similarity
            'metadata': {'name': 'Alice'}
        }
    ]

    # Find best match with high threshold
    match = await service.find_best_match(query_embedding, candidates, threshold=0.9)

    assert match is None


@pytest.mark.asyncio
async def test_find_best_match_empty_candidates():
    """Test with no candidates."""
    service = SpeakerEmbeddingService(device="cpu")

    query_embedding = np.array([1.0] + [0.0] * 511)

    match = await service.find_best_match(query_embedding, [], threshold=0.6)

    assert match is None


def test_cosine_similarity_zero_vectors():
    """Test cosine similarity with zero vectors."""
    vec1 = np.array([0, 0, 0])
    vec2 = np.array([1, 0, 0])

    similarity = SpeakerEmbeddingService.cosine_similarity(vec1, vec2)
    assert similarity == 0.0

    vec1 = np.array([0, 0, 0])
    vec2 = np.array([0, 0, 0])

    similarity = SpeakerEmbeddingService.cosine_similarity(vec1, vec2)
    assert similarity == 0.0


def test_cosine_similarity_normalized():
    """Test cosine similarity with normalized vectors."""
    # Unit vectors should give same result regardless of magnitude
    vec1 = np.array([1, 1, 0])
    vec2 = np.array([2, 2, 0])

    similarity = SpeakerEmbeddingService.cosine_similarity(vec1, vec2)
    assert abs(similarity - 1.0) < 0.001  # Should be identical direction
