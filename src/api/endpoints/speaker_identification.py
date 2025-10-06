"""
Speaker Identification API Endpoint

Separate from transcription - handles speaker identification with confidence scoring.
UI sends audio clips to identify speakers, system returns matches from DB.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import uuid
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/speaker", tags=["speaker-identification"])


# Pydantic models for request/response
class SpeakerMatch(BaseModel):
    """Speaker identification match result"""
    speaker_name: Optional[str] = None
    confidence_score: float
    match_found: bool
    embedding_id: Optional[str] = None


class SpeakerFeedback(BaseModel):
    """User feedback on speaker identification"""
    audio_clip_id: str
    suggested_name: Optional[str] = None  # What system suggested
    user_provided_name: str  # What user says it is
    user_agrees: bool  # True if user agrees with suggestion


class SpeakerIdentificationResponse(BaseModel):
    """Response for speaker identification"""
    match_found: bool
    speaker_name: Optional[str] = None
    confidence_score: float
    audio_clip_id: str  # To reference in feedback
    message: str


@router.post("/identify", response_model=SpeakerIdentificationResponse)
async def identify_speaker(
    audio_clip: UploadFile = File(..., description="Short audio clip of the speaker"),
    job_id: str = Form(..., description="Original transcription job ID for context"),
    segment_index: int = Form(..., description="Segment index from transcription")
):
    """
    Identify a speaker from an audio clip.

    **Flow:**
    1. UI extracts audio segment from original file based on transcription timestamps
    2. Sends short clip (2-5 seconds) to this endpoint
    3. System extracts embedding and searches speaker DB
    4. Returns match if found (with confidence) or "not found"

    **Parameters:**
    - audio_clip: Short audio file (WAV format, 2-5 seconds)
    - job_id: Original transcription job ID (for logging/tracking)
    - segment_index: Which segment from transcription this corresponds to

    **Returns:**
    - match_found: True if speaker found in DB
    - speaker_name: Name of identified speaker (if match_found=True)
    - confidence_score: 0.0-1.0 confidence score
    - audio_clip_id: ID to use when submitting feedback
    - message: Human-readable status message
    """

    audio_clip_id = str(uuid.uuid4())

    logger.info("Speaker identification request", extra={
        "audio_clip_id": audio_clip_id,
        "job_id": job_id,
        "segment_index": segment_index,
        "filename": audio_clip.filename
    })

    try:
        # Validate audio file
        if not audio_clip.content_type or not audio_clip.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid audio format: {audio_clip.content_type}"
            )

        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_clip.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name

        # TODO: Extract embedding from audio clip
        # from src.services.speaker_embedding_service import speaker_embedding_service
        # embedding = await speaker_embedding_service.extract_embedding(temp_audio_path)

        # TODO: Search speaker database for match
        # from src.services.speaker_database_service import speaker_db_service
        # match = await speaker_db_service.find_speaker_by_embedding(
        #     embedding,
        #     threshold=0.75  # Configurable threshold
        # )

        # PLACEHOLDER: Return "not found" until services are enabled
        # When speaker services are enabled, this will do actual matching

        Path(temp_audio_path).unlink()  # Clean up temp file

        return SpeakerIdentificationResponse(
            match_found=False,
            speaker_name=None,
            confidence_score=0.0,
            audio_clip_id=audio_clip_id,
            message="No match found in speaker database"
        )

        # EXAMPLE RESPONSE when match IS found:
        # return SpeakerIdentificationResponse(
        #     match_found=True,
        #     speaker_name="John Doe",
        #     confidence_score=0.87,
        #     audio_clip_id=audio_clip_id,
        #     message="Speaker identified with high confidence"
        # )

    except Exception as e:
        logger.error(f"Speaker identification failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_speaker_feedback(feedback: SpeakerFeedback):
    """
    Submit user feedback on speaker identification.

    **Flow:**
    1. User reviews speaker identification suggestion
    2. Either agrees or provides correct name
    3. UI calls this endpoint with feedback
    4. System updates confidence scores in DB

    **If user agrees (user_agrees=True):**
    - Increase confidence score for suggested_name
    - Strengthen association between embedding and name

    **If user provides different name (user_agrees=False):**
    - Decrease confidence for suggested_name (if it was suggested)
    - Add/increase confidence for user_provided_name
    - If user_provided_name is new, add to DB with initial score

    **Parameters:**
    - audio_clip_id: ID from identify_speaker response
    - suggested_name: What system suggested (None if no match)
    - user_provided_name: What user says correct name is
    - user_agrees: True if user agrees with suggestion

    **Returns:**
    - success: True if feedback processed
    - message: What action was taken
    - new_speaker_added: True if this created a new speaker in DB
    """

    logger.info("Speaker feedback received", extra={
        "audio_clip_id": feedback.audio_clip_id,
        "suggested_name": feedback.suggested_name,
        "user_provided_name": feedback.user_provided_name,
        "user_agrees": feedback.user_agrees
    })

    try:
        # TODO: Get embedding from audio_clip_id cache
        # embedding = await get_cached_embedding(feedback.audio_clip_id)

        new_speaker_added = False
        message = ""

        if feedback.user_agrees and feedback.suggested_name:
            # User agrees - increase confidence
            # TODO: await speaker_db_service.increase_confidence(
            #     speaker_name=feedback.suggested_name,
            #     embedding=embedding,
            #     amount=0.1  # Configurable boost
            # )
            message = f"Confidence increased for '{feedback.suggested_name}'"

        elif not feedback.user_agrees and feedback.suggested_name:
            # User disagrees - decrease old, increase new
            # TODO: await speaker_db_service.decrease_confidence(
            #     speaker_name=feedback.suggested_name,
            #     embedding=embedding,
            #     amount=0.05
            # )
            # TODO: speaker_exists = await speaker_db_service.speaker_exists(feedback.user_provided_name)
            # if not speaker_exists:
            #     await speaker_db_service.add_speaker(
            #         name=feedback.user_provided_name,
            #         embedding=embedding,
            #         initial_confidence=0.6
            #     )
            #     new_speaker_added = True
            # else:
            #     await speaker_db_service.increase_confidence(
            #         speaker_name=feedback.user_provided_name,
            #         embedding=embedding,
            #         amount=0.15
            #     )
            message = f"Updated: '{feedback.suggested_name}' -> '{feedback.user_provided_name}'"

        else:
            # No suggestion, user provides name
            # TODO: Check if speaker exists
            # TODO: If not, create new speaker with initial confidence
            message = f"Added new speaker: '{feedback.user_provided_name}'"
            new_speaker_added = True

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": message,
                "new_speaker_added": new_speaker_added,
                "audio_clip_id": feedback.audio_clip_id
            }
        )

    except Exception as e:
        logger.error(f"Speaker feedback processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_known_speakers():
    """
    Get list of all known speakers in the database.

    **Returns:**
    - speakers: List of speaker names with their average confidence scores
    - total_count: Total number of known speakers
    """

    try:
        # TODO: Get speakers from database
        # speakers = await speaker_db_service.get_all_speakers()

        # PLACEHOLDER
        speakers = []

        return JSONResponse(
            status_code=200,
            content={
                "speakers": speakers,
                "total_count": len(speakers)
            }
        )

    except Exception as e:
        logger.error(f"Failed to list speakers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/speaker/{speaker_name}")
async def delete_speaker(speaker_name: str):
    """
    Delete a speaker from the database.

    **Parameters:**
    - speaker_name: Name of speaker to delete

    **Returns:**
    - success: True if deleted
    - message: Confirmation message
    """

    try:
        # TODO: Delete speaker from database
        # await speaker_db_service.delete_speaker(speaker_name)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Deleted speaker: {speaker_name}"
            }
        )

    except Exception as e:
        logger.error(f"Failed to delete speaker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
