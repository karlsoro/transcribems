#!/usr/bin/env python3
"""
Test script to verify MCP server connectivity.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ MCP SDK not installed. Install with: pip install mcp")
    sys.exit(1)


async def test_mcp_server():
    """Test the TranscribeMCP MCP server connection and tools."""

    print("=" * 60)
    print("TranscribeMCP MCP Server Connection Test")
    print("=" * 60)
    print()

    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.mcp_server.fastmcp_server"],
        cwd=str(project_root),
        env={"PYTHONPATH": str(project_root)}
    )

    print("🔄 Connecting to MCP server...")
    print(f"   Command: python -m src.mcp_server.fastmcp_server")
    print(f"   Working directory: {project_root}")
    print()

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                print("🔄 Initializing session...")
                await session.initialize()
                print("✅ Session initialized successfully")
                print()

                # List available tools
                print("🔄 Listing available tools...")
                tools_response = await session.list_tools()

                if hasattr(tools_response, 'tools'):
                    tools = tools_response.tools
                else:
                    tools = tools_response

                print(f"✅ Found {len(tools)} tools:")
                print()

                for i, tool in enumerate(tools, 1):
                    tool_name = tool.name if hasattr(tool, 'name') else tool.get('name', 'Unknown')
                    tool_desc = tool.description if hasattr(tool, 'description') else tool.get('description', 'No description')

                    print(f"   {i}. {tool_name}")
                    print(f"      {tool_desc[:80]}..." if len(tool_desc) > 80 else f"      {tool_desc}")
                    print()

                print("=" * 60)
                print("✅ MCP Server Test Completed Successfully")
                print("=" * 60)
                print()
                print("The server is ready to accept connections from:")
                print("  • Claude Desktop")
                print("  • Python MCP clients")
                print("  • Node.js MCP clients")
                print()
                print("See MCP_CONNECTION_GUIDE.md for integration details.")

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure virtual environment is activated")
        print("  2. Check that all dependencies are installed")
        print("  3. Verify Python version is 3.11+")
        print(f"     Current: {sys.version}")
        raise


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
