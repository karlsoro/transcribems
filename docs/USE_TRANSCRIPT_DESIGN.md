# Use Transcript Feature - System Design

**Version:** 1.0.0
**Date:** October 8, 2025
**Status:** Design Phase

## Overview

The Use Transcript feature transforms transcribed audio into formatted documents based on user-selected templates. It provides intelligent formatting with AI-powered content extraction and validation.

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  - Transcript Selector (dropdown)                           │
│  - Template Selector (dropdown)                             │
│  - Script Downloader (guidance documents)                   │
│  - Preview & Download                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     REST API Layer                           │
│  - GET /v1/transcripts (list available)                     │
│  - GET /v1/templates (list available templates)             │
│  - POST /v1/format (format transcript with template)        │
│  - GET /v1/templates/{id}/script (download guidance)        │
│  - GET /v1/format/preview/{job_id} (preview formatted)      │
│  - GET /v1/format/download/{job_id} (download file)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │ Template Manager │  │ Transcript Formatter Service    │ │
│  │ - Load templates │  │ - AI-powered extraction         │ │
│  │ - Validate       │  │ - Content validation            │ │
│  │ - List available │  │ - Missing info detection        │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
│                                                              │
│  ┌──────────────────┐  ┌─────────────────────────────────┐ │
│  │ Document         │  │ Script Generator                │ │
│  │ Generator        │  │ - Generate guidance docs        │ │
│  │ - DOCX creation  │  │ - Template-specific scripts     │ │
│  │ - Text files     │  │ - Requirements checklists       │ │
│  └──────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                             │
│  - Templates DB (metadata)                                   │
│  - Template Files (.dotx, .json configs)                    │
│  - Formatted Output Cache                                    │
│  - Transcripts (from existing system)                        │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Templates Table
```sql
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL,  -- 'system_request', 'general_meeting', 'project_meeting'
    file_path TEXT NOT NULL,  -- Path to .dotx or template config
    output_format TEXT NOT NULL,  -- 'docx', 'txt', 'md'
    version TEXT NOT NULL,
    required_fields TEXT,  -- JSON array of required fields
    optional_fields TEXT,  -- JSON array of optional fields
    script_path TEXT,  -- Path to guidance script file
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_templates_type ON templates(type);
CREATE INDEX idx_templates_active ON templates(is_active);
```

### Format Jobs Table
```sql
CREATE TABLE format_jobs (
    id TEXT PRIMARY KEY,
    transcript_id TEXT NOT NULL,  -- References job_storage
    template_id TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    progress INTEGER DEFAULT 0,
    output_file_path TEXT,
    preview_data TEXT,  -- JSON preview of formatted content
    validation_issues TEXT,  -- JSON array of missing/invalid fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates(id)
);

CREATE INDEX idx_format_jobs_status ON format_jobs(status);
CREATE INDEX idx_format_jobs_transcript ON format_jobs(transcript_id);
```

## Template Types

### 1. System/Feature Request
**Output:** Text file (.txt or .md)
**Purpose:** Generate spec-kit compatible feature requests

**Required Fields:**
- Feature name/title
- Problem statement
- Proposed solution
- Acceptance criteria
- Technical constraints
- Dependencies

**AI Processing:**
- Extract key requirements from transcript
- Structure into spec-kit format
- Validate completeness
- Flag missing critical information

**Guidance Script Content:**
```markdown
# System/Feature Request Recording Guide

To ensure high-quality feature requests, please cover:

## Required Information:
1. **Feature Name**: Clear, concise title
2. **Problem Statement**: What problem are you solving?
3. **Target Users**: Who will use this feature?
4. **Proposed Solution**: High-level approach
5. **Acceptance Criteria**: How do we know it's done?
6. **Technical Constraints**: Any limitations or requirements?
7. **Dependencies**: What else is needed?
8. **Priority**: Business urgency

## Tips:
- Speak clearly and provide specific examples
- Mention any related systems or integrations
- Discuss edge cases and error scenarios
- Include performance requirements if applicable
```

### 2. General Meeting Notes
**Output:** MS Word document (.docx)
**Template:** `/templates/meeting_notes.dotx`

**Required Fields:**
- Meeting date/time
- Attendees
- Key discussion points
- Action items
- Decisions made

**AI Processing:**
- Identify speakers and attendees
- Extract discussion topics
- Detect action items and owners
- Summarize decisions

### 3. Project Meeting Notes
**Output:** MS Word document (.docx)
**Template:** `/templates/project_meeting_notes.dotx`

**Required Fields:**
- Project name
- Meeting date/time
- Attendees with roles
- Agenda items covered
- Status updates
- Risks and issues
- Action items with owners and due dates
- Next steps

**AI Processing:**
- Structure by project phases
- Track commitments and deadlines
- Identify blockers and risks
- Extract milestone updates

**Guidance Script Content:**
```markdown
# Project Meeting Recording Guide

For effective project meeting notes, ensure you cover:

## Required Information:
1. **Project Context**: Project name and phase
2. **Attendees**: Names and roles
3. **Status Updates**: Progress on deliverables
4. **Risks/Issues**: Current blockers or concerns
5. **Action Items**: Who will do what by when
6. **Decisions**: Key decisions and rationale
7. **Next Meeting**: Date and focus areas

## Structure Your Discussion:
1. Review previous action items
2. Status updates from each team
3. Current risks and mitigation
4. New action items
5. Parking lot items
6. Next steps

## Tips:
- State names clearly when speaking
- Use phrases like "Action item for [Name]..."
- Explicitly state decisions: "We've decided to..."
- Mention due dates for action items
```

## API Endpoints

### List Available Transcripts
```http
GET /v1/transcripts
```

**Response:**
```json
{
  "transcripts": [
    {
      "id": "uuid",
      "filename": "meeting_2025-10-08.wav",
      "created_at": "2025-10-08T10:30:00Z",
      "duration": 3600,
      "speakers_count": 5,
      "segments_count": 782
    }
  ]
}
```

### List Available Templates
```http
GET /v1/templates?type=all&active_only=true
```

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
      "has_guidance_script": true,
      "required_fields": ["feature_name", "problem_statement", "acceptance_criteria"]
    },
    {
      "id": "general-meeting-v1",
      "name": "General Meeting Notes",
      "description": "Standard meeting notes with action items",
      "type": "general_meeting",
      "output_format": "docx",
      "has_guidance_script": false
    }
  ]
}
```

### Format Transcript
```http
POST /v1/format
Content-Type: application/json

{
  "transcript_id": "uuid",
  "template_id": "system-request-v1",
  "user_inputs": {
    "feature_name": "Use Transcript Feature",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "job_id": "format-uuid",
  "status": "processing",
  "estimated_time": 30
}
```

### Get Format Job Status
```http
GET /v1/format/status/{job_id}
```

**Response:**
```json
{
  "job_id": "format-uuid",
  "status": "completed",
  "progress": 100,
  "validation_issues": [
    {
      "field": "acceptance_criteria",
      "severity": "warning",
      "message": "Acceptance criteria may be incomplete. Consider adding more specific conditions."
    }
  ],
  "preview_available": true,
  "download_url": "/v1/format/download/format-uuid"
}
```

### Preview Formatted Content
```http
GET /v1/format/preview/{job_id}
```

**Response:**
```json
{
  "job_id": "format-uuid",
  "content": "# Feature Request: Use Transcript Feature\n\n...",
  "validation_issues": [...],
  "suggestions": [
    "Consider adding user personas",
    "Technical constraints section needs more detail"
  ]
}
```

### Download Formatted File
```http
GET /v1/format/download/{job_id}
Content-Disposition: attachment; filename="feature-request-2025-10-08.txt"
```

### Download Template Guidance Script
```http
GET /v1/templates/{template_id}/script
Content-Disposition: attachment; filename="recording-guide-system-request.md"
```

## Service Implementation

### Template Manager Service
**File:** `src/services/template_manager.py`

**Responsibilities:**
- Load template configurations from database
- Validate template files exist
- Cache template metadata
- Support dynamic template addition/removal
- Version management

**Key Methods:**
```python
async def list_templates(self, type: Optional[str] = None, active_only: bool = True) -> List[Template]
async def get_template(self, template_id: str) -> Template
async def validate_template(self, template_id: str) -> ValidationResult
async def reload_templates(self) -> None  # Hot reload without restart
```

### Transcript Formatter Service
**File:** `src/services/transcript_formatter.py`

**Responsibilities:**
- AI-powered content extraction from transcripts
- Template-specific formatting
- Field validation and completeness checking
- Suggestion generation for missing information

**Key Methods:**
```python
async def format_transcript(
    self,
    transcript: Dict,
    template: Template,
    user_inputs: Dict
) -> FormatResult

async def validate_content(
    self,
    extracted_content: Dict,
    required_fields: List[str]
) -> ValidationResult

async def generate_suggestions(
    self,
    content: Dict,
    template: Template
) -> List[Suggestion]
```

**AI Integration:**
- Use Claude/GPT for intelligent extraction
- Template-specific prompts for each document type
- Context-aware validation
- Suggestion generation

### Document Generator Service
**File:** `src/services/document_generator.py`

**Responsibilities:**
- Generate DOCX files from templates using python-docx
- Create text files with proper formatting
- Handle template variable substitution
- Preserve formatting from .dotx templates

**Key Methods:**
```python
async def generate_docx(
    self,
    template_path: str,
    content: Dict
) -> bytes

async def generate_text(
    self,
    content: Dict,
    format: str = "txt"
) -> str
```

**Dependencies:**
- `python-docx` for Word document manipulation
- `jinja2` for text template rendering

### Script Generator Service
**File:** `src/services/script_generator.py`

**Responsibilities:**
- Generate recording guidance scripts
- Template-specific instructions
- Maintain script library

**Key Methods:**
```python
async def get_script(self, template_id: str) -> str
async def generate_script(self, template: Template) -> str
```

## File Structure

```
TranscribeMS/
├── src/
│   ├── api/endpoints/
│   │   ├── transcript_formatter.py      # NEW: Format endpoints
│   │   └── template_management.py       # NEW: Template CRUD
│   ├── services/
│   │   ├── template_manager.py          # NEW: Template service
│   │   ├── transcript_formatter.py      # NEW: AI formatting
│   │   ├── document_generator.py        # NEW: DOCX generation
│   │   └── script_generator.py          # NEW: Guidance scripts
│   ├── models/
│   │   ├── template.py                  # NEW: Template model
│   │   └── format_job.py                # NEW: Format job model
│   └── core/
│       └── llm_client.py                # NEW: LLM integration
├── templates/
│   ├── meeting_notes.dotx               # Word template
│   ├── project_meeting_notes.dotx       # Word template
│   ├── system_request.json              # Text template config
│   └── scripts/
│       ├── system_request_guide.md
│       └── project_meeting_guide.md
├── format_output/                        # Generated files
└── template_database.db                  # SQLite database
```

## Configuration Updates

### Environment Variables
```bash
# Template Configuration
TEMPLATE_DIR="templates"
TEMPLATE_SCRIPT_DIR="templates/scripts"
FORMAT_OUTPUT_DIR="format_output"

# LLM Configuration (for AI formatting)
LLM_PROVIDER="anthropic"  # or "openai"
LLM_MODEL="claude-3-5-sonnet-20241022"
LLM_API_KEY="..."
LLM_MAX_TOKENS=4096
```

## Design Constraints

### 1. Template Extensibility
- **Zero-code template addition:** Drop new .dotx file + JSON config → appears in dropdown
- **Database-driven:** All template metadata in database
- **Hot-reload capable:** Template changes reflect immediately

### 2. Format Consistency
- **Standard API responses:** All endpoints follow same structure
- **Predictable file naming:** `{template-type}-{date}-{id}.{ext}`
- **Consistent validation:** Same validation format across all templates

### 3. AI Integration
- **Provider-agnostic:** Support multiple LLM providers
- **Graceful degradation:** Work without AI (basic extraction)
- **Token management:** Chunk large transcripts for processing

### 4. Performance
- **Async processing:** All formatting jobs are async
- **Caching:** Cache template metadata and formatted previews
- **Streaming:** Support large transcript processing

### 5. Frontend Integration
- **Standard REST API:** JSON responses for all endpoints
- **File downloads:** Standard HTTP file download patterns
- **Progress tracking:** SSE or polling for format job status

## Future Enhancements (Out of Scope for v1)

1. **Microsoft Office Integration**
   - Auto-populate meeting metadata from Outlook
   - Attach generated notes to calendar events
   - Sync to OneNote

2. **Advanced AI Features**
   - Sentiment analysis
   - Topic clustering
   - Automatic summary generation
   - Key quote extraction

3. **Collaboration Features**
   - Multi-user editing
   - Comment threads
   - Approval workflows

4. **Analytics**
   - Template usage metrics
   - Average formatting times
   - Common validation issues

## Testing Strategy

### Unit Tests
- Template loading and validation
- AI extraction accuracy
- Document generation
- Field validation logic

### Integration Tests
- End-to-end format workflow
- Template database operations
- File generation and download
- API endpoint contracts

### Template Tests
- Each template type separately
- Required field validation
- Output file integrity
- DOCX template rendering

## Success Criteria

1. ✅ Users can select any transcript from dropdown
2. ✅ Users can select any active template from dropdown
3. ✅ Users can download guidance scripts
4. ✅ AI extracts content with 90%+ accuracy
5. ✅ Validation detects missing critical information
6. ✅ Generated DOCX files preserve template formatting
7. ✅ Adding new templates requires no code changes
8. ✅ All endpoints return standard JSON responses
9. ✅ Frontend can display preview before download
10. ✅ System handles large transcripts (1000+ segments)

---

**Next Steps:**
1. Review and approve design
2. Create database migrations
3. Implement core services
4. Build API endpoints
5. Create test templates
6. Write comprehensive tests
7. Document API for frontend team
