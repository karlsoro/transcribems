"""Contract test for get_transcription_result MCP tool.

This test verifies the MCP tool interface contract for retrieving transcription results.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
import uuid
from typing import Dict, Any

from src.tools.result_tool import get_transcription_result_tool


class TestTranscriptionResultToolContract:
    """Contract tests for get_transcription_result MCP tool."""

    @pytest.fixture
    def result_request(self) -> Dict[str, Any]:
        """Valid request for result tool."""
        return {
            "job_id": str(uuid.uuid4()),
            "format": "full"
        }

    async def test_result_tool_exists(self):
        """Test that the result tool exists and is importable."""
        # This MUST fail until we implement the tool
        assert hasattr(get_transcription_result_tool, '__call__')

    async def test_result_tool_full_format(self, result_request: Dict[str, Any]):
        """Test full format result retrieval."""
        result = await get_transcription_result_tool(result_request)

        if result["status"] == "completed":
            assert "result" in result
            result_data = result["result"]

            # Full format should include all transcription data
            expected_fields = [
                "text", "confidence_score", "language",
                "processing_time", "segments", "speakers", "metadata"
            ]
            for field in expected_fields:
                assert field in result_data

    async def test_result_tool_text_only_format(self):
        """Test text-only format result retrieval."""
        request = {
            "job_id": str(uuid.uuid4()),
            "format": "text_only"
        }
        result = await get_transcription_result_tool(request)

        if result["status"] == "completed":
            result_data = result["result"]
            assert "text" in result_data
            # Should not include segments, speakers, etc.

    async def test_result_tool_job_not_found(self):
        """Test error handling for non-existent job."""
        request = {"job_id": str(uuid.uuid4())}
        result = await get_transcription_result_tool(request)
        assert "error" in result
        assert "JOB_NOT_FOUND" in result["error"]["code"]
