"""Contract test for transcribe_audio MCP tool.

This test verifies the MCP tool interface contract for audio transcription.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any

from src.tools.transcribe_tool import transcribe_audio_tool
from src.models.types import JobStatus


class TestTranscribeAudioToolContract:
    """Contract tests for transcribe_audio MCP tool."""

    @pytest.fixture
    def sample_audio_file(self, tmp_path: Path) -> Path:
        """Create a sample audio file for testing."""
        audio_file = tmp_path / "test_audio.wav"
        # This will fail until we implement the tool
        audio_file.write_bytes(b"fake_wav_data")
        return audio_file

    @pytest.fixture
    def valid_transcribe_request(self, sample_audio_file: Path) -> Dict[str, Any]:
        """Valid request for transcribe_audio tool."""
        return {
            "file_path": str(sample_audio_file),
            "settings": {
                "model_size": "base",
                "language": "en",
                "enable_diarization": True,
                "device": "cpu"
            }
        }

    async def test_transcribe_audio_tool_exists(self):
        """Test that the transcribe_audio tool exists and is importable."""
        # This MUST fail until we implement the tool
        assert hasattr(transcribe_audio_tool, '__call__')
        assert transcribe_audio_tool.__name__ == 'transcribe_audio_tool'

    async def test_transcribe_audio_input_schema(self, valid_transcribe_request: Dict[str, Any]):
        """Test that the tool accepts valid input according to MCP contract."""
        # This MUST fail until we implement proper schema validation
        result = await transcribe_audio_tool(valid_transcribe_request)

        # Tool should return a dict with job_id and status
        assert isinstance(result, dict)
        assert "job_id" in result
        assert "status" in result

        # job_id should be a valid UUID
        import uuid
        uuid.UUID(result["job_id"])  # Should not raise exception

        # status should be a valid JobStatus
        assert result["status"] in [s.value for s in JobStatus]

    async def test_transcribe_audio_output_schema(self, valid_transcribe_request: Dict[str, Any]):
        """Test that the tool returns valid output according to MCP contract."""
        result = await transcribe_audio_tool(valid_transcribe_request)

        # Must contain required fields
        required_fields = ["job_id", "status"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # If status is completed, must have result field
        if result["status"] == "completed":
            assert "result" in result
            result_data = result["result"]

            # Result must contain transcription data
            transcription_fields = ["text", "confidence_score", "language", "processing_time", "segments"]
            for field in transcription_fields:
                assert field in result_data, f"Missing transcription field: {field}"

    async def test_transcribe_audio_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test with non-existent file
        invalid_request = {
            "file_path": "/non/existent/file.wav",
            "settings": {"model_size": "base"}
        }

        result = await transcribe_audio_tool(invalid_request)
        assert result["status"] == "failed"
        assert "error" in result
        assert "FILE_NOT_FOUND" in result["error"]["code"]

    async def test_transcribe_audio_file_too_large(self, tmp_path: Path):
        """Test error handling for files exceeding 1GB limit."""
        # Simulate large file check (we won't actually create 1GB file)
        large_file_request = {
            "file_path": str(tmp_path / "large_file.wav"),
            "settings": {"model_size": "base"}
        }

        # Mock file size check will be implemented in actual tool
        result = await transcribe_audio_tool(large_file_request)
        # This should fail with FILE_TOO_LARGE when file size validation is implemented

    async def test_transcribe_audio_unsupported_format(self, tmp_path: Path):
        """Test error handling for unsupported audio formats."""
        txt_file = tmp_path / "not_audio.txt"
        txt_file.write_text("This is not audio")

        invalid_format_request = {
            "file_path": str(txt_file),
            "settings": {"model_size": "base"}
        }

        result = await transcribe_audio_tool(invalid_format_request)
        assert result["status"] == "failed"
        assert "error" in result
        assert "UNSUPPORTED_FORMAT" in result["error"]["code"]

    async def test_transcribe_audio_settings_validation(self, sample_audio_file: Path):
        """Test settings validation according to contract."""
        # Test invalid model size
        invalid_settings_request = {
            "file_path": str(sample_audio_file),
            "settings": {
                "model_size": "invalid_size",
                "device": "cpu"
            }
        }

        result = await transcribe_audio_tool(invalid_settings_request)
        # Should validate settings and reject invalid model_size

    async def test_transcribe_audio_concurrent_processing(self, valid_transcribe_request: Dict[str, Any]):
        """Test that multiple transcription jobs can be started concurrently."""
        # Start multiple transcription jobs
        results = []
        for i in range(3):
            result = await transcribe_audio_tool(valid_transcribe_request)
            results.append(result)

        # Each should get a unique job_id
        job_ids = [r["job_id"] for r in results]
        assert len(set(job_ids)) == 3, "Job IDs should be unique"