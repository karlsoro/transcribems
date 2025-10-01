"""TranscribeMCP MCP Server.

This module implements the Model Context Protocol server for TranscribeMCP,
providing audio transcription capabilities through standardized MCP tools.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

try:
    from mcp.server import FastMCP
except ImportError:
    # Fallback for development without MCP SDK installed
    class MockServer:
        def __init__(self, name: str, version: str): pass
        def tool(self): return lambda fn: fn
        async def run_stdio_async(self): pass
        async def run_sse_async(self): pass
        async def run_streamable_http_async(self): pass

    FastMCP = MockServer

from ..tools.transcribe_tool import transcribe_audio_tool
from ..tools.progress_tool import get_transcription_progress_tool
from ..tools.history_tool import list_transcription_history_tool
from ..tools.result_tool import get_transcription_result_tool
from ..tools.batch_tool import batch_transcribe_tool
from ..tools.cancel_tool import cancel_transcription_tool

logger = logging.getLogger(__name__)

class TranscribeMCPServer:
    """TranscribeMCP MCP Server implementation."""

    def __init__(self):
        """Initialize the MCP server."""
        self.server = FastMCP("transcribe_mcp")
        self._setup_tools()

    def _setup_tools(self):
        """Register all MCP tools with the server."""

        # Transcribe audio tool
        @self.server.tool()
        async def transcribe_audio(
            file_path: str,
            model_size: str = "base",
            language: str = None,
            enable_diarization: bool = True,
            output_format: str = "detailed",
            device: str = None,
            compute_type: str = None
        ) -> dict:
            """Transcribe audio file using WhisperX with speaker diarization"""
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

        # Progress tracking tool
        @self.server.tool()
        async def get_transcription_progress(
            job_id: str = None,
            all_jobs: bool = False
        ) -> dict:
            """Get progress information for transcription jobs"""
            request = {
                'job_id': job_id,
                'all_jobs': all_jobs
            }
            return await get_transcription_progress_tool(request)

        # History tool
        @self.server.tool()
        async def list_transcription_history(
            limit: int = 10,
            status_filter: str = None,
            date_from: str = None,
            date_to: str = None,
            search_query: str = None,
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

        # Result retrieval tool
        @self.server.tool()
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

        # Batch transcription tool
        @self.server.tool()
        async def batch_transcribe(
            file_paths: list[str],
            model_size: str = "base",
            language: str = None,
            enable_diarization: bool = True,
            output_format: str = "detailed",
            device: str = "cpu",
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

        # Cancellation tool
        @self.server.tool()
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

        logger.info("All MCP tools registered successfully")

    async def run_stdio(self):
        """Run the MCP server in stdio mode (for Claude Desktop)."""
        try:
            logger.info("Starting TranscribeMCP MCP Server in stdio mode...")
            await self.server.run_stdio_async()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

    async def run_sse(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the MCP server in SSE HTTP mode.

        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        try:
            logger.info(f"Starting TranscribeMCP MCP Server in SSE mode on {host}:{port}...")
            # Configure server settings for HTTP mode
            self.server.settings.host = host
            self.server.settings.port = port
            await self.server.run_sse_async()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

    async def run_streamable_http(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the MCP server in StreamableHTTP mode.

        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        try:
            logger.info(f"Starting TranscribeMCP MCP Server in StreamableHTTP mode on {host}:{port}...")
            # Configure server settings for HTTP mode
            self.server.settings.host = host
            self.server.settings.port = port
            await self.server.run_streamable_http_async()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

    async def run(self):
        """Run the MCP server in stdio mode (default, for backward compatibility)."""
        await self.run_stdio()

def main():
    """Main entry point for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    server = TranscribeMCPServer()

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        raise

if __name__ == "__main__":
    main()