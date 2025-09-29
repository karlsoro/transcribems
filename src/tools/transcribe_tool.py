"""Transcribe audio MCP tool with GPU-Enhanced SimpleWhisperXCLI.

This tool handles audio file transcription using our GPU-accelerated service.
It validates files, processes them through the GPU-enhanced transcription adapter,
and returns job status information with performance metrics.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..services.mcp_transcription_adapter import MCPTranscriptionAdapter
from ..models.types import TranscriptionSettings, JobStatus
from ..error_handler import MCPErrorHandler

logger = logging.getLogger(__name__)

# Initialize GPU-enhanced services
transcription_adapter = MCPTranscriptionAdapter()
error_handler = MCPErrorHandler()

async def transcribe_audio_tool(request: dict) -> dict:
    """MCP tool for GPU-enhanced audio transcription.

    Args:
        request: MCP request containing:
            - file_path: Path to audio file
            - model_size: WhisperX model size (tiny, base, small, medium, large)
            - language: Language code (optional, auto-detect if None)
            - enable_diarization: Enable speaker diarization
            - output_format: Output format preference
            - device: Processing device (auto-detected: cuda if available, else cpu)
            - compute_type: Compute type (auto-optimized based on device)

    Returns:
        dict: Job status and information with GPU performance metrics
    """
    try:
        # Extract and validate file path
        file_path = request.get('file_path')
        if not file_path:
            return error_handler.file_not_found("file_path parameter is required")

        # Validate file exists
        if not Path(file_path).exists():
            return error_handler.file_not_found(f"Audio file not found: {file_path}")

        # Get file size for estimates
        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

        # Create transcription settings (optimized for GPU)
        settings = TranscriptionSettings(
            model_size=request.get('model_size', 'base'),
            language=request.get('language'),  # None for auto-detect
            enable_diarization=request.get('enable_diarization', True),
            output_format=request.get('output_format', 'detailed'),
            # Device and compute_type will be auto-detected by SimpleWhisperXCLI
            device=request.get('device'),  # Optional override
            compute_type=request.get('compute_type'),  # Optional override
            chunk_length=request.get('chunk_length', 30),
            beam_size=request.get('beam_size', 5),
            temperature=request.get('temperature', 0.0)
        )

        logger.info(f"Starting transcription: {file_path} ({file_size_mb:.1f}MB)")
        logger.info(f"Settings: model={settings.model_size}, diarization={settings.enable_diarization}")

        # Start transcription using GPU-enhanced adapter
        job = await transcription_adapter.transcribe_audio(
            file_path=file_path,
            settings=settings
        )

        # Get system info for response
        system_info = transcription_adapter.get_system_info()

        # Return enhanced job status with GPU info
        return {
            "success": True,
            "job_id": job.job_id,
            "status": job.status.value,
            "file_path": file_path,
            "file_size_mb": file_size_mb,
            "settings": {
                "model_size": settings.model_size,
                "language": settings.language,
                "enable_diarization": settings.enable_diarization,
                "auto_optimization": True
            },
            "system_info": {
                "gpu_available": system_info["gpu_available"],
                "service_type": system_info["service_type"],
                "device_auto_detected": True
            },
            "created_at": job.created_at.isoformat(),
            "message": f"Transcription started using {'GPU' if system_info['gpu_available'] else 'CPU'} acceleration"
        }

    except Exception as e:
        logger.error(f"GPU-enhanced transcription tool error: {e}")
        return error_handler.internal_error(f"Transcription failed: {str(e)}")

# Set function name for tests
transcribe_audio_tool.__name__ = 'transcribe_audio_tool'