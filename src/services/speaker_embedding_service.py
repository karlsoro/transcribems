"""
Speaker embedding extraction and comparison service using pyannote.audio.
"""

import asyncio
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Configure audio backend
import os
os.environ.setdefault('TORCHAUDIO_BACKEND', 'soundfile')
warnings.filterwarnings("ignore", message=".*torchaudio.*")

import torch

from src.core.logging import get_logger

logger = get_logger(__name__)


class SpeakerEmbeddingService:
    """
    Service for extracting and comparing speaker embeddings using pyannote.audio.

    Uses pyannote/embedding model to generate 512-dimensional speaker embeddings
    for speaker identification and verification.
    """

    def __init__(
        self,
        device: Optional[str] = None,
        hf_token: Optional[str] = None
    ):
        """
        Initialize the speaker embedding service.

        Args:
            device: Device to use (cuda, cpu, or auto)
            hf_token: Hugging Face token for model access
        """
        self.hf_token = hf_token
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self._embedding_model = None
        self._inference = None

        logger.info(f"SpeakerEmbeddingService initialized", extra={
            "device": self.device
        })

    async def load_model(self) -> None:
        """
        Load the pyannote.audio embedding model.

        Raises:
            RuntimeError: If model loading fails
        """
        if self._embedding_model is not None:
            return

        try:
            logger.info("Loading pyannote embedding model")

            from pyannote.audio import Model, Inference

            # Load model in thread to avoid blocking
            self._embedding_model = await asyncio.to_thread(
                Model.from_pretrained,
                "pyannote/embedding",
                use_auth_token=self.hf_token
            )

            # Create inference wrapper
            self._inference = Inference(
                self._embedding_model,
                window="whole",
                device=torch.device(self.device)
            )

            logger.info("Pyannote embedding model loaded successfully")

        except Exception as e:
            logger.warning(f"Speaker embedding model not available: {e}")
            # Don't raise - allow the service to continue without speaker identification
            self._inference = None
            self._embedding_model = None

    async def extract_embedding(
        self,
        audio_path: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> np.ndarray:
        """
        Extract speaker embedding from audio file or segment.

        Args:
            audio_path: Path to audio file
            start_time: Start time of segment in seconds (optional)
            end_time: End time of segment in seconds (optional)

        Returns:
            512-dimensional embedding as numpy array

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If embedding extraction fails
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model if not loaded
        await self.load_model()

        try:
            logger.debug(f"Extracting embedding from {audio_path}", extra={
                "start_time": start_time,
                "end_time": end_time
            })

            # Import for audio handling
            from pyannote.audio import Audio
            from pyannote.core import Segment

            # Load audio
            audio = Audio(sample_rate=16000, mono=True)

            # Create segment if times provided
            if start_time is not None and end_time is not None:
                segment = Segment(start=start_time, end=end_time)
                waveform, sample_rate = audio.crop(str(audio_path), segment)
            else:
                waveform, sample_rate = audio(str(audio_path))

            # Extract embedding in thread to avoid blocking
            embedding = await asyncio.to_thread(
                self._extract_embedding_sync,
                waveform
            )

            logger.debug(f"Embedding extracted, shape: {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}", exc_info=True)
            raise RuntimeError(f"Embedding extraction failed: {str(e)}")

    def _extract_embedding_sync(self, waveform: torch.Tensor) -> np.ndarray:
        """
        Synchronous embedding extraction (runs in thread).

        Args:
            waveform: Audio waveform tensor

        Returns:
            Embedding as numpy array
        """
        # Inference returns embedding
        embedding = self._inference({"waveform": waveform, "sample_rate": 16000})

        # Convert to numpy
        if torch.is_tensor(embedding):
            embedding = embedding.cpu().numpy()

        return embedding

    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between -1 and 1 (higher is more similar)
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

        return float(similarity)

    async def find_best_match(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[Dict[str, Any]],
        threshold: float = 0.6
    ) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """
        Find the best matching speaker from candidate embeddings.

        Args:
            query_embedding: Embedding to match
            candidate_embeddings: List of dicts with 'speaker_id', 'embedding', and metadata
            threshold: Minimum similarity threshold for a match

        Returns:
            Tuple of (speaker_id, similarity_score, metadata) or None if no match
        """
        if not candidate_embeddings:
            return None

        best_match = None
        best_similarity = threshold

        for candidate in candidate_embeddings:
            similarity = self.cosine_similarity(
                query_embedding,
                candidate['embedding']
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = (
                    candidate['speaker_id'],
                    similarity,
                    candidate.get('metadata', {})
                )

        if best_match:
            logger.debug(f"Best match found: speaker_id={best_match[0]}, similarity={best_match[1]:.3f}")
        else:
            logger.debug(f"No match found above threshold {threshold}")

        return best_match

    async def batch_extract_embeddings(
        self,
        audio_path: str,
        segments: List[Dict[str, float]]
    ) -> List[np.ndarray]:
        """
        Extract embeddings for multiple segments in batch.

        Args:
            audio_path: Path to audio file
            segments: List of dicts with 'start' and 'end' times

        Returns:
            List of embeddings corresponding to each segment
        """
        embeddings = []

        for segment in segments:
            try:
                embedding = await self.extract_embedding(
                    audio_path,
                    start_time=segment.get('start'),
                    end_time=segment.get('end')
                )
                embeddings.append(embedding)
            except Exception as e:
                logger.warning(f"Failed to extract embedding for segment {segment}: {e}")
                # Use zero embedding for failed extractions
                embeddings.append(np.zeros(512))

        logger.info(f"Extracted {len(embeddings)} embeddings from {len(segments)} segments")
        return embeddings

    @staticmethod
    def calculate_confidence_from_similarity(similarity: float) -> float:
        """
        Calculate confidence score from similarity score.

        Args:
            similarity: Cosine similarity score (0-1)

        Returns:
            Confidence score (0-1)
        """
        if similarity >= 0.85:
            return 0.95  # High confidence
        elif similarity >= 0.75:
            return 0.85  # Good confidence
        elif similarity >= 0.65:
            return 0.70  # Medium confidence
        elif similarity >= 0.60:
            return 0.60  # Low confidence
        else:
            return 0.50  # Very low confidence

    @staticmethod
    def get_confidence_level(confidence: float) -> str:
        """
        Get confidence level label from confidence score.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Confidence level: 'high', 'medium', 'low', or 'very_low'
        """
        if confidence >= 0.85:
            return 'high'
        elif confidence >= 0.70:
            return 'medium'
        elif confidence >= 0.60:
            return 'low'
        else:
            return 'very_low'

    async def cleanup(self) -> None:
        """Clean up loaded models and free memory."""
        logger.info("Cleaning up speaker embedding service")

        self._embedding_model = None
        self._inference = None

        # Clear GPU memory if using CUDA
        if self.device.startswith("cuda"):
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        logger.info("Speaker embedding service cleanup completed")
