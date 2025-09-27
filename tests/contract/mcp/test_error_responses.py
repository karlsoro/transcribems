"""Contract test for MCP error responses.

This test verifies that error responses follow the MCP error schema.
Tests MUST FAIL before implementation - this is TDD.
"""


from src.error_handler import MCPErrorHandler


class TestMCPErrorResponsesContract:
    """Contract tests for MCP error response structure."""

    async def test_error_handler_exists(self):
        """Test that the MCP error handler exists."""
        # This MUST fail until we implement the error handler
        assert MCPErrorHandler is not None

    async def test_file_not_found_error_structure(self):
        """Test FILE_NOT_FOUND error response structure."""
        handler = MCPErrorHandler()
        error = handler.file_not_found("/non/existent/file.wav")

        assert "error" in error
        assert "code" in error["error"]
        assert "message" in error["error"]
        assert "details" in error["error"]

        assert error["error"]["code"] == "FILE_NOT_FOUND"
        assert "error_type" in error["error"]["details"]
        assert "user_action" in error["error"]["details"]

    async def test_file_too_large_error_structure(self):
        """Test FILE_TOO_LARGE error response structure."""
        handler = MCPErrorHandler()
        error = handler.file_too_large("/large/file.wav", 2000000000)

        assert error["error"]["code"] == "FILE_TOO_LARGE"
        assert "max_size_bytes" in error["error"]["details"]
        assert error["error"]["details"]["max_size_bytes"] == 1073741824

    async def test_unsupported_format_error_structure(self):
        """Test UNSUPPORTED_FORMAT error response structure."""
        handler = MCPErrorHandler()
        error = handler.unsupported_format("/file.txt")

        assert error["error"]["code"] == "UNSUPPORTED_FORMAT"
        assert "supported_formats" in error["error"]["details"]
        expected_formats = ["MP3", "WAV", "M4A", "OGG", "FLAC", "AAC", "WMA"]
        assert error["error"]["details"]["supported_formats"] == expected_formats

    async def test_job_not_found_error_structure(self):
        """Test JOB_NOT_FOUND error response structure."""
        handler = MCPErrorHandler()
        error = handler.job_not_found("invalid-job-id")

        assert error["error"]["code"] == "JOB_NOT_FOUND"
        assert error["error"]["details"]["error_type"] == "not_found_error"

    async def test_transcription_failed_error_structure(self):
        """Test TRANSCRIPTION_FAILED error response structure."""
        handler = MCPErrorHandler()
        error = handler.transcription_failed("Model failed to process audio")

        assert error["error"]["code"] == "TRANSCRIPTION_FAILED"
        assert error["error"]["details"]["error_type"] == "processing_error"
