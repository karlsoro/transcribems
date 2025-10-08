#!/bin/bash

# TranscribeMCP Server Startup Script
# Sets required environment variables for cuDNN compatibility

# Set cuDNN library path for PyTorch/WhisperX compatibility
export LD_LIBRARY_PATH="/home/karlsoro/Projects/TranscribeMS/transcribe_mcp_env/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"

# Start the server (NO --reload to avoid inconsistent state)
cd /home/karlsoro/Projects/TranscribeMS
exec transcribe_mcp_env/bin/uvicorn src.main_simple:app --host 127.0.0.1 --port 8000
