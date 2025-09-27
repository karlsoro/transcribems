"""
Contract test for logging configuration and functionality.
This test defines the expected behavior and must FAIL initially (TDD approach).
"""

import pytest
import json
from pathlib import Path
import tempfile


class TestLoggingConfigurationContract:
    """Contract tests for application logging system."""

    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_logger_creates_structured_logs(self, temp_log_dir):
        """
        Contract: Should create structured logs in JSON format.
        """
        from src.core.logging import setup_logging, get_logger

        # This will fail until logging module is implemented
        setup_logging(log_dir=str(temp_log_dir), log_level="INFO")
        logger = get_logger("test_module")

        logger.info("Test message", extra={
            "job_id": "test-123",
            "file_name": "test.wav",
            "processing_stage": "upload"
        })

        # Check log file was created
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0

        # Find the main log file (not error log)
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None, f"No main log file found in {[f.name for f in log_files]}"

        # Verify structured format - get the last log entry (our test message)
        log_content = main_log_file.read_text()
        log_lines = [line for line in log_content.strip().split('\n') if line.strip()]
        assert len(log_lines) > 0, f"No log lines found in {log_content}"

        # Parse the last log entry (our test message)
        log_entry = json.loads(log_lines[-1])

        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert log_entry["job_id"] == "test-123"
        assert log_entry["file_name"] == "test.wav"
        assert log_entry["processing_stage"] == "upload"

    def test_logger_supports_multiple_log_levels(self, temp_log_dir):
        """
        Contract: Should support DEBUG, INFO, WARNING, ERROR, CRITICAL levels.
        """
        from src.core.logging import setup_logging, get_logger

        setup_logging(log_dir=str(temp_log_dir), log_level="DEBUG")
        logger = get_logger("test_levels")

        # Test all log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()
        log_lines = [line for line in log_content.strip().split('\n') if line.strip()]

        # Should have 6 log entries (5 test + 1 setup)
        assert len(log_lines) >= 5

        # Verify each level was logged - filter out setup log
        test_lines = [line for line in log_lines if '"test_levels"' in line]
        levels = [json.loads(line)["level"] for line in test_lines]
        assert "DEBUG" in levels
        assert "INFO" in levels
        assert "WARNING" in levels
        assert "ERROR" in levels
        assert "CRITICAL" in levels

    def test_logger_respects_debug_flag(self, temp_log_dir):
        """
        Contract: Should respect DEBUG flag to control verbosity.
        """
        from src.core.logging import setup_logging, get_logger

        # Test with DEBUG disabled
        setup_logging(log_dir=str(temp_log_dir), log_level="INFO")
        logger = get_logger("debug_test")

        logger.debug("Debug message - should not appear")
        logger.info("Info message - should appear")

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()

        # Should only contain INFO message, not DEBUG
        assert "Info message - should appear" in log_content
        assert "Debug message - should not appear" not in log_content

    def test_logger_includes_transcription_context(self, temp_log_dir):
        """
        Contract: Should include transcription-specific context in logs.
        """
        from src.core.logging import setup_logging, get_logger

        setup_logging(log_dir=str(temp_log_dir), log_level="INFO")
        logger = get_logger("transcription")

        # Log with transcription context
        logger.info("Processing started", extra={
            "job_id": "job-456",
            "audio_file": "meeting.wav",
            "file_size_mb": 150,
            "duration_seconds": 3600,
            "model": "large-v2",
            "language": "en",
            "gpu_used": True,
            "speaker_diarization": True
        })

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()
        log_lines = [line.strip() for line in log_content.split('\n') if line.strip()]
        # Get the transcription log entry (not the setup log)
        transcription_line = [line for line in log_lines if '"transcription"' in line][0]
        log_entry = json.loads(transcription_line)

        assert log_entry["job_id"] == "job-456"
        assert log_entry["audio_file"] == "meeting.wav"
        assert log_entry["file_size_mb"] == 150
        assert log_entry["duration_seconds"] == 3600
        assert log_entry["model"] == "large-v2"
        assert log_entry["language"] == "en"
        assert log_entry["gpu_used"] is True
        assert log_entry["speaker_diarization"] is True

    def test_logger_handles_processing_progress(self, temp_log_dir):
        """
        Contract: Should log processing progress with timestamps.
        """
        from src.core.logging import setup_logging, get_logger

        setup_logging(log_dir=str(temp_log_dir), log_level="INFO")
        logger = get_logger("progress")

        # Log processing stages
        stages = [
            {"stage": "file_upload", "progress": 0.0},
            {"stage": "audio_preprocessing", "progress": 0.2},
            {"stage": "transcription", "progress": 0.7},
            {"stage": "speaker_diarization", "progress": 0.9},
            {"stage": "output_generation", "progress": 1.0}
        ]

        for stage_info in stages:
            logger.info("Processing progress", extra={
                "job_id": "progress-test",
                "stage": stage_info["stage"],
                "progress_percent": stage_info["progress"] * 100
            })

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()
        # Split by actual newlines and filter out empty lines
        log_lines = [line.strip() for line in log_content.split('\n') if line.strip()]

        assert len(log_lines) >= 5

        # Verify progress logging - skip setup log entry
        progress_lines = [line for line in log_lines if '"progress_percent"' in line]
        progress_values = [json.loads(line)["progress_percent"] for line in progress_lines]
        assert progress_values == [0.0, 20.0, 70.0, 90.0, 100.0]

    def test_logger_captures_errors_with_stack_traces(self, temp_log_dir):
        """
        Contract: Should capture errors with full stack traces.
        """
        from src.core.logging import setup_logging, get_logger

        setup_logging(log_dir=str(temp_log_dir), log_level="ERROR")
        logger = get_logger("error_handling")

        try:
            # Simulate an error
            raise ValueError("Test error for logging")
        except Exception as e:
            logger.error("Processing failed", extra={
                "job_id": "error-test",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, exc_info=True)

        log_files = list(temp_log_dir.glob("*.log"))
        log_content = log_files[0].read_text()
        log_entry = json.loads(log_content.strip())

        assert log_entry["level"] == "ERROR"
        assert log_entry["error_type"] == "ValueError"
        assert log_entry["error_message"] == "Test error for logging"
        assert "traceback" in log_entry or "stack_trace" in log_entry

    def test_logger_supports_log_rotation(self, temp_log_dir):
        """
        Contract: Should support log rotation to prevent disk space issues.
        """
        from src.core.logging import setup_logging, get_logger

        # Setup with small max file size to force rotation
        setup_logging(
            log_dir=str(temp_log_dir),
            log_level="INFO",
            max_file_size_mb=1,  # 1MB max
            backup_count=3
        )
        logger = get_logger("rotation_test")

        # Generate enough logs to trigger rotation
        for i in range(1000):
            logger.info(f"Log message {i}" * 100)  # Large messages

        log_files = list(temp_log_dir.glob("*.log*"))
        # Should have multiple log files due to rotation
        assert len(log_files) >= 2

    def test_logger_performance_timing(self, temp_log_dir):
        """
        Contract: Should include performance timing information.
        """
        from src.core.logging import setup_logging, get_logger
        import time

        setup_logging(log_dir=str(temp_log_dir), log_level="INFO")
        logger = get_logger("performance")

        start_time = time.time()

        # Simulate processing time
        time.sleep(0.1)

        processing_time = time.time() - start_time

        logger.info("Transcription completed", extra={
            "job_id": "perf-test",
            "processing_time_seconds": processing_time,
            "audio_duration_seconds": 60,
            "realtime_factor": 60 / processing_time
        })

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()
        log_lines = [line.strip() for line in log_content.split('\n') if line.strip()]
        # Get the performance log entry
        perf_line = [line for line in log_lines if '"processing_time_seconds"' in line][0]
        log_entry = json.loads(perf_line)

        assert "processing_time_seconds" in log_entry
        assert "realtime_factor" in log_entry
        assert log_entry["processing_time_seconds"] >= 0.1

    def test_logger_configurable_from_environment(self, temp_log_dir):
        """
        Contract: Should be configurable via environment variables.
        """
        import os

        # Set environment variables
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["LOG_DIR"] = str(temp_log_dir)
        os.environ["LOG_FORMAT"] = "json"

        from src.core.logging import setup_logging_from_env, get_logger

        # This will fail until environment-based config is implemented
        setup_logging_from_env()
        logger = get_logger("env_config")

        logger.debug("Debug from environment config")

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()

        # Should contain debug message since LOG_LEVEL=DEBUG
        assert "Debug from environment config" in log_content

        # Cleanup
        del os.environ["LOG_LEVEL"]
        del os.environ["LOG_DIR"]
        del os.environ["LOG_FORMAT"]

    def test_logger_sanitizes_sensitive_data(self, temp_log_dir):
        """
        Contract: Should sanitize sensitive information from logs.
        """
        from src.core.logging import setup_logging, get_logger

        setup_logging(log_dir=str(temp_log_dir), log_level="INFO")
        logger = get_logger("security")

        # Log with potentially sensitive data
        logger.info("User upload", extra={
            "user_id": "user123",
            "api_key": "sk-1234567890abcdef",  # Should be sanitized
            "file_path": "/home/user/secret_meeting.wav",  # Should be sanitized
            "ip_address": "192.168.1.100"  # Should be sanitized
        })

        log_files = list(temp_log_dir.glob("*.log"))
        main_log_file = None
        for log_file in log_files:
            if "error" not in log_file.name:
                main_log_file = log_file
                break

        assert main_log_file is not None
        log_content = main_log_file.read_text()

        # Sensitive data should be masked/sanitized
        assert "sk-1234567890abcdef" not in log_content
        assert "***" in log_content or "REDACTED" in log_content
