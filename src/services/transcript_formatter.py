"""
Transcript formatting service with AI-powered content extraction.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.core.logging import get_logger
from src.core.llm_client import get_llm_client
from src.models.template import (
    Template,
    ValidationIssue,
    ValidationResult,
    ExtractedContent,
    FormatJob
)
from src.services.job_storage import get_job_storage

logger = get_logger(__name__)


class TranscriptFormatterService:
    """Service for formatting transcripts using templates and AI."""

    def __init__(self):
        """Initialize transcript formatter service."""
        self.llm_client = get_llm_client()
        logger.info("TranscriptFormatterService initialized")

    async def format_transcript(
        self,
        transcript_id: str,
        template: Template,
        user_inputs: Dict[str, Any]
    ) -> FormatJob:
        """Format a transcript using specified template.

        Args:
            transcript_id: ID of transcript to format
            template: Template to use for formatting
            user_inputs: User-provided field values

        Returns:
            FormatJob tracking the formatting process
        """
        job_id = str(uuid.uuid4())
        job = FormatJob(
            id=job_id,
            transcript_id=transcript_id,
            template_id=template.id,
            status="pending",
            progress=0
        )

        try:
            # Get transcript data
            job_storage = get_job_storage()
            transcript_job = await job_storage.get_job(transcript_id)

            if not transcript_job:
                raise ValueError(f"Transcript {transcript_id} not found")

            if transcript_job.get("status") != "completed":
                raise ValueError(f"Transcript {transcript_id} is not completed")

            # Extract transcript text
            result = transcript_job.get("result", {})
            transcript_text = result.get("text", "")
            segments = result.get("segments", [])

            if not transcript_text:
                raise ValueError("Transcript has no text content")

            # Update job status
            job.status = "processing"
            job.progress = 10
            logger.info(f"Starting format job {job_id} for transcript {transcript_id}")

            # Extract content using AI
            extracted = await self._extract_content(
                transcript_text,
                segments,
                template,
                user_inputs
            )

            job.progress = 50

            # Validate extracted content
            validation = await self.validate_content(
                extracted.raw_fields,
                template.required_fields
            )

            job.validation_issues = validation.issues
            job.progress = 70

            # Generate preview
            preview = await self._generate_preview(
                extracted.raw_fields,
                template
            )

            job.preview_data = {
                "content": preview,
                "extracted_fields": extracted.raw_fields,
                "confidence_scores": extracted.confidence_scores
            }

            job.progress = 90

            # Mark as completed (actual file generation happens on download)
            job.status = "completed"
            job.progress = 100
            job.updated_at = datetime.utcnow()

            logger.info(f"Format job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Format job {job_id} failed: {e}", exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            job.updated_at = datetime.utcnow()

        return job

    async def _extract_content(
        self,
        transcript_text: str,
        segments: List[Dict],
        template: Template,
        user_inputs: Dict[str, Any]
    ) -> ExtractedContent:
        """Extract structured content from transcript.

        Args:
            transcript_text: Full transcript text
            segments: Transcript segments with speakers
            template: Template configuration
            user_inputs: User-provided values

        Returns:
            Extracted content with confidence scores
        """
        # Use LLM for intelligent extraction
        result = await self.llm_client.extract_content(
            transcript_text=transcript_text,
            template_type=template.type,
            required_fields=template.required_fields,
            optional_fields=template.optional_fields,
            user_inputs=user_inputs
        )

        # Merge user inputs (they take precedence)
        extracted_fields = result.get("extracted_fields", {})
        extracted_fields.update(user_inputs)

        # Add metadata
        metadata = {
            "template_id": template.id,
            "template_version": template.version,
            "transcript_length": len(transcript_text),
            "segments_count": len(segments),
            "extraction_timestamp": datetime.utcnow().isoformat()
        }

        return ExtractedContent(
            raw_fields=extracted_fields,
            confidence_scores=result.get("confidence_scores", {}),
            metadata=metadata
        )

    async def validate_content(
        self,
        content: Dict[str, Any],
        required_fields: List[str]
    ) -> ValidationResult:
        """Validate extracted content completeness.

        Args:
            content: Extracted content fields
            required_fields: Required field names

        Returns:
            Validation result with issues
        """
        issues = []
        fields_present = 0
        total_fields = len(required_fields)

        for field in required_fields:
            value = content.get(field)

            if not value or (isinstance(value, str) and not value.strip()):
                issues.append(ValidationIssue(
                    field=field,
                    severity="error",
                    message=f"Required field '{field}' is missing or empty",
                    suggestion=f"Please provide a value for {field}"
                ))
            else:
                fields_present += 1

                # Check for very short values
                if isinstance(value, str) and len(value.strip()) < 10:
                    issues.append(ValidationIssue(
                        field=field,
                        severity="warning",
                        message=f"Field '{field}' may be too brief",
                        suggestion=f"Consider providing more detail for {field}"
                    ))

        completeness = (fields_present / total_fields * 100) if total_fields > 0 else 100

        return ValidationResult(
            is_valid=len([i for i in issues if i.severity == "error"]) == 0,
            issues=issues,
            completeness_score=completeness
        )

    async def generate_suggestions(
        self,
        content: Dict[str, Any],
        template: Template
    ) -> List[str]:
        """Generate suggestions for improving content.

        Args:
            content: Extracted content
            template: Template configuration

        Returns:
            List of suggestions
        """
        suggestions = []

        # Check for specific template types
        if template.type == "system_request":
            if "acceptance_criteria" in content:
                criteria = content["acceptance_criteria"]
                if isinstance(criteria, str) and len(criteria.split("\n")) < 3:
                    suggestions.append(
                        "Consider adding more acceptance criteria (aim for 3-5 specific conditions)"
                    )

            if "technical_constraints" not in content or not content.get("technical_constraints"):
                suggestions.append(
                    "Adding technical constraints would help implementation planning"
                )

            if "dependencies" not in content or not content.get("dependencies"):
                suggestions.append(
                    "Consider documenting any dependencies on other systems or features"
                )

        elif template.type in ["general_meeting", "project_meeting"]:
            if "action_items" in content:
                items = content["action_items"]
                if isinstance(items, str) and "owner" not in items.lower():
                    suggestions.append(
                        "Action items should include clear owners/assignees"
                    )

            if "decisions" not in content or not content.get("decisions"):
                suggestions.append(
                    "Document key decisions made during the meeting"
                )

        return suggestions

    async def _generate_preview(
        self,
        content: Dict[str, Any],
        template: Template
    ) -> str:
        """Generate text preview of formatted content.

        Args:
            content: Extracted content
            template: Template configuration

        Returns:
            Preview text
        """
        if template.type == "system_request":
            return self._preview_system_request(content)
        elif template.type == "general_meeting":
            return self._preview_general_meeting(content)
        elif template.type == "project_meeting":
            return self._preview_project_meeting(content)
        else:
            return "\n".join(f"{k}: {v}" for k, v in content.items())

    def _preview_system_request(self, content: Dict[str, Any]) -> str:
        """Generate preview for system request."""
        preview = f"""# Feature Request: {content.get('feature_name', 'Untitled')}

## Problem Statement
{content.get('problem_statement', '[Not provided]')}

## Proposed Solution
{content.get('proposed_solution', '[Not provided]')}

## Acceptance Criteria
{content.get('acceptance_criteria', '[Not provided]')}

## Technical Constraints
{content.get('technical_constraints', '[Not provided]')}

## Dependencies
{content.get('dependencies', '[Not provided]')}

## Priority
{content.get('priority', '[Not provided]')}
"""
        return preview

    def _preview_general_meeting(self, content: Dict[str, Any]) -> str:
        """Generate preview for general meeting notes."""
        preview = f"""# Meeting Notes

**Date:** {content.get('meeting_date', '[Not provided]')}
**Attendees:** {content.get('attendees', '[Not provided]')}

## Discussion Topics
{content.get('discussion_topics', '[Not provided]')}

## Key Decisions
{content.get('decisions', '[Not provided]')}

## Action Items
{content.get('action_items', '[Not provided]')}

## Next Steps
{content.get('next_steps', '[Not provided]')}
"""
        return preview

    def _preview_project_meeting(self, content: Dict[str, Any]) -> str:
        """Generate preview for project meeting notes."""
        preview = f"""# Project Meeting Notes: {content.get('project_name', 'Untitled')}

**Date:** {content.get('meeting_date', '[Not provided]')}
**Attendees:** {content.get('attendees', '[Not provided]')}

## Status Updates
{content.get('status_updates', '[Not provided]')}

## Risks & Issues
{content.get('risks_issues', '[Not provided]')}

## Decisions Made
{content.get('decisions', '[Not provided]')}

## Action Items
{content.get('action_items', '[Not provided]')}

## Next Meeting
{content.get('next_meeting', '[Not provided]')}
"""
        return preview
