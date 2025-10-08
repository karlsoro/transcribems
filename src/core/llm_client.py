"""
LLM client for AI-powered content extraction and formatting.
"""

import os
from typing import Dict, Any, Optional, List
from anthropic import AsyncAnthropic

from src.core.logging import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Client for interacting with LLM providers (Claude, GPT, etc.)."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        max_tokens: int = 4096
    ):
        """Initialize LLM client.

        Args:
            provider: LLM provider (anthropic, openai)
            model: Model identifier
            api_key: API key (defaults to env var)
            max_tokens: Maximum tokens in response
        """
        self.provider = provider
        self.model = model
        self.max_tokens = max_tokens

        if provider == "anthropic":
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = AsyncAnthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"LLM client initialized: {provider}/{model}")

    async def extract_content(
        self,
        transcript_text: str,
        template_type: str,
        required_fields: List[str],
        optional_fields: List[str],
        user_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract structured content from transcript using AI.

        Args:
            transcript_text: Full transcript text
            template_type: Type of template (system_request, etc.)
            required_fields: Required fields to extract
            optional_fields: Optional fields to extract
            user_inputs: User-provided field values

        Returns:
            Extracted content with fields and confidence scores
        """
        prompt = self._build_extraction_prompt(
            transcript_text,
            template_type,
            required_fields,
            optional_fields,
            user_inputs
        )

        try:
            if self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.content[0].text

                # Parse structured response
                extracted = self._parse_extraction_response(content, required_fields, optional_fields)

                logger.info(f"Content extracted successfully for {template_type}")
                return extracted

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            raise

    def _build_extraction_prompt(
        self,
        transcript: str,
        template_type: str,
        required_fields: List[str],
        optional_fields: List[str],
        user_inputs: Dict[str, Any]
    ) -> str:
        """Build extraction prompt for specific template type."""

        if template_type == "system_request":
            return f"""You are analyzing a transcript to extract information for a system/feature request document.

The transcript contains a discussion about a new feature or system requirement. Extract the following information:

REQUIRED FIELDS:
{chr(10).join(f'- {field}' for field in required_fields)}

OPTIONAL FIELDS:
{chr(10).join(f'- {field}' for field in optional_fields)}

USER-PROVIDED VALUES:
{chr(10).join(f'- {k}: {v}' for k, v in user_inputs.items())}

TRANSCRIPT:
{transcript}

Extract the information in JSON format. For each field:
1. Provide the extracted value
2. Provide a confidence score (0-100)
3. Note if information is missing or unclear

Format your response as JSON with this structure:
{{
  "extracted_fields": {{
    "field_name": {{
      "value": "extracted value",
      "confidence": 95,
      "notes": "any relevant notes"
    }}
  }},
  "missing_fields": ["list", "of", "missing", "required", "fields"],
  "suggestions": ["suggestions for improving the request"]
}}

Be thorough and extract as much relevant detail as possible."""

        elif template_type == "general_meeting":
            return f"""You are analyzing a meeting transcript to extract meeting notes.

Extract the following information:

REQUIRED FIELDS:
{chr(10).join(f'- {field}' for field in required_fields)}

OPTIONAL FIELDS:
{chr(10).join(f'- {field}' for field in optional_fields)}

TRANSCRIPT:
{transcript}

Extract the information in JSON format with these sections:
- meeting_date: Date/time of meeting
- attendees: List of participants
- discussion_topics: Main topics discussed
- decisions: Key decisions made
- action_items: List of action items with owners
- next_steps: Planned next steps

Format as JSON with confidence scores for each field."""

        elif template_type == "project_meeting":
            return f"""You are analyzing a project meeting transcript to extract detailed project notes.

Extract the following information:

REQUIRED FIELDS:
{chr(10).join(f'- {field}' for field in required_fields)}

OPTIONAL FIELDS:
{chr(10).join(f'- {field}' for field in optional_fields)}

TRANSCRIPT:
{transcript}

Extract the information in JSON format with these sections:
- project_name: Name of the project
- meeting_date: Date/time of meeting
- attendees: List with names and roles
- status_updates: Progress on deliverables
- risks_issues: Current blockers or concerns
- action_items: Who will do what by when
- decisions: Key decisions and rationale
- next_meeting: Date and focus areas

Format as JSON with confidence scores for each field."""

        else:
            raise ValueError(f"Unknown template type: {template_type}")

    def _parse_extraction_response(
        self,
        response: str,
        required_fields: List[str],
        optional_fields: List[str]
    ) -> Dict[str, Any]:
        """Parse LLM response into structured format.

        Args:
            response: Raw LLM response
            required_fields: Expected required fields
            optional_fields: Expected optional fields

        Returns:
            Structured extraction result
        """
        import json

        # Try to find JSON in the response
        start = response.find("{")
        end = response.rfind("}") + 1

        if start == -1 or end == 0:
            logger.warning("No JSON found in LLM response")
            return {
                "extracted_fields": {},
                "confidence_scores": {},
                "missing_fields": required_fields,
                "suggestions": ["Could not parse LLM response"]
            }

        try:
            data = json.loads(response[start:end])

            # Normalize structure
            extracted_fields = data.get("extracted_fields", {})
            confidence_scores = {}

            # Extract confidence scores
            for field, value in extracted_fields.items():
                if isinstance(value, dict) and "confidence" in value:
                    confidence_scores[field] = value["confidence"]
                    extracted_fields[field] = value.get("value", "")

            return {
                "extracted_fields": extracted_fields,
                "confidence_scores": confidence_scores,
                "missing_fields": data.get("missing_fields", []),
                "suggestions": data.get("suggestions", [])
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM: {e}")
            return {
                "extracted_fields": {},
                "confidence_scores": {},
                "missing_fields": required_fields,
                "suggestions": ["Failed to parse LLM response"]
            }


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance.

    Returns:
        LLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(
            provider=os.getenv("LLM_PROVIDER", "anthropic"),
            model=os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096"))
        )
    return _llm_client
