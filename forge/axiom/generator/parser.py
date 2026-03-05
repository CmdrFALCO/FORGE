"""
Parse LLM responses to extract YAML cell definitions.

Handles various response formats:
- YAML in ```yaml code blocks
- YAML in ``` generic code blocks
- Raw YAML (no code blocks)
"""

import re
from dataclasses import dataclass

import yaml


@dataclass
class ParseResult:
    """Result of parsing an LLM response."""

    success: bool
    yaml_content: dict | None = None
    raw_yaml: str | None = None
    error: str | None = None


def extract_yaml_block(response: str) -> ParseResult:
    """
    Extract YAML content from an LLM response.

    Tries multiple patterns:
    1. ```yaml ... ``` code block
    2. ``` ... ``` generic code block containing YAML
    3. Raw YAML (starts with valid YAML indicators)

    Args:
        response: Raw LLM response text

    Returns:
        ParseResult with parsed content or error
    """

    # Pattern 1: Explicit yaml code block
    yaml_block_pattern = r"```yaml\s*\n(.*?)\n```"
    matches = re.findall(yaml_block_pattern, response, re.DOTALL)

    if matches:
        # Use the longest match (most likely the full template)
        raw_yaml = max(matches, key=len)
        return _try_parse_yaml(raw_yaml)

    # Pattern 2: Generic code block
    generic_block_pattern = r"```\s*\n(.*?)\n```"
    matches = re.findall(generic_block_pattern, response, re.DOTALL)

    for match in matches:
        # Check if it looks like YAML
        if _looks_like_yaml(match):
            result = _try_parse_yaml(match)
            if result.success:
                return result

    # Pattern 3: Raw YAML (no code blocks)
    if _looks_like_yaml(response):
        return _try_parse_yaml(response)

    return ParseResult(
        success=False, error="No YAML content found in response. Expected ```yaml code block."
    )


def _looks_like_yaml(text: str) -> bool:
    """Check if text appears to be YAML content."""
    text = text.strip()

    # YAML indicators
    yaml_indicators = [
        text.startswith("_meta:"),
        text.startswith("envelope:"),
        text.startswith("---"),
        ": " in text and not text.startswith("{"),  # Has YAML-style key-value
    ]

    return any(yaml_indicators)


def _try_parse_yaml(raw_yaml: str) -> ParseResult:
    """Attempt to parse YAML string."""
    try:
        content = yaml.safe_load(raw_yaml)

        if content is None:
            return ParseResult(
                success=False, raw_yaml=raw_yaml, error="YAML parsed to None (empty content)"
            )

        if not isinstance(content, dict):
            return ParseResult(
                success=False,
                raw_yaml=raw_yaml,
                error=f"YAML must be a dictionary, got {type(content).__name__}",
            )

        return ParseResult(success=True, yaml_content=content, raw_yaml=raw_yaml)

    except yaml.YAMLError as e:
        return ParseResult(success=False, raw_yaml=raw_yaml, error=f"YAML parse error: {e}")
