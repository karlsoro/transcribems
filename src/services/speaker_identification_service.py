"""
Speaker identification service integrating embedding extraction, database, and confidence scoring.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from src.core.logging import get_logger
from src.services.speaker_embedding_service import SpeakerEmbeddingService
from src.services.speaker_database_service import SpeakerDatabaseService

logger = get_logger(__name__)


class SpeakerIdentificationService:
    """
    Comprehensive speaker identification service with learning capabilities.

    Combines embedding extraction, similarity matching, database storage,
    and confidence-based learning from manual feedback.
    """

    def __init__(
        self,
        embedding_service: SpeakerEmbeddingService,
        database_service: SpeakerDatabaseService,
        auto_assign_threshold: float = 0.85,
        suggest_threshold: float = 0.70,
        min_match_threshold: float = 0.60
    ):
        """
        Initialize speaker identification service.

        Args:
            embedding_service: Speaker embedding service
            database_service: Speaker database service
            auto_assign_threshold: Confidence threshold for auto-assignment (default 0.85)
            suggest_threshold: Confidence threshold for suggestions (default 0.70)
            min_match_threshold: Minimum similarity for match consideration (default 0.60)
        """
        self.embedding_service = embedding_service
        self.database_service = database_service
        self.auto_assign_threshold = auto_assign_threshold
        self.suggest_threshold = suggest_threshold
        self.min_match_threshold = min_match_threshold

        logger.info("SpeakerIdentificationService initialized", extra={
            "auto_assign_threshold": auto_assign_threshold,
            "suggest_threshold": suggest_threshold,
            "min_match_threshold": min_match_threshold
        })

    async def identify_from_audio_segment(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        transcription_id: Optional[str] = None,
        segment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Identify speaker from an audio segment.

        Args:
            audio_path: Path to audio file
            start_time: Segment start time in seconds
            end_time: Segment end time in seconds
            transcription_id: Optional transcription ID for tracking
            segment_id: Optional segment ID for tracking

        Returns:
            Dict with identification results including speaker name, confidence, and suggestions
        """
        # Extract embedding from segment
        embedding = await self.embedding_service.extract_embedding(
            audio_path,
            start_time=start_time,
            end_time=end_time
        )

        # Get all candidate embeddings from database
        candidate_embeddings = await self.database_service.get_all_embeddings()

        # Find best match
        match = await self.embedding_service.find_best_match(
            embedding,
            candidate_embeddings,
            threshold=self.min_match_threshold
        )

        if not match:
            # No match found - return unknown speaker
            return {
                'identified': False,
                'speaker_id': None,
                'speaker_name': None,
                'confidence': 0.0,
                'identification_type': 'unknown',
                'suggested_speaker': None,
                'embedding': embedding
            }

        speaker_id, similarity, metadata = match

        # Get speaker info
        speaker = await self.database_service.get_speaker_by_id(speaker_id)
        if not speaker:
            logger.warning(f"Speaker {speaker_id} not found in database")
            return {
                'identified': False,
                'speaker_id': None,
                'speaker_name': None,
                'confidence': 0.0,
                'identification_type': 'unknown',
                'suggested_speaker': None,
                'embedding': embedding
            }

        # Calculate confidence from similarity
        confidence = self.embedding_service.calculate_confidence_from_similarity(similarity)

        # Determine identification type
        if confidence >= self.auto_assign_threshold:
            identification_type = 'automatic'
            identified = True
            speaker_name = speaker['name']
            suggested_speaker = None
        elif confidence >= self.suggest_threshold:
            identification_type = 'suggested'
            identified = False
            speaker_name = None
            suggested_speaker = {
                'speaker_id': speaker_id,
                'speaker_name': speaker['name'],
                'confidence': confidence
            }
        else:
            identification_type = 'uncertain'
            identified = False
            speaker_name = None
            suggested_speaker = {
                'speaker_id': speaker_id,
                'speaker_name': speaker['name'],
                'confidence': confidence
            }

        # Record identification
        embedding_id = metadata.get('embedding_id') if isinstance(metadata, dict) else None
        if embedding_id and identified:
            await self.database_service.record_identification(
                speaker_id=speaker_id,
                embedding_id=embedding_id,
                similarity_score=similarity,
                identification_type='automatic',
                transcription_id=transcription_id,
                segment_id=segment_id,
                verified=False
            )

        result = {
            'identified': identified,
            'speaker_id': speaker_id if identified else None,
            'speaker_name': speaker_name,
            'confidence': confidence,
            'similarity': similarity,
            'identification_type': identification_type,
            'suggested_speaker': suggested_speaker,
            'embedding': embedding
        }

        logger.debug(f"Identification result: {identification_type}, confidence={confidence:.3f}", extra={
            'speaker_name': speaker_name,
            'transcription_id': transcription_id,
            'segment_id': segment_id
        })

        return result

    async def identify_batch_segments(
        self,
        audio_path: str,
        segments: List[Dict[str, Any]],
        transcription_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify speakers for multiple segments in batch.

        Args:
            audio_path: Path to audio file
            segments: List of segment dicts with 'start', 'end', and optional 'segment_id'
            transcription_id: Optional transcription ID

        Returns:
            List of identification results for each segment
        """
        results = []

        for segment in segments:
            result = await self.identify_from_audio_segment(
                audio_path=audio_path,
                start_time=segment['start'],
                end_time=segment['end'],
                transcription_id=transcription_id,
                segment_id=segment.get('segment_id')
            )
            results.append(result)

        logger.info(f"Batch identified {len(results)} segments", extra={
            'identified_count': sum(1 for r in results if r['identified']),
            'suggested_count': sum(1 for r in results if r['identification_type'] == 'suggested'),
            'uncertain_count': sum(1 for r in results if r['identification_type'] == 'uncertain'),
            'unknown_count': sum(1 for r in results if r['identification_type'] == 'unknown')
        })

        return results

    async def verify_identification(
        self,
        speaker_id: str,
        embedding: np.ndarray,
        correct: bool,
        transcription_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        source_file: Optional[str] = None,
        segment_start: Optional[float] = None,
        segment_end: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Verify or correct a speaker identification with manual feedback.

        Args:
            speaker_id: Speaker ID (confirmed or corrected)
            embedding: Speaker embedding
            correct: True if identification was correct, False if corrected
            transcription_id: Optional transcription ID
            segment_id: Optional segment ID
            source_file: Optional source audio file
            segment_start: Optional segment start time
            segment_end: Optional segment end time

        Returns:
            Dict with updated confidence and embedding ID
        """
        # Add embedding to speaker profile
        embedding_id = await self.database_service.add_embedding(
            speaker_id=speaker_id,
            embedding=embedding,
            confidence=0.95 if correct else 0.80,  # Higher confidence for manual verification
            source_file=source_file,
            segment_start=segment_start,
            segment_end=segment_end,
            metadata={
                'verified': True,
                'manual_feedback': 'correct' if correct else 'corrected'
            }
        )

        # Record identification
        await self.database_service.record_identification(
            speaker_id=speaker_id,
            embedding_id=embedding_id,
            similarity_score=1.0,  # Manual verification = perfect match
            identification_type='manual',
            transcription_id=transcription_id,
            segment_id=segment_id,
            verified=True
        )

        # Update confidence of related embeddings if this was a correction
        if not correct:
            await self._adjust_related_confidences(speaker_id, embedding, decrease=True)
        else:
            await self._adjust_related_confidences(speaker_id, embedding, decrease=False)

        logger.info(f"Verified identification for speaker {speaker_id}", extra={
            'correct': correct,
            'embedding_id': embedding_id
        })

        return {
            'embedding_id': embedding_id,
            'speaker_id': speaker_id,
            'verified': True,
            'confidence': 0.95 if correct else 0.80
        }

    async def _adjust_related_confidences(
        self,
        speaker_id: str,
        reference_embedding: np.ndarray,
        decrease: bool
    ) -> None:
        """
        Adjust confidence of related embeddings based on feedback.

        Args:
            speaker_id: Speaker ID
            reference_embedding: Reference embedding
            decrease: True to decrease confidence, False to increase
        """
        # Get all embeddings for this speaker
        embeddings = await self.database_service.get_speaker_embeddings(speaker_id)

        for emb_data in embeddings:
            # Calculate similarity with reference
            similarity = self.embedding_service.cosine_similarity(
                reference_embedding,
                emb_data['embedding']
            )

            # Adjust confidence based on similarity
            current_confidence = emb_data['confidence']

            if decrease:
                # Decrease confidence for similar embeddings (they might be wrong too)
                if similarity > 0.80:
                    new_confidence = max(0.1, current_confidence * 0.7)
                    await self.database_service.update_confidence(
                        embedding_id=emb_data['embedding_id'],
                        new_confidence=new_confidence,
                        reason='incorrect'
                    )
            else:
                # Increase confidence for similar embeddings (they're likely correct)
                if similarity > 0.80:
                    new_confidence = min(1.0, current_confidence * 1.2)
                    await self.database_service.update_confidence(
                        embedding_id=emb_data['embedding_id'],
                        new_confidence=new_confidence,
                        reason='correct'
                    )

    async def register_new_speaker(
        self,
        name: str,
        audio_path: str,
        start_time: float,
        end_time: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new speaker with initial embedding from audio segment.

        Args:
            name: Speaker name
            audio_path: Path to audio file
            start_time: Segment start time
            end_time: Segment end time
            metadata: Optional speaker metadata

        Returns:
            Speaker ID
        """
        # Create speaker profile
        speaker_id = await self.database_service.create_speaker(
            name=name,
            metadata=metadata or {}
        )

        # Extract embedding
        embedding = await self.embedding_service.extract_embedding(
            audio_path,
            start_time=start_time,
            end_time=end_time
        )

        # Add initial embedding
        await self.database_service.add_embedding(
            speaker_id=speaker_id,
            embedding=embedding,
            confidence=0.5,  # Initial confidence
            source_file=audio_path,
            segment_start=start_time,
            segment_end=end_time,
            metadata={'initial_registration': True}
        )

        logger.info(f"Registered new speaker: {name} (id={speaker_id})")

        return speaker_id

    async def get_speaker_statistics(self, speaker_id: str) -> Dict[str, Any]:
        """
        Get statistics for a speaker.

        Args:
            speaker_id: Speaker ID

        Returns:
            Dict with speaker statistics
        """
        speaker = await self.database_service.get_speaker_by_id(speaker_id)
        if not speaker:
            return {}

        embeddings = await self.database_service.get_speaker_embeddings(speaker_id)

        return {
            'speaker_id': speaker_id,
            'name': speaker['name'],
            'embedding_count': len(embeddings),
            'avg_confidence': np.mean([e['confidence'] for e in embeddings]) if embeddings else 0.0,
            'max_confidence': max([e['confidence'] for e in embeddings]) if embeddings else 0.0,
            'min_confidence': min([e['confidence'] for e in embeddings]) if embeddings else 0.0,
            'created_at': speaker['created_at'],
            'metadata': speaker['metadata']
        }
