#!/bin/bash
# TranscribeMS MCP Server Startup Script

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  TranscribeMS MCP Server${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/transcribems_env" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found at $PROJECT_ROOT/transcribems_env${NC}"
    echo "Please create it first with: python -m venv transcribems_env"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}✓${NC} Activating virtual environment..."
source "$PROJECT_ROOT/transcribems_env/bin/activate"

# Change to project root
cd "$PROJECT_ROOT"

# Check if MCP is installed
if ! python -c "import mcp" 2>/dev/null; then
    echo -e "${YELLOW}Warning: MCP package not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Display server info
echo -e "${GREEN}✓${NC} Virtual environment: $VIRTUAL_ENV"
echo -e "${GREEN}✓${NC} Python version: $(python --version)"
echo -e "${GREEN}✓${NC} Working directory: $PROJECT_ROOT"
echo ""

# Check GPU availability
GPU_INFO=$(python -c "import torch; print('CUDA available' if torch.cuda.is_available() else 'CPU only')" 2>/dev/null || echo "GPU check failed")
echo -e "${BLUE}Device mode:${NC} $GPU_INFO"
echo ""

echo -e "${GREEN}✓${NC} Starting MCP server..."
echo -e "${BLUE}================================================${NC}"
echo ""

# Start the MCP server
exec python -m src.mcp_server.fastmcp_server
