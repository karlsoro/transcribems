#!/bin/bash
# Start TranscribeMCP MCP Server in HTTP mode
#
# This script starts the TranscribeMCP MCP server in HTTP/SSE mode.
# Use this for web applications and services that need HTTP access.
#
# Usage:
#   ./scripts/start_mcp_server_http.sh [PORT] [HOST]
#
# Examples:
#   ./scripts/start_mcp_server_http.sh              # Default: 0.0.0.0:8000
#   ./scripts/start_mcp_server_http.sh 3000         # Custom port
#   ./scripts/start_mcp_server_http.sh 3000 127.0.0.1  # Custom port and host

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Default values
PORT="${1:-8000}"
HOST="${2:-0.0.0.0}"
TRANSPORT="${3:-sse}"

echo "========================================="
echo "TranscribeMCP HTTP Server Startup"
echo "========================================="
echo "Project root: $PROJECT_ROOT"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Transport: $TRANSPORT"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "transcribe_mcp_env" ]; then
    echo "❌ Error: Virtual environment not found at transcribe_mcp_env/"
    echo "Please create it first:"
    echo "  python -m venv transcribe_mcp_env"
    echo "  source transcribe_mcp_env/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source transcribe_mcp_env/bin/activate

# Check if transcribe-mcp command is available
if ! command -v transcribe-mcp &> /dev/null; then
    echo "❌ Error: transcribe-mcp command not found"
    echo "Please install the package:"
    echo "  pip install -e ."
    exit 1
fi

echo "✅ Environment ready"
echo ""

# Start the server
echo "Starting TranscribeMCP HTTP server..."
echo "Server will be available at: http://$HOST:$PORT"
echo "SSE endpoint: http://$HOST:$PORT/sse"
echo "Message endpoint: http://$HOST:$PORT/message"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================="
echo ""

# Start server with appropriate transport
exec transcribe-mcp http --host "$HOST" --port "$PORT" --transport "$TRANSPORT"
