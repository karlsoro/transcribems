"""
REST API endpoints for transcript formatting.
"""

import asyncio
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse

from src.core.logging import get_logger
from src.models.template import (
    FormatRequest,
    FormatResponse,
    FormatStatusResponse,
    FormatPreviewResponse,
    TemplateListResponse
)
from src.services.template_database import get_template_db
from src.services.format_job_storage import get_format_job_storage
from src.services.transcript_formatter import TranscriptFormatterService
from src.services.document_generator import DocumentGeneratorService
from src.services.script_generator import ScriptGeneratorService
from src.services.job_storage import get_job_storage

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["formatting"])


async def _format_transcript_background(
    job_id: str,
    transcript_id: str,
    template_id: str,
    user_inputs: dict
):
    """Background task for formatting transcript.

    Args:
        job_id: Format job ID
        transcript_id: Transcript to format
        template_id: Template to use
        user_inputs: User-provided values
    """
    try:
        template_db = await get_template_db()
        job_storage = await get_format_job_storage()
        formatter = TranscriptFormatterService()

        # Get template
        template = await template_db.get_template(template_id)
        if not template:
            await job_storage.update_job_status(
                job_id, "failed", 0, f"Template {template_id} not found"
            )
            return

        # Format transcript
        job = await formatter.format_transcript(transcript_id, template, user_inputs)

        # Save job
        await job_storage.save_job(job)

        logger.info(f"Background format job {job_id} completed with status: {job.status}")

    except Exception as e:
        logger.error(f"Background format job {job_id} failed: {e}", exc_info=True)
        job_storage = await get_format_job_storage()
        await job_storage.update_job_status(job_id, "failed", 0, str(e))


@router.get("/transcripts")
async def list_transcripts():
    """List available transcripts.

    Returns:
        List of completed transcripts
    """
    try:
        job_storage = get_job_storage()

        # Get all completed transcription jobs
        # Note: This is a simplified implementation
        # In production, you'd want pagination and filtering
        transcripts = []

        # For now, return basic structure
        # Frontend can adapt to use existing job storage
        return {
            "transcripts": transcripts,
            "note": "Use existing /v1/jobs endpoint to list transcription jobs"
        }

    except Exception as e:
        logger.error(f"Failed to list transcripts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    type: Optional[str] = None,
    active_only: bool = True
):
    """List available templates.

    Args:
        type: Filter by template type (system_request, general_meeting, project_meeting)
        active_only: Only return active templates

    Returns:
        List of available templates
    """
    try:
        template_db = await get_template_db()
        templates = await template_db.list_templates(type=type, active_only=active_only)

        # Add has_guidance_script flag
        for template in templates:
            template_dict = template.dict()
            template_dict["has_guidance_script"] = bool(template.script_path)

        return TemplateListResponse(templates=templates)

    except Exception as e:
        logger.error(f"Failed to list templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/format", response_model=FormatResponse)
async def format_transcript(
    request: FormatRequest,
    background_tasks: BackgroundTasks
):
    """Submit a transcript for formatting.

    Args:
        request: Format request with transcript ID and template ID
        background_tasks: FastAPI background tasks

    Returns:
        Format job information
    """
    try:
        # Validate transcript exists
        job_storage = get_job_storage()
        transcript = await job_storage.get_job(request.transcript_id)

        if not transcript:
            raise HTTPException(
                status_code=404,
                detail=f"Transcript {request.transcript_id} not found"
            )

        if transcript.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Transcript {request.transcript_id} is not completed"
            )

        # Validate template exists
        template_db = await get_template_db()
        template = await template_db.get_template(request.template_id)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {request.template_id} not found"
            )

        if not template.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"Template {request.template_id} is not active"
            )

        # Create format job
        import uuid
        job_id = f"format-{uuid.uuid4()}"

        # Save initial job state
        from src.models.template import FormatJob
        format_job = FormatJob(
            id=job_id,
            transcript_id=request.transcript_id,
            template_id=request.template_id,
            status="pending",
            progress=0
        )

        format_job_storage = await get_format_job_storage()
        await format_job_storage.save_job(format_job)

        # Start background processing
        background_tasks.add_task(
            _format_transcript_background,
            job_id,
            request.transcript_id,
            request.template_id,
            request.user_inputs
        )

        logger.info(f"Format job {job_id} submitted for transcript {request.transcript_id}")

        return FormatResponse(
            job_id=job_id,
            status="pending",
            estimated_time=30  # Estimate 30 seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit format job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/format/status/{job_id}", response_model=FormatStatusResponse)
async def get_format_status(job_id: str):
    """Get format job status.

    Args:
        job_id: Format job identifier

    Returns:
        Current job status and progress
    """
    try:
        job_storage = await get_format_job_storage()
        job = await job_storage.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Format job {job_id} not found")

        download_url = None
        if job.status == "completed":
            download_url = f"/v1/format/download/{job_id}"

        return FormatStatusResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            validation_issues=job.validation_issues,
            preview_available=job.status == "completed",
            download_url=download_url,
            error_message=job.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get format status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/format/preview/{job_id}", response_model=FormatPreviewResponse)
async def preview_formatted_content(job_id: str):
    """Preview formatted content before downloading.

    Args:
        job_id: Format job identifier

    Returns:
        Preview of formatted content with validation info
    """
    try:
        job_storage = await get_format_job_storage()
        job = await job_storage.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Format job {job_id} not found")

        if job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Format job is {job.status}, preview not available yet"
            )

        if not job.preview_data:
            raise HTTPException(status_code=500, detail="Preview data not available")

        # Generate suggestions
        formatter = TranscriptFormatterService()
        template_db = await get_template_db()
        template = await template_db.get_template(job.template_id)

        suggestions = []
        if template:
            extracted_fields = job.preview_data.get("extracted_fields", {})
            suggestions = await formatter.generate_suggestions(extracted_fields, template)

        return FormatPreviewResponse(
            job_id=job.id,
            content=job.preview_data.get("content", ""),
            validation_issues=job.validation_issues,
            suggestions=suggestions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/format/download/{job_id}")
async def download_formatted_file(job_id: str):
    """Download formatted file.

    Args:
        job_id: Format job identifier

    Returns:
        Formatted file (DOCX or text)
    """
    try:
        job_storage = await get_format_job_storage()
        job = await job_storage.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Format job {job_id} not found")

        if job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Format job is {job.status}, file not ready"
            )

        # Get template
        template_db = await get_template_db()
        template = await template_db.get_template(job.template_id)

        if not template:
            raise HTTPException(status_code=500, detail="Template not found")

        # Generate document
        doc_generator = DocumentGeneratorService()
        extracted_fields = job.preview_data.get("extracted_fields", {})

        # Create output directory
        output_dir = Path("format_output")
        output_dir.mkdir(exist_ok=True)

        # Generate filename
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{template.type}_{timestamp}.{template.output_format}"
        output_path = output_dir / filename

        # Generate document
        doc_bytes = await doc_generator.generate_document(
            template,
            extracted_fields,
            output_path
        )

        # Update job with output path
        job.output_file_path = str(output_path)
        await job_storage.save_job(job)

        # Determine media type
        if template.output_format == "docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            media_type = "text/plain"

        logger.info(f"Format job {job_id} file downloaded: {filename}")

        # Return file
        return StreamingResponse(
            iter([doc_bytes]),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}/script")
async def download_template_script(template_id: str):
    """Download recording guidance script for a template.

    Args:
        template_id: Template identifier

    Returns:
        Markdown guidance script
    """
    try:
        # Get template
        template_db = await get_template_db()
        template = await template_db.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

        # Get or generate script
        script_generator = ScriptGeneratorService()
        script_content = await script_generator.get_script(template)

        if not script_content:
            raise HTTPException(
                status_code=404,
                detail=f"No guidance script available for template {template_id}"
            )

        # Save script if not already saved
        if not template.script_path or not Path(template.script_path).exists():
            script_path = await script_generator.save_script(template, script_content)
            template.script_path = str(script_path)
            await template_db.add_template(template)

        filename = f"recording-guide-{template.type}.md"

        logger.info(f"Template script downloaded: {template_id}")

        # Return script as downloadable file
        return StreamingResponse(
            iter([script_content.encode("utf-8")]),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download script: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
