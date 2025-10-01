"""
TranscribeMCP FastMCP Server.

A simplified MCP server implementation using FastMCP for GPU-enhanced audio transcription.
"""

import asyncio
import logging
from typing import Optional

try:
    from mcp.server import FastMCP
except ImportError:
    # Fallback for development
    class FastMCP:
        def __init__(self, name: str): pass
        def tool(self): pass
        async def run_stdio_async(self): pass

from ..tools.transcribe_tool import transcribe_audio_tool
from ..tools.progress_tool import get_transcription_progress_tool
from ..tools.result_tool import get_transcription_result_tool
from ..tools.history_tool import list_transcription_history_tool
from ..tools.batch_tool import batch_transcribe_tool
from ..tools.cancel_tool import cancel_transcription_tool

logger = logging.getLogger(__name__)

# Create FastMCP server
server = FastMCP("transcribe_mcp")

@server.tool()
async def transcribe_audio(
    file_path: str,
    model_size: str = "base",
    language: Optional[str] = None,
    enable_diarization: bool = True,
    output_format: str = "detailed",
    device: Optional[str] = None,
    compute_type: Optional[str] = None
) -> dict:
    """Transcribe audio file using GPU-enhanced WhisperX with speaker diarization"""
    request = {
        'file_path': file_path,
        'model_size': model_size,
        'language': language,
        'enable_diarization': enable_diarization,
        'output_format': output_format,
        'device': device,
        'compute_type': compute_type
    }
    return await transcribe_audio_tool(request)

@server.tool()
async def get_transcription_progress(
    job_id: Optional[str] = None,
    all_jobs: bool = False
) -> dict:
    """Get progress information for transcription jobs with GPU performance metrics"""
    request = {
        'job_id': job_id,
        'all_jobs': all_jobs
    }
    return await get_transcription_progress_tool(request)

@server.tool()
async def get_transcription_result(
    job_id: str,
    format: str = "full",
    include_metadata: bool = True,
    include_timestamps: bool = True,
    include_confidence: bool = True,
    include_speakers: bool = True
) -> dict:
    """Retrieve transcription results with various formatting options"""
    request = {
        'job_id': job_id,
        'format': format,
        'include_metadata': include_metadata,
        'include_timestamps': include_timestamps,
        'include_confidence': include_confidence,
        'include_speakers': include_speakers
    }
    return await get_transcription_result_tool(request)

@server.tool()
async def list_transcription_history(
    limit: int = 10,
    status_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search_query: Optional[str] = None,
    get_statistics: bool = False,
    statistics_days: int = 30
) -> dict:
    """List transcription history with filtering and search capabilities"""
    request = {
        'limit': limit,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'get_statistics': get_statistics,
        'statistics_days': statistics_days
    }
    return await list_transcription_history_tool(request)

@server.tool()
async def batch_transcribe(
    file_paths: list,
    model_size: str = "base",
    language: Optional[str] = None,
    enable_diarization: bool = True,
    output_format: str = "detailed",
    device: Optional[str] = None,
    max_concurrent: int = 3
) -> dict:
    """Transcribe multiple audio files with shared settings"""
    request = {
        'file_paths': file_paths,
        'model_size': model_size,
        'language': language,
        'enable_diarization': enable_diarization,
        'output_format': output_format,
        'device': device,
        'max_concurrent': max_concurrent
    }
    return await batch_transcribe_tool(request)

@server.tool()
async def cancel_transcription(
    job_id: str,
    reason: str = "Cancelled by user"
) -> dict:
    """Cancel in-progress transcription jobs"""
    request = {
        'job_id': job_id,
        'reason': reason
    }
    return await cancel_transcription_tool(request)

def main():
    """Main entry point for the FastMCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting TranscribeMCP FastMCP Server...")

    try:
        asyncio.run(server.run_stdio_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise

if __name__ == "__main__":
    main()