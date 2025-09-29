"""Result retrieval MCP tool for GPU-enhanced transcription.

This tool retrieves completed transcription results with performance metrics
and various formatting options from GPU-accelerated processing.
"""

import logging
from typing import Dict, Any, Optional

from ..services.mcp_transcription_adapter import MCPTranscriptionAdapter
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize GPU-enhanced services
transcription_adapter = MCPTranscriptionAdapter()
error_handler = MCPErrorHandler()

async def get_transcription_result_tool(request: dict) -> dict:
    """MCP tool for retrieving GPU-enhanced transcription results.

    Args:
        request: MCP request containing:
            - job_id: Job ID to get results for
            - format: Output format (text, segments, full, summary)
            - include_metadata: Include processing metadata
            - include_timestamps: Include word-level timestamps
            - include_confidence: Include confidence scores
            - include_speakers: Include speaker information

    Returns:
        dict: Transcription result data with GPU performance metrics
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

        # Get result from GPU-enhanced adapter
        result = transcription_adapter.get_job_result(job_id)

        if not result:
            return error_handler.result_not_found(f"Result for job {job_id} not found or not completed")

        if result.get("status") != "completed":
            return {
                "success": False,
                "error": {
                    "code": "JOB_NOT_COMPLETED",
                    "message": f"Job {job_id} is not completed",
                    "current_status": result.get("status", "unknown")
                }
            }

        result_data = result.get("result", {})

        # Format response based on requested format
        if output_format == "text":
            response_data = {
                "text": result_data.get("text", ""),
                "word_count": result_data.get("word_count", 0),
                "language": result_data.get("language", "unknown")
            }

        elif output_format == "summary":
            response_data = {
                "job_id": job_id,
                "text": result_data.get("text", ""),
                "word_count": result_data.get("word_count", 0),
                "confidence_score": result_data.get("confidence_score", 0.0),
                "processing_time": result_data.get("processing_time", 0.0),
                "language": result_data.get("language", "unknown"),
                "speaker_count": len(result_data.get("speakers", [])),
                "segment_count": len(result_data.get("segments", []))
            }

        elif output_format == "segments":
            segments_data = []
            for segment in result_data.get("segments", []):
                seg_data = {
                    "id": segment.get("segment_id"),
                    "text": segment.get("text"),
                    "start_time": segment.get("start_time"),
                    "end_time": segment.get("end_time")
                }

                if include_confidence:
                    seg_data["confidence"] = segment.get("confidence")

                if include_speakers:
                    seg_data["speaker_id"] = segment.get("speaker_id")

                segments_data.append(seg_data)

            response_data = {
                "segments": segments_data,
                "segment_count": len(segments_data)
            }

        else:  # full format
            response_data = {
                "job_id": job_id,
                "text": result_data.get("text", ""),
                "segments": result_data.get("segments", []) if include_timestamps else [],
                "speakers": result_data.get("speakers", []) if include_speakers else [],
                "confidence_score": result_data.get("confidence_score", 0.0),
                "processing_time": result_data.get("processing_time", 0.0),
                "language": result_data.get("language", "unknown"),
                "word_count": result_data.get("word_count", 0)
            }

        # Add GPU performance metadata if requested
        if include_metadata and "metadata" in result_data:
            metadata = result_data["metadata"]
            response_data["metadata"] = {
                "whisperx_version": metadata.get("whisperx_version"),
                "device_used": metadata.get("device_used"),
                "gpu_available": metadata.get("gpu_available"),
                "realtime_factor": metadata.get("realtime_factor"),
                "file_size_mb": metadata.get("file_size_mb"),
                "audio_duration": metadata.get("audio_duration"),
                "model_size": metadata.get("model_size"),
                "diarization_enabled": metadata.get("diarization_enabled"),
                "chunks_processed": metadata.get("chunks_processed")
            }

        return {
            "success": True,
            "result": response_data
        }

    except Exception as e:
        logger.error(f"GPU-enhanced result tool error: {e}")
        return error_handler.internal_error(f"Result retrieval failed: {str(e)}")

get_transcription_result_tool.__name__ = 'get_transcription_result_tool'