"""Contract test for batch_transcribe MCP tool.

This test verifies the MCP tool interface contract for batch transcription.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List

from src.tools.batch_tool import batch_transcribe_tool


class TestBatchTranscribeToolContract:
    """Contract tests for batch_transcribe MCP tool."""

    @pytest.fixture
    def sample_audio_files(self, tmp_path: Path) -> List[Path]:
        """Create sample audio files for batch testing."""
        files = []
        for i in range(3):
            file_path = tmp_path / f"audio_{i}.wav"
            file_path.write_bytes(b"fake_wav_data")
            files.append(file_path)
        return files

    @pytest.fixture
    def batch_request(self, sample_audio_files: List[Path]) -> Dict[str, Any]:
        """Valid batch transcription request."""
        return {
            "file_paths": [str(f) for f in sample_audio_files],
            "settings": {
                "model_size": "base",
                "enable_diarization": True
            }
        }

    async def test_batch_tool_exists(self):
        """Test that the batch tool exists and is importable."""
        # This MUST fail until we implement the tool
        assert hasattr(batch_transcribe_tool, '__call__')

    async def test_batch_tool_output_schema(self, batch_request: Dict[str, Any]):
        """Test batch tool output structure."""
        result = await batch_transcribe_tool(batch_request)

        assert "batch_id" in result
        assert "jobs" in result
        assert "total_jobs" in result
        assert len(result["jobs"]) == len(batch_request["file_paths"])

        for job in result["jobs"]:
            assert "job_id" in job
            assert "file_path" in job
            assert "status" in job

    async def test_batch_tool_size_limit(self):
        """Test batch size limit enforcement."""
        # Create request with too many files (>10)
        large_batch = {
            "file_paths": [f"/fake/file_{i}.wav" for i in range(15)],
            "settings": {"model_size": "base"}
        }

        result = await batch_transcribe_tool(large_batch)
        assert "error" in result
        assert "BATCH_TOO_LARGE" in result["error"]["code"]