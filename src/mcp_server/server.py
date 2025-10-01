"""TranscribeMCP MCP Server.

This module implements the Model Context Protocol server for TranscribeMCP,
providing audio transcription capabilities through standardized MCP tools.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

try:
    from mcp.server import FastMCP
    from mcp.types import Tool, TextContent
except ImportError:
    # Fallback for development without MCP SDK installed
    class MockServer:
        def __init__(self, name: str, version: str): pass
        def add_tool(self, *args, **kwargs): pass
        async def run_stdio_async(self): pass

    FastMCP = MockServer
    TextContent = dict
    Tool = dict

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
        self.server.add_tool(
            Tool(
                name="list_transcription_history",
                description="List transcription history with filtering and search capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Maximum number of entries to return"
                        },
                        "status_filter": {
                            "type": "string",
                            "enum": ["pending", "processing", "completed", "failed", "cancelled"],
                            "description": "Filter by job status"
                        },
                        "date_from": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Start date filter (ISO format)"
                        },
                        "date_to": {
                            "type": "string",
                            "format": "date-time",
                            "description": "End date filter (ISO format)"
                        },
                        "search_query": {
                            "type": "string",
                            "description": "Search in filenames"
                        },
                        "get_statistics": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include usage statistics"
                        },
                        "statistics_days": {
                            "type": "integer",
                            "default": 30,
                            "minimum": 1,
                            "maximum": 365,
                            "description": "Number of days for statistics"
                        }
                    }
                }
            ),
            list_transcription_history_tool
        )

        # Result retrieval tool
        self.server.add_tool(
            Tool(
                name="get_transcription_result",
                description="Retrieve transcription results with various formatting options",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job ID to get results for"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["text", "segments", "full", "summary"],
                            "default": "full",
                            "description": "Output format"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include processing metadata"
                        },
                        "include_timestamps": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include word-level timestamps"
                        },
                        "include_confidence": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include confidence scores"
                        },
                        "include_speakers": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include speaker information"
                        }
                    },
                    "required": ["job_id"]
                }
            ),
            get_transcription_result_tool
        )

        # Batch transcription tool
        self.server.add_tool(
            Tool(
                name="batch_transcribe",
                description="Transcribe multiple audio files with shared settings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 10,
                            "description": "List of audio file paths"
                        },
                        "model_size": {
                            "type": "string",
                            "enum": ["tiny", "base", "small", "medium", "large"],
                            "default": "base",
                            "description": "WhisperX model size for all files"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code (optional, auto-detect if not provided)"
                        },
                        "enable_diarization": {
                            "type": "boolean",
                            "default": True,
                            "description": "Enable speaker diarization"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["simple", "detailed", "segments"],
                            "default": "detailed",
                            "description": "Output format preference"
                        },
                        "device": {
                            "type": "string",
                            "enum": ["cpu", "cuda"],
                            "default": "cpu",
                            "description": "Processing device"
                        },
                        "max_concurrent": {
                            "type": "integer",
                            "default": 3,
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Maximum concurrent jobs"
                        }
                    },
                    "required": ["file_paths"]
                }
            ),
            batch_transcribe_tool
        )

        # Cancellation tool
        self.server.add_tool(
            Tool(
                name="cancel_transcription",
                description="Cancel in-progress transcription jobs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job ID to cancel"
                        },
                        "reason": {
                            "type": "string",
                            "default": "Cancelled by user",
                            "description": "Cancellation reason"
                        }
                    },
                    "required": ["job_id"]
                }
            ),
            cancel_transcription_tool
        )

        logger.info("All MCP tools registered successfully")

    async def run(self):
        """Run the MCP server."""
        try:
            logger.info("Starting TranscribeMCP MCP Server...")
            await self.server.run_stdio_async()
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

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