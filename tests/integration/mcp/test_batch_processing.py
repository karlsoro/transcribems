"""Integration test for batch processing scenario."""

import pytest
from pathlib import Path
from src.mcp_server.server import MCPServer


class TestBatchProcessingIntegration:
    """Integration tests for batch transcription processing."""

    async def test_batch_processing_workflow(self, tmp_path: Path):
        """Test batch processing as per quickstart scenario 3."""
        # This MUST fail until MCP server is implemented
        server = MCPServer()

        # Create multiple episode files
        files = []
        for i, ext in enumerate(["mp3", "mp3", "m4a"]):
            file_path = tmp_path / f"episode_{i+1:02d}.{ext}"
            file_path.write_bytes(b"episode_content" * 1000)
            files.append(str(file_path))

        result = await server.call_tool("batch_transcribe", {
            "file_paths": files
        })

        assert "batch_id" in result
        assert len(result["jobs"]) == 3