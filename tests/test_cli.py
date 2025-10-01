"""Test CLI functionality for TranscribeMCP server modes.

This module tests the command-line interface for both stdio and HTTP modes.
"""

import pytest
import subprocess
import sys
from pathlib import Path


def test_cli_help():
    """Test that CLI help message displays correctly."""
    result = subprocess.run(
        [sys.executable, "-m", "src.mcp_server.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "transcribe-mcp" in result.stdout
    assert "stdio" in result.stdout
    assert "http" in result.stdout


def test_cli_stdio_help():
    """Test stdio mode help message."""
    result = subprocess.run(
        [sys.executable, "-m", "src.mcp_server.cli", "stdio", "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "stdio" in result.stdout
    assert "--log-level" in result.stdout


def test_cli_http_help():
    """Test HTTP mode help message."""
    result = subprocess.run(
        [sys.executable, "-m", "src.mcp_server.cli", "http", "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "http" in result.stdout
    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert "--transport" in result.stdout


def test_cli_no_mode_error():
    """Test that CLI requires a mode to be specified."""
    result = subprocess.run(
        [sys.executable, "-m", "src.mcp_server.cli"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode != 0
    assert "required" in result.stderr.lower() or "required" in result.stdout.lower()


def test_cli_invalid_mode_error():
    """Test that CLI rejects invalid modes."""
    result = subprocess.run(
        [sys.executable, "-m", "src.mcp_server.cli", "invalid_mode"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode != 0


def test_import_cli_module():
    """Test that CLI module can be imported."""
    from src.mcp_server.cli import create_parser, setup_logging

    parser = create_parser()
    assert parser is not None

    # Test setup_logging doesn't raise
    setup_logging("INFO")


def test_cli_server_import():
    """Test that server modes can be imported."""
    from src.mcp_server.server import TranscribeMCPServer

    server = TranscribeMCPServer()
    assert server is not None
    assert hasattr(server, "run_stdio")
    assert hasattr(server, "run_sse")
    assert hasattr(server, "run_streamable_http")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
