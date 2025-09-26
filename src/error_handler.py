"""MCP error handler for structured error responses.

Provides standardized error responses following MCP protocol.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .models.types import MCPErrorResponse, MCPError, MCPErrorDetails, SUPPORTED_AUDIO_FORMATS, MAX_FILE_SIZE


class MCPErrorHandler:
    """Handler for creating standardized MCP error responses."""

    def file_not_found(self, file_path: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FILE_NOT_FOUND error response."""
        error = MCPError(
            code="FILE_NOT_FOUND",
            message="The specified audio file does not exist or is not accessible",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Verify the file path exists and Claude Code has read permissions",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def file_too_large(self, file_path: str, file_size: int, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create FILE_TOO_LARGE error response."""
        error = MCPError(
            code="FILE_TOO_LARGE",
            message="Audio file exceeds maximum size limit of 1GB",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Split the audio file into smaller chunks or compress the file",
                http_equivalent=413,
                max_size_bytes=MAX_FILE_SIZE
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def unsupported_format(self, file_path: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create UNSUPPORTED_FORMAT error response."""
        error = MCPError(
            code="UNSUPPORTED_FORMAT",
            message="Audio format is not supported",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Convert the audio file to a supported format",
                http_equivalent=415,
                supported_formats=SUPPORTED_AUDIO_FORMATS
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def job_not_found(self, job_id: str) -> Dict[str, Any]:
        """Create JOB_NOT_FOUND error response."""
        error = MCPError(
            code="JOB_NOT_FOUND",
            message="The specified transcription job was not found",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Verify the job ID is correct",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def transcription_failed(self, error_message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create TRANSCRIPTION_FAILED error response."""
        error = MCPError(
            code="TRANSCRIPTION_FAILED",
            message="Transcription processing failed",
            details=MCPErrorDetails(
                error_type="processing_error",
                user_action="Try again with a different model size or check audio quality",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def batch_too_large(self, file_count: int, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create BATCH_TOO_LARGE error response."""
        error = MCPError(
            code="BATCH_TOO_LARGE",
            message="Batch contains too many files",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Split into smaller batches with 10 or fewer files",
                http_equivalent=413
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def server_overloaded(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create SERVER_OVERLOADED error response."""
        error = MCPError(
            code="SERVER_OVERLOADED",
            message="Server is currently processing too many jobs",
            details=MCPErrorDetails(
                error_type="capacity_error",
                user_action="Wait and retry, or check job queue status",
                http_equivalent=503,
                retry_after=30
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_file(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_FILE error response."""
        error = MCPError(
            code="INVALID_FILE",
            message=f"Audio file validation failed: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Ensure the file is a valid audio file with proper format",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def invalid_parameters(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INVALID_PARAMETERS error response."""
        error = MCPError(
            code="INVALID_PARAMETERS",
            message=f"Invalid parameters provided: {message}",
            details=MCPErrorDetails(
                error_type="validation_error",
                user_action="Check the parameter values and try again",
                http_equivalent=400
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def internal_error(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create INTERNAL_ERROR error response."""
        error = MCPError(
            code="INTERNAL_ERROR",
            message=f"An internal server error occurred: {message}",
            details=MCPErrorDetails(
                error_type="server_error",
                user_action="Try again later or contact support if the problem persists",
                http_equivalent=500
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()

    def result_not_found(self, message: str, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RESULT_NOT_FOUND error response."""
        error = MCPError(
            code="RESULT_NOT_FOUND",
            message=f"Transcription result not found: {message}",
            details=MCPErrorDetails(
                error_type="not_found_error",
                user_action="Ensure the job completed successfully before requesting results",
                http_equivalent=404
            )
        )

        response = MCPErrorResponse(
            error=error,
            job_id=job_id,
            timestamp=datetime.utcnow().isoformat()
        )

        return response.dict()