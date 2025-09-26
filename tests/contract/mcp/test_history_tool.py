"""Contract test for list_transcription_history MCP tool.

This test verifies the MCP tool interface contract for transcription history.
Tests MUST FAIL before implementation - this is TDD.
"""

import pytest
from typing import Dict, Any, Optional

from src.tools.history_tool import list_transcription_history_tool
from src.models.types import JobStatus


class TestTranscriptionHistoryToolContract:
    """Contract tests for list_transcription_history MCP tool."""

    @pytest.fixture
    def default_history_request(self) -> Dict[str, Any]:
        """Default request for history tool."""
        return {"limit": 10}

    @pytest.fixture
    def filtered_history_request(self) -> Dict[str, Any]:
        """Filtered request for history tool."""
        return {
            "limit": 5,
            "status_filter": "completed"
        }

    async def test_history_tool_exists(self):
        """Test that the history tool exists and is importable."""
        # This MUST fail until we implement the tool
        assert hasattr(list_transcription_history_tool, '__call__')
        assert list_transcription_history_tool.__name__ == 'list_transcription_history_tool'

    async def test_history_tool_default_request(self, default_history_request: Dict[str, Any]):
        """Test that the tool accepts default request parameters."""
        # This MUST fail until we implement the tool
        result = await list_transcription_history_tool(default_history_request)

        assert isinstance(result, dict)
        assert "jobs" in result
        assert "total_count" in result
        assert isinstance(result["jobs"], list)
        assert isinstance(result["total_count"], int)

    async def test_history_tool_output_schema(self, default_history_request: Dict[str, Any]):
        """Test that the tool returns valid output according to MCP contract."""
        result = await list_transcription_history_tool(default_history_request)

        # Required top-level fields
        assert "jobs" in result
        assert "total_count" in result

        # Validate jobs list structure
        for job in result["jobs"]:
            required_job_fields = ["job_id", "file_path", "status", "started_at"]
            for field in required_job_fields:
                assert field in job, f"Missing required job field: {field}"

            # Validate field types
            assert isinstance(job["job_id"], str)
            assert isinstance(job["file_path"], str)
            assert job["status"] in [s.value for s in JobStatus]
            assert isinstance(job["started_at"], str)  # ISO datetime string

            # Optional fields with type validation
            if "completed_at" in job:
                assert isinstance(job["completed_at"], str)
            if "duration" in job:
                assert isinstance(job["duration"], (int, float))
            if "word_count" in job:
                assert isinstance(job["word_count"], int)

    async def test_history_tool_limit_parameter(self):
        """Test limit parameter functionality."""
        # Test various limit values
        for limit in [1, 5, 10, 50, 100]:
            request = {"limit": limit}
            result = await list_transcription_history_tool(request)

            assert len(result["jobs"]) <= limit
            assert result["total_count"] >= 0

    async def test_history_tool_status_filter(self, filtered_history_request: Dict[str, Any]):
        """Test status filtering functionality."""
        result = await list_transcription_history_tool(filtered_history_request)

        # All returned jobs should match the status filter
        for job in result["jobs"]:
            assert job["status"] == "completed"

    async def test_history_tool_invalid_status_filter(self):
        """Test error handling for invalid status filter."""
        invalid_request = {
            "limit": 10,
            "status_filter": "invalid_status"
        }

        result = await list_transcription_history_tool(invalid_request)
        # Should handle invalid status gracefully or return error

    async def test_history_tool_limit_bounds(self):
        """Test limit parameter boundary conditions."""
        # Test minimum limit
        min_request = {"limit": 1}
        result = await list_transcription_history_tool(min_request)
        assert len(result["jobs"]) <= 1

        # Test maximum limit
        max_request = {"limit": 100}
        result = await list_transcription_history_tool(max_request)
        assert len(result["jobs"]) <= 100

        # Test invalid limits
        invalid_limit_request = {"limit": 0}
        # Should handle invalid limits appropriately

    async def test_history_tool_empty_history(self):
        """Test behavior when no transcription history exists."""
        result = await list_transcription_history_tool({"limit": 10})

        assert result["total_count"] == 0
        assert result["jobs"] == []

    async def test_history_tool_job_ordering(self, default_history_request: Dict[str, Any]):
        """Test that jobs are returned in proper order (most recent first)."""
        result = await list_transcription_history_tool(default_history_request)

        if len(result["jobs"]) >= 2:
            # Jobs should be ordered by started_at descending
            for i in range(len(result["jobs"]) - 1):
                current_job = result["jobs"][i]
                next_job = result["jobs"][i + 1]
                # ISO datetime string comparison should work for proper ordering
                assert current_job["started_at"] >= next_job["started_at"]

    async def test_history_tool_pagination_consistency(self):
        """Test that pagination works consistently."""
        # Get first page
        page1 = await list_transcription_history_tool({"limit": 5})

        # Total count should be consistent across calls
        page2 = await list_transcription_history_tool({"limit": 10})

        # If we have jobs, total counts should match
        if page1["total_count"] > 0:
            assert page1["total_count"] == page2["total_count"]

    async def test_history_tool_completed_job_fields(self):
        """Test that completed jobs include all expected fields."""
        result = await list_transcription_history_tool({
            "limit": 10,
            "status_filter": "completed"
        })

        for job in result["jobs"]:
            if job["status"] == "completed":
                # Completed jobs should have completion time and duration
                assert "completed_at" in job
                assert "duration" in job
                # May have word count for completed transcriptions
                # assert "word_count" in job  # Optional for now