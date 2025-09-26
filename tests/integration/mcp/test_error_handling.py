"""Integration test for error handling and recovery scenario."""

import pytest
from src.mcp_server.server import MCPServer


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""

    async def test_error_handling_workflow(self):
        """Test error handling as per quickstart scenario 4."""
        # This MUST fail until MCP server is implemented
        server = MCPServer()

        # Test non-existent file
        result = await server.call_tool("transcribe_audio", {
            "file_path": "nonexistent.mp3"
        })

        assert "error" in result
        assert "FILE_NOT_FOUND" in result["error"]["code"]