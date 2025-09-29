"""Contract test for cancel_transcription MCP tool.

This test verifies the MCP tool interface contract for transcription cancellation.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
import uuid
from typing import Dict

from src.tools.cancel_tool import cancel_transcription_tool


class TestCancelTranscriptionToolContract:
    """Contract tests for cancel_transcription MCP tool."""

    @pytest.fixture
    def cancel_request(self) -> Dict[str, str]:
        """Valid cancellation request."""
        return {"job_id": str(uuid.uuid4())}

    async def test_cancel_tool_exists(self):
        """Test that the cancel tool exists and is importable."""
        # This MUST fail until we implement the tool
        assert hasattr(cancel_transcription_tool, '__call__')

    async def test_cancel_tool_output_schema(self, cancel_request: Dict[str, str]):
        """Test cancel tool output structure."""
        result = await cancel_transcription_tool(cancel_request)

        required_fields = ["job_id", "status", "message"]
        for field in required_fields:
            assert field in result

        assert result["status"] in ["cancelled", "completed", "failed"]

    async def test_cancel_tool_job_not_found(self):
        """Test error handling for non-existent job."""
        request = {"job_id": str(uuid.uuid4())}
        result = await cancel_transcription_tool(request)
        assert "error" in result or result["status"] == "failed"
