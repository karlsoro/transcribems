# Multi-stage Docker build for TranscribeMS with CUDA support
FROM nvidia/cuda:12.1-devel-ubuntu22.04 AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Production stage
FROM base AS production

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install -e ".[gpu]"

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY .env.example .env

# Create necessary directories
RUN mkdir -p uploads transcriptions logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/v1/health')" || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM production AS development

USER root

# Install development dependencies
RUN pip install -e ".[dev]"

# Install pre-commit
RUN pip install pre-commit

USER appuser

# Override command for development
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Worker stage for Celery workers
FROM production AS worker

# Override command for Celery worker
CMD ["celery", "-A", "src.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=2"]