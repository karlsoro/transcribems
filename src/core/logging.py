"""
Structured logging configuration for TranscribeMCP.
"""

import logging
import logging.handlers
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import structlog


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields
        if hasattr(record, 'job_id'):
            log_entry["job_id"] = record.job_id
        if hasattr(record, 'file_name'):
            log_entry["file_name"] = record.file_name
        if hasattr(record, 'processing_stage'):
            log_entry["processing_stage"] = record.processing_stage
        if hasattr(record, 'audio_file'):
            log_entry["audio_file"] = record.audio_file
        if hasattr(record, 'file_size_mb'):
            log_entry["file_size_mb"] = record.file_size_mb
        if hasattr(record, 'duration_seconds'):
            log_entry["duration_seconds"] = record.duration_seconds
        if hasattr(record, 'model'):
            log_entry["model"] = record.model
        if hasattr(record, 'language'):
            log_entry["language"] = record.language
        if hasattr(record, 'gpu_used'):
            log_entry["gpu_used"] = record.gpu_used
        if hasattr(record, 'speaker_diarization'):
            log_entry["speaker_diarization"] = record.speaker_diarization
        if hasattr(record, 'progress_percent'):
            log_entry["progress_percent"] = record.progress_percent
        if hasattr(record, 'stage'):
            log_entry["stage"] = record.stage
        if hasattr(record, 'processing_time_seconds'):
            log_entry["processing_time_seconds"] = record.processing_time_seconds
        if hasattr(record, 'realtime_factor'):
            log_entry["realtime_factor"] = record.realtime_factor
        if hasattr(record, 'error_type'):
            log_entry["error_type"] = record.error_type
        if hasattr(record, 'error_message'):
            log_entry["error_message"] = record.error_message

        # Add additional fields for testing
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'api_key'):
            log_entry["api_key"] = record.api_key
        if hasattr(record, 'file_path'):
            log_entry["file_path"] = record.file_path
        if hasattr(record, 'ip_address'):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, 'original_filename'):
            log_entry["original_filename"] = record.original_filename

        # Add exception information
        if record.exc_info:
            log_entry["traceback"] = self.formatException(record.exc_info)

        # Sanitize sensitive data
        log_entry = _sanitize_log_data(log_entry)

        return json.dumps(log_entry)


def _sanitize_log_data(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive information from log data.

    Args:
        log_data: Log data dictionary

    Returns:
        Sanitized log data
    """
    sensitive_keys = {
        'api_key', 'token', 'password', 'secret', 'key',
        'authorization', 'auth', 'credential'
    }

    sensitive_patterns = {
        'file_path': lambda x: _mask_file_path(x) if isinstance(x, str) else x,
        'ip_address': lambda x: _mask_ip_address(x) if isinstance(x, str) else x
    }

    sanitized = {}
    for key, value in log_data.items():
        key_lower = key.lower()

        # Check for sensitive keys
        if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                sanitized[key] = value[:2] + "***" + value[-2:]
            else:
                sanitized[key] = "REDACTED"
        # Check for sensitive patterns
        elif key_lower in sensitive_patterns:
            sanitized[key] = sensitive_patterns[key_lower](value)
        else:
            sanitized[key] = value

    return sanitized


def _mask_file_path(file_path: str) -> str:
    """Mask sensitive parts of file paths."""
    if "/home/" in file_path or "/Users/" in file_path:
        parts = file_path.split("/")
        masked_parts = []
        for part in parts:
            if part in ["home", "Users"] or part.startswith("user"):
                masked_parts.append("***")
            else:
                masked_parts.append(part)
        return "/".join(masked_parts)
    return file_path


def _mask_ip_address(ip: str) -> str:
    """Mask IP addresses for privacy."""
    if "." in ip:  # IPv4
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.***.**"
    elif ":" in ip:  # IPv6
        parts = ip.split(":")
        if len(parts) >= 4:
            return ":".join(parts[:2]) + ":***:***"
    return ip


def setup_logging(
    log_dir: str = "./logs",
    log_level: str = "INFO",
    max_file_size_mb: int = 100,
    backup_count: int = 5,
    enable_console: bool = True
) -> None:
    """
    Set up structured logging configuration.

    Args:
        log_dir: Directory for log files
        log_level: Logging level
        max_file_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler with rotation
    log_file = log_path / "transcribe_mcp.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)

    # Error file handler
    error_log_file = log_path / "transcribe_mcp_errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setFormatter(JSONFormatter())
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("whisperx").setLevel(logging.INFO)
    logging.getLogger("torch").setLevel(logging.WARNING)

    logging.info("Logging configured successfully", extra={
        "log_dir": str(log_path),
        "log_level": log_level,
        "max_file_size_mb": max_file_size_mb,
        "backup_count": backup_count
    })


def setup_logging_from_env() -> None:
    """Set up logging from environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_dir = os.getenv("LOG_DIR", "./logs")
    log_format = os.getenv("LOG_FORMAT", "json")

    setup_logging(
        log_dir=log_dir,
        log_level=log_level,
        enable_console=True
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)