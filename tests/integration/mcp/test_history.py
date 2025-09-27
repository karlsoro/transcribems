"""Integration test for transcription history scenario."""

from src.mcp_server.server import MCPServer


class TestHistoryIntegration:
    """Integration tests for transcription history management."""

    async def test_history_workflow(self):
        """Test history retrieval as per quickstart scenario 5."""
        # This MUST fail until MCP server is implemented
        server = MCPServer()

        # Get history
        result = await server.call_tool("list_transcription_history", {
            "limit": 10
        })

        assert "jobs" in result
        assert "total_count" in result
