#!/usr/bin/env python3
"""Validation script for TranscribeMCP MCP implementation.

This script validates the structure and imports without requiring
external dependencies like WhisperX, librosa, etc.
"""

import sys
from pathlib import Path

def validate_structure():
    """Validate project structure."""
    print("🔍 Validating project structure...")

    required_files = [
        "src/models/types.py",
        "src/models/audio_file_mcp.py",
        "src/models/transcription_job.py",
        "src/models/transcription_result.py",
        "src/services/audio_file_service.py",
        "src/services/transcription_service.py",
        "src/services/progress_service.py",
        "src/services/storage_service.py",
        "src/services/history_service.py",
        "src/tools/transcribe_tool.py",
        "src/tools/progress_tool.py",
        "src/tools/history_tool.py",
        "src/tools/result_tool.py",
        "src/tools/batch_tool.py",
        "src/tools/cancel_tool.py",
        "src/mcp_server/server.py",
        "src/error_handler.py"
    ]

    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)

    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    else:
        print(f"✅ All {len(required_files)} required files present")
        return True

def validate_tool_functions():
    """Validate tool functions exist and are callable."""
    print("🔍 Validating tool functions...")

    try:
        # Mock the dependencies that would cause import errors
        sys.modules['librosa'] = type('MockLibrosa', (), {})
        sys.modules['soundfile'] = type('MockSoundFile', (), {})
        sys.modules['mutagen'] = type('MockMutagen', (), {'File': lambda x: None})
        sys.modules['aiofiles'] = type('MockAioFiles', (), {'open': lambda *args, **kwargs: None})

        # Import and test tool functions
        from src.tools.transcribe_tool import transcribe_audio_tool
        from src.tools.progress_tool import get_transcription_progress_tool
        from src.tools.history_tool import list_transcription_history_tool
        from src.tools.result_tool import get_transcription_result_tool
        from src.tools.batch_tool import batch_transcribe_tool
        from src.tools.cancel_tool import cancel_transcription_tool

        tools = [
            ('transcribe_audio_tool', transcribe_audio_tool),
            ('get_transcription_progress_tool', get_transcription_progress_tool),
            ('list_transcription_history_tool', list_transcription_history_tool),
            ('get_transcription_result_tool', get_transcription_result_tool),
            ('batch_transcribe_tool', batch_transcribe_tool),
            ('cancel_transcription_tool', cancel_transcription_tool)
        ]

        for name, func in tools:
            if not callable(func):
                print(f"❌ {name} is not callable")
                return False
            if func.__name__ != name:
                print(f"❌ {name} has incorrect __name__: {func.__name__}")
                return False

        print(f"✅ All {len(tools)} MCP tools are callable with correct names")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def validate_models():
    """Validate model classes can be imported."""
    print("🔍 Validating model classes...")

    try:
        from src.models.types import JobStatus, AudioFileState, TranscriptionSettings
        from src.models.audio_file_mcp import AudioFile
        from src.models.transcription_job import TranscriptionJob
        from src.models.transcription_result import TranscriptionResult

        # Test enum values
        assert JobStatus.PENDING.value == "pending"
        assert AudioFileState.DISCOVERED.value == "discovered"

        print("✅ All model classes imported successfully")
        return True

    except Exception as e:
        print(f"❌ Model validation error: {e}")
        return False

def main():
    """Run all validations."""
    print("🚀 Starting TranscribeMCP Implementation Validation")
    print("=" * 50)

    validations = [
        validate_structure,
        validate_models,
        validate_tool_functions
    ]

    results = []
    for validation in validations:
        results.append(validation())
        print()

    if all(results):
        print("✅ All validations passed! MCP implementation is ready.")
        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install WhisperX: pip install whisperx")
        print("3. Run integration tests")
        print("4. Test with real audio files")
        return 0
    else:
        print("❌ Some validations failed. Please fix issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())