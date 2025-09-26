"""Integration test for single audio file transcription scenario.

This test implements the quickstart scenario from the specification.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any

from src.mcp_server.server import MCPServer


class TestSingleFileTranscriptionIntegration:
    """Integration tests for single file transcription scenario."""

    @pytest.fixture
    async def mcp_server(self):
        """Create MCP server instance for testing."""
        # This MUST fail until we implement the MCP server
        server = MCPServer()
        await server.start()
        yield server
        await server.stop()

    @pytest.fixture
    def meeting_audio_file(self, tmp_path: Path) -> Path:
        """Create a mock meeting audio file."""
        audio_file = tmp_path / "meeting_2025_01_24.mp3"
        # Simulate real audio file with proper headers
        audio_file.write_bytes(b"fake_mp3_data_with_audio_content" * 1000)
        return audio_file

    async def test_single_file_transcription_workflow(
        self,
        mcp_server: MCPServer,
        meeting_audio_file: Path
    ):
        """Test complete workflow for single file transcription.

        This matches Scenario 1 from quickstart.md:
        1. User requests transcription of meeting_2025_01_24.mp3
        2. MCP tool processes the request
        3. User receives transcription with speaker identification
        """
        # Step 1: Request transcription
        transcribe_request = {
            "file_path": str(meeting_audio_file),
            "settings": {
                "model_size": "base",
                "enable_diarization": True
            }
        }

        result = await mcp_server.call_tool("transcribe_audio", transcribe_request)

        # Verify initial response
        assert result["status"] in ["processing", "completed"]
        assert "job_id" in result
        job_id = result["job_id"]

        # Step 2: Wait for processing if needed
        if result["status"] == "processing":
            # Poll for completion (with timeout)
            max_attempts = 30  # 30 seconds timeout
            attempt = 0

            while attempt < max_attempts:
                progress_result = await mcp_server.call_tool(
                    "get_transcription_progress",
                    {"job_id": job_id}
                )

                if progress_result["status"] == "completed":
                    break
                elif progress_result["status"] == "failed":
                    pytest.fail(f"Transcription failed: {progress_result.get('error_message')}")

                await asyncio.sleep(1)
                attempt += 1

            if attempt >= max_attempts:
                pytest.fail("Transcription timed out")

        # Step 3: Get final results
        final_result = await mcp_server.call_tool(
            "get_transcription_result",
            {"job_id": job_id, "format": "full"}
        )

        # Verify transcription results match expected schema
        assert final_result["status"] == "completed"
        assert "result" in final_result

        result_data = final_result["result"]
        required_fields = [
            "text", "confidence_score", "language",
            "processing_time", "segments", "speakers"
        ]

        for field in required_fields:
            assert field in result_data, f"Missing field: {field}"

        # Verify transcription content quality
        assert isinstance(result_data["text"], str)
        assert len(result_data["text"]) > 0
        assert 0.0 <= result_data["confidence_score"] <= 1.0
        assert isinstance(result_data["segments"], list)
        assert len(result_data["segments"]) > 0

        # Verify speaker diarization
        assert isinstance(result_data["speakers"], list)
        # Should have at least one speaker for non-empty audio

        # Verify segments have proper structure
        for segment in result_data["segments"]:
            assert "start_time" in segment
            assert "end_time" in segment
            assert "text" in segment
            assert "confidence" in segment
            assert segment["end_time"] > segment["start_time"]

    async def test_single_file_error_handling(self, mcp_server: MCPServer):
        """Test error handling in single file scenario."""
        # Test with non-existent file
        error_request = {
            "file_path": "/non/existent/meeting.mp3"
        }

        result = await mcp_server.call_tool("transcribe_audio", error_request)
        assert "error" in result
        assert "FILE_NOT_FOUND" in result["error"]["code"]

    async def test_single_file_progress_updates(
        self,
        mcp_server: MCPServer,
        meeting_audio_file: Path
    ):
        """Test progress updates during single file transcription."""
        # Start transcription
        transcribe_request = {
            "file_path": str(meeting_audio_file),
            "settings": {"model_size": "base"}
        }

        result = await mcp_server.call_tool("transcribe_audio", transcribe_request)
        job_id = result["job_id"]

        # Monitor progress updates
        progress_updates = []
        max_checks = 10

        for _ in range(max_checks):
            progress_result = await mcp_server.call_tool(
                "get_transcription_progress",
                {"job_id": job_id}
            )

            progress_updates.append(progress_result["progress"])

            if progress_result["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(0.5)

        # Verify progress increases monotonically
        for i in range(1, len(progress_updates)):
            assert progress_updates[i] >= progress_updates[i-1]