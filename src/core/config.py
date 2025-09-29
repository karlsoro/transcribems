"""
Configuration settings for TranscribeMS application.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, description="Port to bind to")

    # GPU Configuration
    CUDA_VISIBLE_DEVICES: str = Field(default="0", description="CUDA visible devices")
    USE_GPU: bool = Field(default=True, description="Enable GPU usage")

    # Redis Configuration (for Celery)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Database Configuration (Optional - for job persistence)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )

    # File Storage Configuration
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    OUTPUT_DIR: str = Field(default="transcriptions", description="Output directory")
    LOG_DIR: str = Field(default="logs", description="Log directory")
    MAX_FILE_SIZE: int = Field(
        default=5368709120,  # 5GB
        description="Maximum file size in bytes"
    )
    CHUNK_SIZE: int = Field(
        default=268435456,  # 256MB
        description="Chunk size for file processing"
    )

    # WhisperX Configuration
    WHISPER_MODEL: str = Field(
        default="large-v2",
        description="Default WhisperX model size"
    )
    SPEAKER_DIARIZATION: bool = Field(
        default=True,
        description="Enable speaker diarization by default"
    )
    LANGUAGE: str = Field(default="auto", description="Default language detection")
    DEVICE: str = Field(default="auto", description="Processing device")

    # Processing Configuration
    MAX_PROCESSING_TIME: int = Field(
        default=3600,  # 1 hour
        description="Maximum processing time in seconds"
    )
    CLEANUP_AFTER_PROCESSING: bool = Field(
        default=False,
        description="Cleanup files after processing"
    )
    RETAIN_UPLOADS_DAYS: int = Field(
        default=7,
        description="Days to retain uploaded files"
    )

    # Celery Configuration
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )
    CELERY_WORKER_CONCURRENCY: int = Field(
        default=2,
        description="Celery worker concurrency"
    )

    # Security Configuration
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for security"
    )
    ALLOWED_HOSTS: str = Field(
        default="localhost,127.0.0.1",
        description="Comma-separated allowed hosts"
    )
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated CORS origins"
    )

    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    FLOWER_PORT: int = Field(default=5555, description="Flower monitoring port")

    # Hugging Face Configuration
    HF_TOKEN: Optional[str] = Field(
        default=None,
        description="Hugging Face token for speaker diarization"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        directories = [
            self.UPLOAD_DIR,
            self.OUTPUT_DIR,
            self.LOG_DIR,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Get allowed hosts as a list."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def get_redis_config(self) -> dict:
        """Get Redis configuration dictionary."""
        return {
            "url": self.REDIS_URL,
            "encoding": "utf-8",
            "decode_responses": True
        }

    def get_whisperx_config(self) -> dict:
        """Get WhisperX configuration dictionary."""
        return {
            "model_size": self.WHISPER_MODEL,
            "device": self.DEVICE,
            "compute_type": "float16" if self.USE_GPU else "float32",
            "language": self.LANGUAGE if self.LANGUAGE != "auto" else None
        }

    def get_celery_config(self) -> dict:
        """Get Celery configuration dictionary."""
        return {
            "broker_url": self.CELERY_BROKER_URL,
            "result_backend": self.CELERY_RESULT_BACKEND,
            "worker_concurrency": self.CELERY_WORKER_CONCURRENCY,
            "task_serializer": "json",
            "accept_content": ["json"],
            "result_serializer": "json",
            "timezone": "UTC",
            "enable_utc": True,
            "task_track_started": True,
            "task_time_limit": self.MAX_PROCESSING_TIME,
            "worker_prefetch_multiplier": 1,
            "task_acks_late": True,
        }

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG and os.getenv("ENVIRONMENT") == "production"

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG or os.getenv("ENVIRONMENT") == "development"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.

    Returns:
        New Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
