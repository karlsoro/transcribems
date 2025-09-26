"""Result retrieval MCP tool.

This tool retrieves completed transcription results with various
formatting options and detailed information.
"""

import logging
from typing import Dict, Any, Optional

from ..services.storage_service import StorageService
from ..services.history_service import HistoryService
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize services
storage_service = StorageService()
history_service = HistoryService(storage_service)
error_handler = MCPErrorHandler()

async def get_transcription_result_tool(request: dict) -> dict:
    """MCP tool for retrieving transcription results.

    Args:
        request: MCP request containing:
            - job_id: Job ID to get results for
            - format: Output format (text, segments, full, summary)
            - include_metadata: Include processing metadata
            - include_timestamps: Include word-level timestamps
            - include_confidence: Include confidence scores
            - include_speakers: Include speaker information

    Returns:
        dict: Transcription result data
    """
    try:
        job_id = request.get('job_id')
        if not job_id:
            return error_handler.invalid_parameters("job_id parameter is required")

        output_format = request.get('format', 'full')
        include_metadata = request.get('include_metadata', True)
        include_timestamps = request.get('include_timestamps', True)
        include_confidence = request.get('include_confidence', True)
        include_speakers = request.get('include_speakers', True)

        # Load job to check status
        job = await storage_service.load_job(job_id)
        if not job:
            return error_handler.job_not_found(f"Job {job_id} not found")

        # Check if job is completed
        if job.status.value != "completed":
            return {
                "success": False,
                "error": {
                    "code": "JOB_NOT_COMPLETED",
                    "message": f"Job {job_id} is not completed (status: {job.status.value})",
                    "current_status": job.status.value,
                    "progress": job.progress
                }
            }

        # Load result
        result = await storage_service.load_result(job_id)
        if not result:
            return error_handler.result_not_found(f"Result for job {job_id} not found")

        # Get job summary for additional context
        job_summary = await history_service.get_job_summary(job_id)

        # Format response based on requested format
        if output_format == "text":
            response_data = {
                "text": result.text,
                "word_count": result.word_count,
                "language": result.language
            }

        elif output_format == "summary":
            response_data = {
                "job_id": job_id,
                "text": result.text,
                "word_count": result.word_count,
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time,
                "language": result.language,
                "speaker_count": len(result.speakers),
                "segment_count": len(result.segments)
            }

        elif output_format == "segments":
            segments_data = []
            for segment in result.segments:
                seg_data = {
                    "id": segment.segment_id,
                    "text": segment.text,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time
                }

                if include_confidence:
                    seg_data["confidence"] = segment.confidence

                if include_speakers and segment.speaker_id:
                    seg_data["speaker_id"] = segment.speaker_id

                if include_timestamps and segment.words:
                    seg_data["words"] = [
                        {
                            "word": word.word,
                            "start_time": word.start_time,
                            "end_time": word.end_time,
                            "confidence": word.confidence if include_confidence else None
                        }
                        for word in segment.words
                    ]

                segments_data.append(seg_data)

            response_data = {
                "segments": segments_data,
                "segment_count": len(segments_data)
            }

        else:  # full format
            response_data = {
                "job_id": job_id,
                "text": result.text,
                "segments": [
                    {
                        "id": seg.segment_id,
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                        "confidence": seg.confidence if include_confidence else None,
                        "speaker_id": seg.speaker_id if include_speakers else None,
                        "language": seg.language,
                        "words": [
                            {
                                "word": w.word,
                                "start_time": w.start_time,
                                "end_time": w.end_time,
                                "confidence": w.confidence if include_confidence else None,
                                "probability": w.probability if include_confidence else None
                            }
                            for w in seg.words
                        ] if include_timestamps else None
                    }
                    for seg in result.segments
                ],
                "speakers": [
                    {
                        "speaker_id": speaker.speaker_id,
                        "label": speaker.speaker_label,
                        "total_speech_time": speaker.total_speech_time,
                        "segment_count": speaker.segment_count,
                        "confidence": speaker.confidence if include_confidence else None,
                        "characteristics": speaker.characteristics
                    }
                    for speaker in result.speakers
                ] if include_speakers else [],
                "confidence_score": result.confidence_score,
                "processing_time": result.processing_time,
                "model_version": result.model_version,
                "language": result.language,
                "word_count": result.word_count
            }

        # Add metadata if requested
        if include_metadata and result.metadata:
            response_data["metadata"] = {
                "whisperx_version": result.metadata.whisperx_version,
                "model_path": result.metadata.model_path,
                "device_used": result.metadata.device_used,
                "memory_usage": result.metadata.memory_usage,
                "chunks_processed": result.metadata.chunks_processed,
                "diarization_enabled": result.metadata.diarization_enabled,
                "preprocessing_time": result.metadata.preprocessing_time,
                "inference_time": result.metadata.inference_time,
                "postprocessing_time": result.metadata.postprocessing_time
            }

        # Add job summary if available
        if job_summary:
            response_data["job_info"] = job_summary

        return {
            "success": True,
            "result": response_data
        }

    except Exception as e:
        logger.error(f"Result tool error: {e}")
        return error_handler.internal_error(f"Result retrieval failed: {str(e)}")

get_transcription_result_tool.__name__ = 'get_transcription_result_tool'