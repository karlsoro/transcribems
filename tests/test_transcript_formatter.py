"""
Tests for transcript formatting functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.transcript_formatter import TranscriptFormatterService
from src.models.template import Template, ValidationIssue


@pytest.fixture
def sample_template():
    """Sample template for testing."""
    return Template(
        id="test-template-v1",
        name="Test Template",
        description="Test template for unit tests",
        type="system_request",
        file_path="templates/test.json",
        output_format="txt",
        version="1.0.0",
        required_fields=["feature_name", "problem_statement"],
        optional_fields=["priority"],
        script_path="templates/scripts/test_guide.md",
        is_active=True
    )


@pytest.fixture
def sample_transcript():
    """Sample transcript data."""
    return {
        "id": "transcript-123",
        "status": "completed",
        "result": {
            "text": "We need a new user authentication system that supports OAuth2.",
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "We need a new user authentication system",
                    "speaker": "SPEAKER_01"
                },
                {
                    "start": 5.0,
                    "end": 8.0,
                    "text": "that supports OAuth2",
                    "speaker": "SPEAKER_01"
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_validate_content_missing_required():
    """Test content validation with missing required fields."""
    formatter = TranscriptFormatterService()

    content = {"feature_name": "Test Feature"}
    required_fields = ["feature_name", "problem_statement", "acceptance_criteria"]

    result = await formatter.validate_content(content, required_fields)

    assert result.is_valid is False
    assert len(result.issues) >= 2
    assert any(issue.field == "problem_statement" for issue in result.issues)
    assert any(issue.field == "acceptance_criteria" for issue in result.issues)


@pytest.mark.asyncio
async def test_validate_content_all_present():
    """Test content validation with all required fields."""
    formatter = TranscriptFormatterService()

    content = {
        "feature_name": "OAuth2 Authentication",
        "problem_statement": "Users need to authenticate using their corporate credentials",
        "acceptance_criteria": "Users can sign in with Microsoft or Google accounts"
    }
    required_fields = ["feature_name", "problem_statement", "acceptance_criteria"]

    result = await formatter.validate_content(content, required_fields)

    assert result.is_valid is True
    assert result.completeness_score == 100


@pytest.mark.asyncio
async def test_validate_content_brief_values():
    """Test content validation detects brief values."""
    formatter = TranscriptFormatterService()

    content = {
        "feature_name": "Auth",  # Too brief
        "problem_statement": "Need auth",  # Too brief
    }
    required_fields = ["feature_name", "problem_statement"]

    result = await formatter.validate_content(content, required_fields)

    # Should have warnings for brief content
    warnings = [issue for issue in result.issues if issue.severity == "warning"]
    assert len(warnings) >= 2


@pytest.mark.asyncio
async def test_generate_suggestions_system_request():
    """Test suggestion generation for system requests."""
    formatter = TranscriptFormatterService()

    template = Template(
        id="system-request-v1",
        name="System Request",
        type="system_request",
        file_path="templates/system_request.json",
        output_format="txt",
        version="1.0.0",
        required_fields=["feature_name"],
        optional_fields=[]
    )

    content = {
        "feature_name": "New Feature",
        "acceptance_criteria": "It works"  # Too brief
    }

    suggestions = await formatter.generate_suggestions(content, template)

    assert len(suggestions) > 0
    # Should suggest more acceptance criteria
    assert any("acceptance criteria" in s.lower() for s in suggestions)


@pytest.mark.asyncio
async def test_preview_system_request():
    """Test preview generation for system request."""
    formatter = TranscriptFormatterService()

    content = {
        "feature_name": "OAuth2 Authentication",
        "problem_statement": "Users need corporate login",
        "proposed_solution": "Integrate OAuth2",
        "acceptance_criteria": "Users can sign in with Microsoft",
        "priority": "High"
    }

    preview = formatter._preview_system_request(content)

    assert "OAuth2 Authentication" in preview
    assert "Users need corporate login" in preview
    assert "Integrate OAuth2" in preview
    assert "High" in preview


@pytest.mark.asyncio
async def test_preview_general_meeting():
    """Test preview generation for general meeting."""
    formatter = TranscriptFormatterService()

    content = {
        "meeting_date": "2025-10-08",
        "attendees": "John, Sarah, Mike",
        "discussion_topics": "Project status and next steps",
        "decisions": "Approved budget increase",
        "action_items": "John to update documentation"
    }

    preview = formatter._preview_general_meeting(content)

    assert "2025-10-08" in preview
    assert "John, Sarah, Mike" in preview
    assert "Project status" in preview
    assert "Approved budget" in preview


@pytest.mark.asyncio
async def test_preview_project_meeting():
    """Test preview generation for project meeting."""
    formatter = TranscriptFormatterService()

    content = {
        "project_name": "Authentication System",
        "meeting_date": "2025-10-08",
        "attendees": "Team members",
        "status_updates": "80% complete",
        "risks_issues": "Security review pending",
        "decisions": "Move to production next week",
        "action_items": "Complete security review"
    }

    preview = formatter._preview_project_meeting(content)

    assert "Authentication System" in preview
    assert "80% complete" in preview
    assert "Security review pending" in preview
    assert "Move to production" in preview


def test_validation_issue_creation():
    """Test ValidationIssue model."""
    issue = ValidationIssue(
        field="test_field",
        severity="error",
        message="Field is missing",
        suggestion="Please provide a value"
    )

    assert issue.field == "test_field"
    assert issue.severity == "error"
    assert issue.message == "Field is missing"
    assert issue.suggestion == "Please provide a value"
