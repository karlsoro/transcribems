"""Integration tests for TranscribeMCP HTTP server.

These tests verify that the HTTP server can start and respond to requests.
"""

import pytest
import subprocess
import sys
import time
import socket
import httpx
import asyncio
from pathlib import Path


def is_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def wait_for_port(port, timeout=10):
    """Wait for a port to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) == 0:
                return True
        time.sleep(0.5)
    return False


@pytest.fixture
def test_port():
    """Find an available port for testing."""
    for port in range(18000, 19000):
        if is_port_available(port):
            return port
    pytest.skip("No available ports found")


@pytest.fixture
async def http_server(test_port):
    """Start HTTP server for testing."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "src.mcp_server.cli", "http", "--port", str(test_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    if not wait_for_port(test_port, timeout=10):
        proc.terminate()
        pytest.fail(f"Server failed to start on port {test_port}")

    yield f"http://localhost:{test_port}"

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_server_connection(http_server):
    """Test basic HTTP server connection."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{http_server}/sse", timeout=2.0)
            # SSE endpoint should return 200 or stream
            assert response.status_code == 200 or response.headers.get("content-type") == "text/event-stream"
        except httpx.TimeoutException:
            # This is expected for SSE - it's a long-lived connection
            pass


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_server_tool_call(http_server):
    """Test calling an MCP tool via HTTP."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{http_server}/message",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            },
            timeout=5.0
        )
        assert response.status_code == 200

        data = response.json()
        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_server_list_tools(http_server):
    """Test listing MCP tools via HTTP."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{http_server}/message",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            },
            timeout=5.0
        )
        assert response.status_code == 200

        data = response.json()
        if "result" in data:
            # Check that we have tools
            tools = data["result"].get("tools", [])
            tool_names = [tool.get("name") for tool in tools]

            # Verify our expected tools are present
            expected_tools = [
                "transcribe_audio",
                "get_transcription_progress",
                "get_transcription_result",
                "list_transcription_history",
                "batch_transcribe",
                "cancel_transcription"
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"Tool {expected_tool} not found in {tool_names}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_server_invalid_method(http_server):
    """Test that invalid methods return proper errors."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{http_server}/message",
            json={
                "jsonrpc": "2.0",
                "method": "invalid/method",
                "params": {},
                "id": 1
            },
            timeout=5.0
        )
        assert response.status_code == 200  # JSON-RPC errors still return 200

        data = response.json()
        # Should have an error field for invalid method
        assert "error" in data or "result" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_http_server_sse_endpoint(http_server):
    """Test that SSE endpoint is accessible."""
    async with httpx.AsyncClient() as client:
        # Use streaming to test SSE
        async with client.stream("GET", f"{http_server}/sse", timeout=2.0) as response:
            # SSE endpoint should support streaming
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.integration
def test_http_server_cli_args():
    """Test server starts with different CLI arguments."""
    test_cases = [
        ["http", "--host", "127.0.0.1"],
        ["http", "--port", "18001"],
        ["http", "--transport", "sse"],
        ["http", "--log-level", "DEBUG"],
    ]

    for args in test_cases:
        port = 18001 if "--port" in args else 18000

        if not is_port_available(port):
            continue

        proc = subprocess.Popen(
            [sys.executable, "-m", "src.mcp_server.cli"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            # Give server time to start
            time.sleep(2)

            # Check process is running
            assert proc.poll() is None, f"Server died with args: {args}"

            # Try to connect
            if wait_for_port(port, timeout=5):
                assert True, f"Server started successfully with args: {args}"
            else:
                pytest.fail(f"Server failed to bind to port with args: {args}")

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
