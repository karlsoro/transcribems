"""
FastAPI main application for TranscribeMS.
"""

import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn

from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger
from src.api.endpoints.transcription import router as transcription_router


# Initialize settings and logging
settings = get_settings()
setup_logging(
    log_dir=settings.LOG_DIR,
    log_level=settings.LOG_LEVEL,
    enable_console=not settings.is_production()
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info("TranscribeMS API starting up", extra={
        "version": "1.0.0",
        "debug": settings.DEBUG,
        "environment": "production" if settings.is_production() else "development"
    })

    # Ensure directories exist
    directories = [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.LOG_DIR]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Initialize services if needed
    try:
        # Import and test GPU service
        from src.services.gpu_service import GPUService
        gpu_service = GPUService()
        gpu_info = gpu_service.detect_gpus()

        logger.info("GPU detection completed", extra={
            "cuda_available": gpu_info["cuda_available"],
            "device_count": gpu_info["device_count"]
        })

        # Test WhisperX service initialization (without loading models)
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

    logger.info("TranscribeMS API startup completed")

    yield

    # Shutdown
    logger.info("TranscribeMS API shutting down")

    # Cleanup if needed
    try:
        # Any cleanup tasks would go here
        pass
    except Exception as e:
        logger.error("Error during shutdown cleanup", extra={"error": str(e)})

    logger.info("TranscribeMS API shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="TranscribeMS API",
    description="WhisperX Audio Transcription API with Speaker Identification",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production() else None,
    redoc_url="/redoc" if not settings.is_production() else None,
)

# Add middleware
if settings.is_production():
    # Trusted host middleware for production
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests and responses."""
    start_time = datetime.utcnow()

    # Log request
    logger.info("HTTP request received", extra={
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    })

    try:
        response = await call_next(request)
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Log response
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


# Health check endpoint
@app.get("/v1/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancing.

    Returns:
        JSON response with system health information
    """
    try:
        # Check basic system health
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "environment": "production" if settings.is_production() else "development"
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

        # Check Redis connection (for Celery)
        redis_ok = True
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
        except Exception:
            redis_ok = False

        health_status["redis"] = "ok" if redis_ok else "error"

        # Overall status
        if not directories_ok or not redis_ok:
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
        "message": "TranscribeMS API",
        "description": "WhisperX Audio Transcription API with Speaker Identification",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/v1/health"
    }


def main():
    """Main entry point for running the application."""
    import os

    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Run the application
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG and not settings.is_production(),
        log_level=settings.LOG_LEVEL.lower(),
        log_config=log_config,
        access_log=True
    )


if __name__ == "__main__":
    main()