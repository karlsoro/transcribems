"""
Initialize default templates in the database.
Run this script to populate the template database with default templates.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.template_database import get_template_db
from src.models.template import Template


async def init_templates():
    """Initialize default templates."""
    template_db = await get_template_db()

    templates_dir = Path("templates")

    # Define default templates
    templates_config = [
        {
            "id": "system-request-v1",
            "name": "System/Feature Request",
            "description": "Generate spec-kit compatible feature requests from transcripts",
            "type": "system_request",
            "file_path": "templates/system_request.json",
            "output_format": "txt",
            "version": "1.0.0",
            "required_fields": [
                "feature_name",
                "problem_statement",
                "proposed_solution",
                "acceptance_criteria"
            ],
            "optional_fields": [
                "target_users",
                "technical_constraints",
                "dependencies",
                "priority",
                "additional_notes"
            ],
            "script_path": "templates/scripts/system_request_guide.md"
        },
        {
            "id": "general-meeting-v1",
            "name": "General Meeting Notes",
            "description": "Standard meeting notes with discussion topics, decisions, and action items",
            "type": "general_meeting",
            "file_path": "templates/general_meeting_template.json",
            "output_format": "docx",
            "version": "1.0.0",
            "required_fields": [
                "meeting_date",
                "attendees",
                "discussion_topics",
                "action_items"
            ],
            "optional_fields": [
                "decisions",
                "next_steps",
                "parking_lot"
            ],
            "script_path": "templates/scripts/general_meeting_guide.md"
        },
        {
            "id": "project-meeting-v1",
            "name": "Project Meeting Notes",
            "description": "Comprehensive project meeting notes with status, risks, and detailed action tracking",
            "type": "project_meeting",
            "file_path": "templates/project_meeting_template.json",
            "output_format": "docx",
            "version": "1.0.0",
            "required_fields": [
                "project_name",
                "meeting_date",
                "attendees",
                "status_updates",
                "action_items"
            ],
            "optional_fields": [
                "risks_issues",
                "decisions",
                "next_meeting"
            ],
            "script_path": "templates/scripts/project_meeting_guide.md"
        }
    ]

    # Add each template
    for config in templates_config:
        template = Template(**config)
        await template_db.add_template(template)
        print(f"✓ Added template: {template.name} ({template.id})")

    print(f"\n✓ Successfully initialized {len(templates_config)} templates")


if __name__ == "__main__":
    asyncio.run(init_templates())
