"""
Simplified FastAPI application for TranscribeMCP without Celery/Redis dependencies.
This version provides a REST API for testing and simple deployments.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.api.endpoints.transcription_simple import router as transcription_router
from src.api.endpoints.transcription_sse import router as sse_router
from src.services.job_storage import get_job_storage


# Fix cuDNN library path for pyannote.audio speaker diarization
# This must be set before importing torch to avoid library loading issues
# The cuDNN libraries are needed for pyannote.audio's neural networks
import sys
cudnn_path = Path(sys.prefix) / "lib" / "python3.12" / "site-packages" / "nvidia" / "cudnn" / "lib"
if cudnn_path.exists():
    current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if str(cudnn_path) not in current_ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{cudnn_path}:{current_ld_path}"

# Initialize settings and logging
settings = get_settings()
setup_logging(
    log_dir=settings.LOG_DIR,
    log_level=settings.LOG_LEVEL,
    enable_console=True
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("TranscribeMCP REST API starting up", extra={
        "version": "1.1.0-simple",
        "mode": "simplified (no Celery/Redis) with persistent storage",
        "debug": settings.DEBUG
    })

    # Ensure directories exist
    directories = [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.LOG_DIR, "job_storage"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Initialize job storage
    job_storage = get_job_storage()

    # Start background job cleanup task (runs every hour)
    async def cleanup_task():
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                deleted = await job_storage.cleanup_old_jobs(retention_hours=48)
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old jobs")
            except Exception as e:
                logger.error(f"Job cleanup error: {e}", exc_info=True)

    import asyncio
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    app.state.cleanup_task = cleanup_task_handle

    # Initialize services if needed
    try:
        from src.services.gpu_service import GPUService
        gpu_service = GPUService()
        gpu_info = gpu_service.detect_gpus()

        logger.info("GPU detection completed", extra={
            "cuda_available": gpu_info["cuda_available"],
            "device_count": gpu_info["device_count"]
        })

        from src.services.whisperx_service import WhisperXService
        whisperx_service = WhisperXService(
            model_size=settings.WHISPER_MODEL,
            device=settings.DEVICE,
            hf_token=settings.HF_TOKEN
        )
        device_info = whisperx_service.get_device_info()

        logger.info("WhisperX service initialized", extra={
            "device": device_info["device_name"],
            "gpu_available": device_info["gpu_available"]
        })

    except Exception as e:
        logger.warning("Service initialization warning", extra={
            "error": str(e),
            "message": "Some services may not be fully available"
        })

    logger.info("TranscribeMCP REST API startup completed")

    yield

    # Shutdown
    logger.info("TranscribeMCP REST API shutting down")

    # Cancel cleanup task
    if hasattr(app.state, 'cleanup_task'):
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass

    logger.info("TranscribeMCP REST API shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="TranscribeMCP REST API (Simplified)",
    description="WhisperX Audio Transcription REST API - Simplified version without Celery/Redis",
    version="1.1.0-simple",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests and responses."""
    start_time = datetime.utcnow()

    # Skip ALL middleware processing for SSE streams - let them pass through untouched
    if "/stream" in request.url.path:
        return await call_next(request)

    logger.info("HTTP request received", extra={
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else None,
    })

    try:
        response = await call_next(request)
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        logger.info("HTTP request completed", extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time": processing_time
        })

        return response

    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        logger.error("HTTP request failed", extra={
            "method": request.method,
            "url": str(request.url),
            "error": str(e),
            "processing_time": processing_time
        }, exc_info=True)

        raise


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning("Request validation failed", extra={
        "url": str(request.url),
        "method": request.method,
        "errors": exc.errors()
    })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", extra={
        "url": str(request.url),
        "method": request.method,
        "error": str(exc),
        "error_type": type(exc).__name__
    }, exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(transcription_router)
app.include_router(sse_router)


# Health check endpoint
@app.get("/v1/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancing.

    Returns:
        JSON response with system health information
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.1.0-simple",
            "mode": "simplified",
            "note": "No Celery/Redis required"
        }

        # Check directory permissions
        import os
        directories_ok = True
        for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.LOG_DIR]:
            dir_path = Path(directory)
            if not (dir_path.exists() and dir_path.is_dir() and
                    os.access(dir_path, os.R_OK | os.W_OK)):
                directories_ok = False
                break

        health_status["directories"] = "ok" if directories_ok else "error"

        # Check GPU availability (non-blocking)
        try:
            from src.services.gpu_service import GPUService
            gpu_service = GPUService()
            gpu_available = gpu_service.is_gpu_available()
            health_status["gpu"] = "available" if gpu_available else "unavailable"
        except Exception:
            health_status["gpu"] = "unknown"

        # Overall status
        if not directories_ok:
            health_status["status"] = "degraded"

        return JSONResponse(
            content=health_status,
            status_code=200 if health_status["status"] == "healthy" else 503
        )

    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)}, exc_info=True)

        return JSONResponse(
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": "Health check failed"
            },
            status_code=503
        )


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "TranscribeMCP REST API (Simplified)",
        "description": "WhisperX Audio Transcription REST API without Celery/Redis",
        "version": "1.1.0-simple",
        "docs": "/docs",
        "health": "/v1/health",
        "note": "This is a simplified version for testing. For production, use the MCP server."
    }


def main():
    """Main entry point for running the application."""
    uvicorn.run(
        "src.main_simple:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        timeout_keep_alive=3600,  # 1 hour keep-alive timeout
        timeout_graceful_shutdown=30
    )


if __name__ == "__main__":
    main()
