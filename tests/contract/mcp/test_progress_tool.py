"""Contract test for get_transcription_progress MCP tool.

This test verifies the MCP tool interface contract for progress tracking.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
import uuid
from typing import Dict, Any

from src.tools.progress_tool import get_transcription_progress_tool
from src.models.types import JobStatus


class TestTranscriptionProgressToolContract:
    """Contract tests for get_transcription_progress MCP tool."""

    @pytest.fixture
    def valid_job_id(self) -> str:
        """Generate a valid job ID for testing."""
        return str(uuid.uuid4())

    @pytest.fixture
    def progress_request(self, valid_job_id: str) -> Dict[str, str]:
        """Valid request for progress tool."""
        return {"job_id": valid_job_id}

    async def test_progress_tool_exists(self):
        """Test that the progress tool exists and is importable."""
        # This MUST fail until we implement the tool
        assert hasattr(get_transcription_progress_tool, '__call__')
        assert get_transcription_progress_tool.__name__ == 'get_transcription_progress_tool'

    async def test_progress_tool_input_schema(self, progress_request: Dict[str, str]):
        """Test that the tool accepts valid input according to MCP contract."""
        # This MUST fail until we implement schema validation
        result = await get_transcription_progress_tool(progress_request)

        assert isinstance(result, dict)
        assert "job_id" in result
        assert "status" in result
        assert "progress" in result

    async def test_progress_tool_output_schema(self, progress_request: Dict[str, str]):
        """Test that the tool returns valid output according to MCP contract."""
        result = await get_transcription_progress_tool(progress_request)

        # Required fields
        required_fields = ["job_id", "status", "progress"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Validate types and ranges
        assert isinstance(result["job_id"], str)
        assert result["status"] in [s.value for s in JobStatus]
        assert isinstance(result["progress"], (int, float))
        assert 0.0 <= result["progress"] <= 1.0

    async def test_progress_tool_processing_status(self, progress_request: Dict[str, str]):
        """Test progress tool output when job is processing."""
        result = await get_transcription_progress_tool(progress_request)

        if result["status"] == "processing":
            # Should include progress details
            assert "current_chunk" in result
            assert "total_chunks" in result
            assert isinstance(result["current_chunk"], int)
            assert isinstance(result["total_chunks"], int)
            assert result["current_chunk"] <= result["total_chunks"]

    async def test_progress_tool_estimated_time(self, progress_request: Dict[str, str]):
        """Test estimated remaining time in progress response."""
        result = await get_transcription_progress_tool(progress_request)

        if result["status"] == "processing" and result["progress"] > 0:
            # May include estimated remaining time
            if "estimated_remaining" in result:
                assert isinstance(result["estimated_remaining"], (int, float))
                assert result["estimated_remaining"] >= 0

    async def test_progress_tool_job_not_found(self):
        """Test error handling for non-existent job ID."""
        non_existent_request = {"job_id": str(uuid.uuid4())}

        result = await get_transcription_progress_tool(non_existent_request)
        assert "error" in result
        assert "JOB_NOT_FOUND" in result["error"]["code"]

    async def test_progress_tool_invalid_job_id(self):
        """Test error handling for invalid job ID format."""
        invalid_request = {"job_id": "not-a-valid-uuid"}

        result = await get_transcription_progress_tool(invalid_request)
        assert "error" in result
        # Should validate UUID format

    async def test_progress_tool_completed_job(self, progress_request: Dict[str, str]):
        """Test progress tool response for completed job."""
        result = await get_transcription_progress_tool(progress_request)

        if result["status"] == "completed":
            assert result["progress"] == 1.0
            # Completed jobs should not have current_chunk info

    async def test_progress_tool_failed_job(self, progress_request: Dict[str, str]):
        """Test progress tool response for failed job."""
        result = await get_transcription_progress_tool(progress_request)

        if result["status"] == "failed":
            assert "error_message" in result
            assert isinstance(result["error_message"], str)

    async def test_progress_tool_cancelled_job(self, progress_request: Dict[str, str]):
        """Test progress tool response for cancelled job."""
        result = await get_transcription_progress_tool(progress_request)

        if result["status"] == "cancelled":
            # Progress should be preserved at cancellation point
            assert 0.0 <= result["progress"] <= 1.0