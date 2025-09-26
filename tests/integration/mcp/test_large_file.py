"""Integration test for large file with progress tracking scenario."""

import pytest
from pathlib import Path
from src.mcp_server.server import MCPServer


class TestLargeFileTranscriptionIntegration:
    """Integration tests for large file transcription with progress tracking."""

    @pytest.fixture
    def large_audio_file(self, tmp_path: Path) -> Path:
        """Create mock large audio file (>5 minutes)."""
        file_path = tmp_path / "interview_long.wav"
        # Simulate large file that would trigger progress updates
        file_path.write_bytes(b"large_audio_content" * 50000)
        return file_path

    async def test_large_file_progress_tracking(self, large_audio_file: Path):
        """Test progress tracking for large files as per quickstart scenario 2."""
        # This MUST fail until MCP server is implemented
        server = MCPServer()

        result = await server.call_tool("transcribe_audio", {
            "file_path": str(large_audio_file)
        })

        assert "job_id" in result
        # Should receive progress updates for files >5 minutes