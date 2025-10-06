"""
REST API endpoints for speaker management and identification.
"""

from typing import Optional, List
import json
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.services.speaker_embedding_service import SpeakerEmbeddingService
from src.services.speaker_database_service import SpeakerDatabaseService
from src.services.speaker_identification_service import SpeakerIdentificationService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/speakers", tags=["speakers"])

# Global service instances (initialized in lifespan)
embedding_service: Optional[SpeakerEmbeddingService] = None
database_service: Optional[SpeakerDatabaseService] = None
identification_service: Optional[SpeakerIdentificationService] = None


# Pydantic Models

class SpeakerCreate(BaseModel):
    """Request model for creating a speaker."""
    name: str = Field(..., description="Speaker name")
    metadata: Optional[dict] = Field(default={}, description="Optional metadata")


class SpeakerResponse(BaseModel):
    """Response model for speaker information."""
    id: str
    name: str
    created_at: str
    updated_at: str
    metadata: dict
    embedding_count: Optional[int] = 0
    avg_confidence: Optional[float] = 0.0


class IdentifyRequest(BaseModel):
    """Request model for speaker identification."""
    audio_path: str = Field(..., description="Path to audio file")
    start_time: float = Field(..., description="Segment start time in seconds")
    end_time: float = Field(..., description="Segment end time in seconds")
    transcription_id: Optional[str] = Field(None, description="Optional transcription ID")
    segment_id: Optional[str] = Field(None, description="Optional segment ID")


class VerifyIdentificationRequest(BaseModel):
    """Request model for verifying identification."""
    speaker_id: str = Field(..., description="Speaker ID (confirmed or corrected)")
    embedding: List[float] = Field(..., description="Speaker embedding as list")
    correct: bool = Field(..., description="True if correct, False if corrected")
    transcription_id: Optional[str] = None
    segment_id: Optional[str] = None
    source_file: Optional[str] = None
    segment_start: Optional[float] = None
    segment_end: Optional[float] = None


class RegisterSpeakerRequest(BaseModel):
    """Request model for registering new speaker."""
    name: str = Field(..., description="Speaker name")
    audio_path: str = Field(..., description="Path to audio file")
    start_time: float = Field(..., description="Segment start time")
    end_time: float = Field(..., description="Segment end time")
    metadata: Optional[dict] = Field(default={}, description="Optional metadata")


# Dependency injection helpers

def get_embedding_service() -> SpeakerEmbeddingService:
    """Get embedding service instance."""
    if embedding_service is None:
        raise HTTPException(status_code=500, detail="Embedding service not initialized")
    return embedding_service


def get_database_service() -> SpeakerDatabaseService:
    """Get database service instance."""
    if database_service is None:
        raise HTTPException(status_code=500, detail="Database service not initialized")
    return database_service


def get_identification_service() -> SpeakerIdentificationService:
    """Get identification service instance."""
    if identification_service is None:
        raise HTTPException(status_code=500, detail="Identification service not initialized")
    return identification_service


# API Endpoints

@router.post("/", response_model=SpeakerResponse)
async def create_speaker(speaker_data: SpeakerCreate):
    """
    Create a new speaker profile.
    """
    try:
        db_service = get_database_service()

        speaker_id = await db_service.create_speaker(
            name=speaker_data.name,
            metadata=speaker_data.metadata
        )

        speaker = await db_service.get_speaker_by_id(speaker_id)

        return SpeakerResponse(
            id=speaker['id'],
            name=speaker['name'],
            created_at=speaker['created_at'],
            updated_at=speaker['updated_at'],
            metadata=speaker['metadata'],
            embedding_count=0,
            avg_confidence=0.0
        )

    except Exception as e:
        logger.error(f"Failed to create speaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[SpeakerResponse])
async def list_speakers():
    """
    List all speakers.
    """
    try:
        db_service = get_database_service()
        speakers = await db_service.list_speakers()

        return [
            SpeakerResponse(
                id=s['id'],
                name=s['name'],
                created_at=s['created_at'],
                updated_at=s['updated_at'],
                metadata=s['metadata'],
                embedding_count=s['embedding_count'],
                avg_confidence=s['avg_confidence']
            )
            for s in speakers
        ]

    except Exception as e:
        logger.error(f"Failed to list speakers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{speaker_id}", response_model=SpeakerResponse)
async def get_speaker(speaker_id: str):
    """
    Get speaker details by ID.
    """
    try:
        db_service = get_database_service()
        speaker = await db_service.get_speaker_by_id(speaker_id)

        if not speaker:
            raise HTTPException(status_code=404, detail="Speaker not found")

        embeddings = await db_service.get_speaker_embeddings(speaker_id)
        avg_confidence = np.mean([e['confidence'] for e in embeddings]) if embeddings else 0.0

        return SpeakerResponse(
            id=speaker['id'],
            name=speaker['name'],
            created_at=speaker['created_at'],
            updated_at=speaker['updated_at'],
            metadata=speaker['metadata'],
            embedding_count=len(embeddings),
            avg_confidence=float(avg_confidence)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get speaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{speaker_id}")
async def delete_speaker(speaker_id: str):
    """
    Delete a speaker and all associated data.
    """
    try:
        db_service = get_database_service()
        deleted = await db_service.delete_speaker(speaker_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Speaker not found")

        return {"message": "Speaker deleted successfully", "speaker_id": speaker_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete speaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/identify")
async def identify_speaker(request: IdentifyRequest):
    """
    Identify speaker from an audio segment.
    """
    try:
        id_service = get_identification_service()

        result = await id_service.identify_from_audio_segment(
            audio_path=request.audio_path,
            start_time=request.start_time,
            end_time=request.end_time,
            transcription_id=request.transcription_id,
            segment_id=request.segment_id
        )

        # Convert numpy array to list for JSON serialization
        if 'embedding' in result:
            result['embedding'] = result['embedding'].tolist()

        return result

    except Exception as e:
        logger.error(f"Failed to identify speaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify")
async def verify_identification(request: VerifyIdentificationRequest):
    """
    Verify or correct a speaker identification with manual feedback.
    """
    try:
        id_service = get_identification_service()

        # Convert list back to numpy array
        embedding = np.array(request.embedding)

        result = await id_service.verify_identification(
            speaker_id=request.speaker_id,
            embedding=embedding,
            correct=request.correct,
            transcription_id=request.transcription_id,
            segment_id=request.segment_id,
            source_file=request.source_file,
            segment_start=request.segment_start,
            segment_end=request.segment_end
        )

        return result

    except Exception as e:
        logger.error(f"Failed to verify identification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_speaker(request: RegisterSpeakerRequest):
    """
    Register a new speaker with initial embedding from audio segment.
    """
    try:
        id_service = get_identification_service()

        speaker_id = await id_service.register_new_speaker(
            name=request.name,
            audio_path=request.audio_path,
            start_time=request.start_time,
            end_time=request.end_time,
            metadata=request.metadata
        )

        # Get speaker details
        db_service = get_database_service()
        speaker = await db_service.get_speaker_by_id(speaker_id)

        return {
            "speaker_id": speaker_id,
            "name": speaker['name'],
            "message": "Speaker registered successfully"
        }

    except Exception as e:
        logger.error(f"Failed to register speaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{speaker_id}/statistics")
async def get_speaker_statistics(speaker_id: str):
    """
    Get statistics for a speaker.
    """
    try:
        id_service = get_identification_service()
        stats = await id_service.get_speaker_statistics(speaker_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Speaker not found")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get speaker statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{speaker_id}/embeddings")
async def get_speaker_embeddings(speaker_id: str):
    """
    Get all embeddings for a speaker.
    """
    try:
        db_service = get_database_service()
        embeddings = await db_service.get_speaker_embeddings(speaker_id)

        # Convert numpy arrays to lists
        for emb in embeddings:
            if 'embedding' in emb:
                emb['embedding'] = emb['embedding'].tolist()

        return {
            "speaker_id": speaker_id,
            "embeddings": embeddings,
            "count": len(embeddings)
        }

    except Exception as e:
        logger.error(f"Failed to get speaker embeddings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Service initialization function (to be called from main app)

async def initialize_speaker_services(
    hf_token: Optional[str] = None,
    db_path: str = "speaker_database.db"
):
    """
    Initialize speaker services.

    Args:
        hf_token: Hugging Face token
        db_path: Database file path
    """
    global embedding_service, database_service, identification_service

    # Initialize services
    embedding_service = SpeakerEmbeddingService(hf_token=hf_token)
    database_service = SpeakerDatabaseService(db_path=db_path)
    identification_service = SpeakerIdentificationService(
        embedding_service=embedding_service,
        database_service=database_service
    )

    # Initialize database schema
    await database_service.initialize()

    # Load embedding model
    await embedding_service.load_model()

    logger.info("Speaker services initialized successfully")


async def cleanup_speaker_services():
    """Cleanup speaker services."""
    global embedding_service, database_service, identification_service

    if embedding_service:
        await embedding_service.cleanup()

    embedding_service = None
    database_service = None
    identification_service = None

    logger.info("Speaker services cleaned up")
