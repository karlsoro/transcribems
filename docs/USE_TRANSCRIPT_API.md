# Use Transcript API Documentation

**Version:** 1.0.0
**Base URL:** `http://127.0.0.1:8000/v1`

## Overview

The Use Transcript API transforms completed transcripts into formatted documents using AI-powered content extraction and template-based formatting. Supports multiple output formats including text files and Microsoft Word documents.

## Features

- ✅ AI-powered content extraction using Claude
- ✅ Multiple template types (feature requests, meeting notes)
- ✅ Validation and completeness checking
- ✅ Preview before download
- ✅ Recording guidance scripts
- ✅ DOCX and text output formats

## Authentication

Currently no authentication required. Future versions will support API keys.

## Endpoints

### 1. List Available Templates

Get all available formatting templates.

```http
GET /v1/templates?type=all&active_only=true
```

**Query Parameters:**
- `type` (optional): Filter by template type (`system_request`, `general_meeting`, `project_meeting`)
- `active_only` (optional, default: true): Only return active templates

**Response:**
```json
{
  "templates": [
    {
      "id": "system-request-v1",
      "name": "System/Feature Request",
      "description": "Generate spec-kit compatible feature requests",
      "type": "system_request",
      "output_format": "txt",
      "version": "1.0.0",
      "required_fields": ["feature_name", "problem_statement", "acceptance_criteria"],
      "optional_fields": ["technical_constraints", "dependencies", "priority"],
      "has_guidance_script": true,
      "is_active": true
    }
  ]
}
```

### 2. Download Recording Guidance Script

Download a markdown guide for recording audio that will work well with a template.

```http
GET /v1/templates/{template_id}/script
```

**Path Parameters:**
- `template_id`: Template identifier (e.g., `system-request-v1`)

**Response:**
- Content-Type: `text/markdown`
- Content-Disposition: `attachment; filename="recording-guide-system-request.md"`

**Example:**
```bash
curl -O "http://127.0.0.1:8000/v1/templates/system-request-v1/script"
```

### 3. Submit Format Job

Submit a transcript for formatting with a specific template.

```http
POST /v1/format
Content-Type: application/json

{
  "transcript_id": "2912dd4c-055a-4872-990e-519edde30410",
  "template_id": "system-request-v1",
  "user_inputs": {
    "feature_name": "Use Transcript Feature",
    "priority": "high"
  }
}
```

**Request Body:**
- `transcript_id`: ID of completed transcription job
- `template_id`: Template to use for formatting
- `user_inputs`: Optional user-provided field values (override AI extraction)

**Response:**
```json
{
  "job_id": "format-a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "status": "pending",
  "estimated_time": 30
}
```

**Status Codes:**
- `200`: Job submitted successfully
- `404`: Transcript or template not found
- `400`: Transcript not completed or template inactive

### 4. Check Format Job Status

Get the current status of a formatting job.

```http
GET /v1/format/status/{job_id}
```

**Path Parameters:**
- `job_id`: Format job identifier

**Response:**
```json
{
  "job_id": "format-a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "status": "completed",
  "progress": 100,
  "validation_issues": [
    {
      "field": "acceptance_criteria",
      "severity": "warning",
      "message": "Field 'acceptance_criteria' may be too brief",
      "suggestion": "Consider providing more detail for acceptance_criteria"
    }
  ],
  "preview_available": true,
  "download_url": "/v1/format/download/format-a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "error_message": null
}
```

**Job Status Values:**
- `pending`: Job queued
- `processing`: AI extraction in progress
- `completed`: Ready for download
- `failed`: Job failed (see error_message)

**Validation Issue Severities:**
- `error`: Required field missing (critical)
- `warning`: Field may be incomplete (non-critical)
- `info`: Suggestions for improvement

### 5. Preview Formatted Content

Preview the formatted content before downloading.

```http
GET /v1/format/preview/{job_id}
```

**Path Parameters:**
- `job_id`: Format job identifier

**Response:**
```json
{
  "job_id": "format-a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "content": "# Feature Request: Use Transcript Feature\n\n## Problem Statement\nUsers need to transform transcripts into formatted documents...",
  "validation_issues": [...],
  "suggestions": [
    "Consider adding more acceptance criteria (aim for 3-5 specific conditions)",
    "Adding technical constraints would help implementation planning"
  ]
}
```

### 6. Download Formatted File

Download the final formatted document.

```http
GET /v1/format/download/{job_id}
```

**Path Parameters:**
- `job_id`: Format job identifier

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (for DOCX)
- Content-Type: `text/plain` (for text files)
- Content-Disposition: `attachment; filename="system_request_20251008_143022.txt"`

**Example:**
```bash
curl -O "http://127.0.0.1:8000/v1/format/download/format-a1b2c3d4"
```

## Template Types

### System/Feature Request

**Template ID:** `system-request-v1`
**Output Format:** Text (.txt)
**Best For:** Creating spec-kit compatible feature requests

**Required Fields:**
- `feature_name`: Clear, concise feature title
- `problem_statement`: What problem are you solving
- `proposed_solution`: High-level approach
- `acceptance_criteria`: Specific conditions that define done

**Optional Fields:**
- `target_users`: Who will use this feature
- `technical_constraints`: Technical limitations or requirements
- `dependencies`: Other systems or features required
- `priority`: Business urgency (High, Medium, Low)

**Example User Inputs:**
```json
{
  "feature_name": "OAuth2 Authentication",
  "priority": "High"
}
```

### General Meeting Notes

**Template ID:** `general-meeting-v1`
**Output Format:** Microsoft Word (.docx)
**Best For:** Standard team meeting notes

**Required Fields:**
- `meeting_date`: Date and time of meeting
- `attendees`: List of participants
- `discussion_topics`: Main topics discussed
- `action_items`: Tasks with owners

**Optional Fields:**
- `decisions`: Key decisions made
- `next_steps`: Planned activities
- `parking_lot`: Deferred topics

### Project Meeting Notes

**Template ID:** `project-meeting-v1`
**Output Format:** Microsoft Word (.docx)
**Best For:** Detailed project status meetings

**Required Fields:**
- `project_name`: Name of the project
- `meeting_date`: Date and time
- `attendees`: Participants with roles
- `status_updates`: Progress on deliverables
- `action_items`: Tasks with owners and due dates

**Optional Fields:**
- `risks_issues`: Current blockers
- `decisions`: Key decisions with rationale
- `next_meeting`: Date and focus areas

## Complete Workflow Example

### Step 1: Record and Transcribe Audio

```bash
# Upload audio file for transcription
curl -X POST "http://127.0.0.1:8000/v1/transcribe/sse" \
  -F "audio_file=@meeting.wav" \
  -F "language=auto" \
  -F "enable_speaker_diarization=true"

# Response: {"job_id": "2912dd4c-055a-4872-990e-519edde30410"}
```

### Step 2: List Available Templates

```bash
curl "http://127.0.0.1:8000/v1/templates"
```

### Step 3: Download Recording Guidance (Optional)

```bash
curl -O "http://127.0.0.1:8000/v1/templates/system-request-v1/script"
```

### Step 4: Submit Format Job

```bash
curl -X POST "http://127.0.0.1:8000/v1/format" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_id": "2912dd4c-055a-4872-990e-519edde30410",
    "template_id": "system-request-v1",
    "user_inputs": {
      "feature_name": "Automated Meeting Notes",
      "priority": "High"
    }
  }'

# Response: {"job_id": "format-xyz123", "status": "pending", "estimated_time": 30}
```

### Step 5: Check Status

```bash
curl "http://127.0.0.1:8000/v1/format/status/format-xyz123"
```

### Step 6: Preview Content

```bash
curl "http://127.0.0.1:8000/v1/format/preview/format-xyz123"
```

### Step 7: Download File

```bash
curl -O "http://127.0.0.1:8000/v1/format/download/format-xyz123"
```

## Error Handling

### Common Error Responses

**404 - Not Found:**
```json
{
  "detail": "Transcript 2912dd4c-055a-4872-990e-519edde30410 not found"
}
```

**400 - Bad Request:**
```json
{
  "detail": "Transcript 2912dd4c-055a-4872-990e-519edde30410 is not completed"
}
```

**500 - Server Error:**
```json
{
  "detail": "Internal server error processing format job"
}
```

## Environment Variables

Required configuration for LLM integration:

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: OpenAI (future support)
# export OPENAI_API_KEY="sk-..."
```

## Rate Limits

Currently no rate limits. Future versions may implement:
- 100 format jobs per hour per user
- 1000 template list requests per hour

## Best Practices

### 1. Recording Quality Audio

- Use a quality microphone
- Speak clearly and at moderate pace
- State names when people speak
- Explicitly mark decisions and action items
- Download and review the guidance script before recording

### 2. Using User Inputs

- Provide known values in `user_inputs` to save AI processing
- User inputs always override AI extraction
- Use for values the AI might not extract correctly

### 3. Handling Validation Issues

- Review all `error` severity issues before downloading
- Address `warning` issues for higher quality output
- Use `suggestions` to improve content completeness

### 4. Template Selection

- Use System Request for new features/capabilities
- Use General Meeting for routine team meetings
- Use Project Meeting for status-heavy project discussions

## Frontend Integration

### React/TypeScript Example

```typescript
import { useState } from 'react';

interface FormatJob {
  job_id: string;
  status: string;
  estimated_time: number;
}

async function formatTranscript(
  transcriptId: string,
  templateId: string
): Promise<FormatJob> {
  const response = await fetch('http://127.0.0.1:8000/v1/format', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transcript_id: transcriptId,
      template_id: templateId,
      user_inputs: {}
    })
  });

  if (!response.ok) {
    throw new Error(`Format failed: ${response.statusText}`);
  }

  return response.json();
}

async function pollJobStatus(jobId: string): Promise<void> {
  const response = await fetch(
    `http://127.0.0.1:8000/v1/format/status/${jobId}`
  );
  const status = await response.json();

  if (status.status === 'completed') {
    window.location.href = status.download_url;
  } else if (status.status === 'failed') {
    throw new Error(status.error_message);
  } else {
    // Poll again in 2 seconds
    setTimeout(() => pollJobStatus(jobId), 2000);
  }
}
```

## Support

For issues or questions:
- GitHub: https://github.com/karlsoro/transcribems
- Documentation: [docs/](../docs/)

---

**Version History:**
- 1.0.0 (2025-10-08): Initial release with three template types
