"""TranscribeMS MCP Server package.

This package contains the Model Context Protocol server implementation
for TranscribeMS audio transcription service.
"""

from .server import TranscribeMSServer, main

__all__ = ['TranscribeMSServer', 'main']