"""
Script generator service for creating recording guidance documents.
"""

from pathlib import Path
from typing import Optional

from src.core.logging import get_logger
from src.models.template import Template

logger = get_logger(__name__)


class ScriptGeneratorService:
    """Service for generating and managing recording guidance scripts."""

    def __init__(self, scripts_dir: str = "templates/scripts"):
        """Initialize script generator service.

        Args:
            scripts_dir: Directory for guidance scripts
        """
        self.scripts_dir = Path(scripts_dir)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ScriptGeneratorService initialized with dir: {scripts_dir}")

    async def get_script(self, template: Template) -> Optional[str]:
        """Get recording guidance script for a template.

        Args:
            template: Template configuration

        Returns:
            Script content or None if not available
        """
        if not template.script_path:
            return None

        script_path = Path(template.script_path)

        if not script_path.exists():
            # Try to generate default script
            return await self.generate_script(template)

        with open(script_path, "r") as f:
            return f.read()

    async def generate_script(self, template: Template) -> str:
        """Generate default recording guidance script for a template.

        Args:
            template: Template configuration

        Returns:
            Generated script content
        """
        if template.type == "system_request":
            return self._generate_system_request_script(template)
        elif template.type == "general_meeting":
            return self._generate_general_meeting_script(template)
        elif template.type == "project_meeting":
            return self._generate_project_meeting_script(template)
        else:
            return self._generate_generic_script(template)

    def _generate_system_request_script(self, template: Template) -> str:
        """Generate system/feature request recording script."""
        return f"""# System/Feature Request Recording Guide

**Template:** {template.name}
**Version:** {template.version}

## Purpose
This guide helps you record a comprehensive feature request that can be automatically formatted into a spec-kit compatible document.

## Required Information

### 1. Feature Name
- Provide a clear, concise title for the feature
- Example: "User Authentication with OAuth2"

### 2. Problem Statement
- What problem are you solving?
- Who is experiencing this problem?
- What is the impact of not solving it?

### 3. Target Users
- Who will use this feature?
- What are their roles?
- What are their skill levels?

### 4. Proposed Solution
- High-level description of your approach
- Key components or changes needed
- How it solves the problem

### 5. Acceptance Criteria
- How will you know the feature is complete?
- What are the specific conditions that must be met?
- List at least 3-5 testable criteria

### 6. Technical Constraints
- Any limitations or requirements?
- Performance considerations?
- Compatibility requirements?
- Security requirements?

### 7. Dependencies
- What other features/systems does this depend on?
- What existing functionality will be affected?
- Are there any prerequisites?

### 8. Priority
- Business urgency: High, Medium, Low
- Why is this priority level appropriate?

## Recording Tips

1. **Speak Clearly**: Articulate each section clearly
2. **Use Structure**: Explicitly state which section you're addressing
   - Example: "For the problem statement..."
3. **Provide Examples**: Use specific scenarios and examples
4. **Think Through Edge Cases**: Mention error scenarios and edge cases
5. **Be Specific**: Avoid vague language like "better" or "improved"
6. **Include Numbers**: Mention specific metrics or requirements

## Sample Script

> "I'd like to request a new feature for user authentication using OAuth2.
>
> For the problem statement: Currently, users must create and remember separate credentials for our application. This creates friction in the onboarding process and leads to support tickets about password resets. Studies show we lose 30% of potential users at the registration step.
>
> The target users are all application users, particularly non-technical business users who prefer using their existing corporate credentials.
>
> For the proposed solution: Integrate OAuth2 authentication supporting Microsoft Azure AD and Google Workspace. This will allow users to sign in with their existing corporate accounts. We'll maintain backward compatibility with existing username/password authentication.
>
> For acceptance criteria:
> - Users can click "Sign in with Microsoft" or "Sign in with Google"
> - Authentication redirects to the appropriate provider
> - User profile is created automatically on first login
> - Existing users can link their OAuth2 accounts to their existing profiles
> - The system logs all authentication attempts for security auditing
>
> Technical constraints include: Must comply with SOC2 requirements, must work with our existing JWT token system, and must support MFA if the OAuth provider requires it.
>
> Dependencies: This depends on the user profile service and the session management system being updated to handle OAuth tokens.
>
> Priority is high because reducing onboarding friction is a key business objective for Q1."

## After Recording

1. Review the transcript to ensure all sections are covered
2. Use the formatting tool to generate the spec-kit document
3. Review validation warnings and add any missing information
4. Download the formatted document

## Questions?

If you're unsure what information to provide for any section, make a note during recording and add it later when reviewing the formatted output.

---
**Generated by TranscribeMCP Template System**
"""

    def _generate_general_meeting_script(self, template: Template) -> str:
        """Generate general meeting recording script."""
        return f"""# General Meeting Recording Guide

**Template:** {template.name}
**Version:** {template.version}

## Purpose
This guide helps you conduct and record meetings that can be automatically formatted into professional meeting notes.

## Meeting Structure

### 1. Opening (First 2 minutes)
- State the meeting date and time
- List all attendees
- Review the agenda

### 2. Discussion Phase
- Cover each agenda topic clearly
- Encourage participants to state their names when speaking
- Document key points and perspectives

### 3. Decisions & Action Items
- Clearly state decisions: "We've decided to..."
- For action items, use format: "Action item for [Name]: [Task] by [Date]"
- Confirm understanding of action items

### 4. Closing
- Summarize key decisions
- Review action items
- Schedule next meeting if needed

## Speaking Tips

1. **State Names**: When someone new speaks, introduce them
   - "Sarah from Engineering is joining us"
2. **Mark Decisions**: Use clear phrases
   - "We've decided..."
   - "The team agreed..."
3. **Mark Action Items**: Be explicit
   - "John will handle the database migration by Friday"
4. **Parking Lot**: Note items to discuss later
   - "Let's put that in the parking lot for next time"

## Required Information

- **Meeting Date/Time**: State at the beginning
- **Attendees**: List everyone present
- **Discussion Topics**: Clear topic transitions
- **Decisions Made**: Explicit decision statements
- **Action Items**: Who, what, when
- **Next Steps**: What happens after this meeting

## Sample Meeting Opening

> "Good morning everyone. This is the weekly product sync on October 8th, 2025, at 10 AM.
>
> We have Sarah from Engineering, Mike from Product, Lisa from Design, and Tom from QA.
>
> Today's agenda includes reviewing last week's sprint results, discussing the upcoming feature release, and addressing any blockers.
>
> Let's start with Sarah giving us the engineering update..."

## After Recording

The system will extract:
- Attendee list
- Discussion topics
- Key decisions
- Action items with owners
- Next steps

Review the generated notes and add any details that need clarification.

---
**Generated by TranscribeMCP Template System**
"""

    def _generate_project_meeting_script(self, template: Template) -> str:
        """Generate project meeting recording script."""
        return f"""# Project Meeting Recording Guide

**Template:** {template.name}
**Version:** {template.version}

## Purpose
Capture comprehensive project meeting notes with status updates, risks, and action items.

## Meeting Structure

### 1. Opening & Context (5 minutes)
- Project name and current phase
- Meeting date and time
- List attendees with their roles
- Review agenda

### 2. Status Updates (15-20 minutes)
- Each team provides updates on their deliverables
- Mention completed items and in-progress work
- Note any changes to timeline

### 3. Risks & Issues (10-15 minutes)
- Discuss current blockers
- Identify new risks
- Review mitigation strategies
- Assign owners for risk mitigation

### 4. Decisions (10 minutes)
- Make decisions on open issues
- State the rationale for each decision
- Confirm everyone understands

### 5. Action Items (5-10 minutes)
- Review and assign action items
- Set clear due dates
- Confirm ownership

### 6. Next Meeting (5 minutes)
- Schedule next meeting
- Define focus areas for next meeting

## Required Information

### Project Context
- Project name
- Current phase (Planning, Development, Testing, etc.)
- Key milestones

### Attendees
- Name and role for each participant
- Example: "Sarah Chen, Technical Lead"

### Status Updates
- What was completed
- What's in progress
- What's coming next
- Any timeline changes

### Risks & Issues
- Description of the risk/issue
- Impact (High, Medium, Low)
- Owner of mitigation
- Mitigation plan

### Action Items
- Task description
- Owner name
- Due date
- Dependencies (if any)

## Speaking Guidelines

1. **State Context**: Begin with project and phase
2. **Use Structure**: "For status updates..." "Moving to risks..."
3. **Be Specific**: Use actual dates and names
4. **Quantify**: Use numbers for progress (e.g., "80% complete")
5. **Mark Severity**: High/Medium/Low for risks
6. **Confirm Action Items**: Repeat back to ensure accuracy

## Sample Status Update

> "For the authentication module status update:
>
> Completed items: We finished the OAuth2 integration with Microsoft Azure AD. All unit tests are passing, and code review is complete.
>
> In progress: Sarah is working on the Google Workspace integration, which is about 60% complete. We expect this to be done by end of week.
>
> Blockers: We're waiting for the security team to complete their review of our token handling. This is a high priority blocker because we can't proceed to QA without their sign-off.
>
> Timeline: We're still on track for the October 15th release date, but the security review needs to happen by October 10th at the latest."

## Sample Action Item

> "Action item for Tom Martinez, QA Lead: Create test cases for OAuth2 error scenarios by October 10th. This depends on the security review being complete."

## After Recording

The system will generate structured project notes including:
- Executive summary
- Detailed status by area
- Risk register with owners
- Action item tracker
- Next meeting agenda

Review for completeness and add any missing details.

---
**Generated by TranscribeMCP Template System**
"""

    def _generate_generic_script(self, template: Template) -> str:
        """Generate generic recording script."""
        required = ", ".join(template.required_fields) if template.required_fields else "None specified"

        return f"""# Recording Guide: {template.name}

**Template:** {template.name}
**Version:** {template.version}
**Description:** {template.description or "No description provided"}

## Required Information

The following fields are required for this template:
{required}

## Recording Tips

1. Speak clearly and at a moderate pace
2. State which section you're addressing
3. Provide specific details and examples
4. Mention any relevant context
5. Review the recording before submitting

## After Recording

The system will extract the required information and format it according to the template. Review the generated document and add any missing details.

---
**Generated by TranscribeMCP Template System**
"""

    async def save_script(self, template: Template, content: str) -> Path:
        """Save a script to file.

        Args:
            template: Template configuration
            content: Script content

        Returns:
            Path to saved script
        """
        filename = f"{template.id}_guide.md"
        script_path = self.scripts_dir / filename

        with open(script_path, "w") as f:
            f.write(content)

        logger.info(f"Script saved: {script_path}")
        return script_path
