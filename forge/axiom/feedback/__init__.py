"""
AXIOM Feedback - Corrective feedback formatting for LLM retry prompts.

Transforms validation errors into structured, actionable feedback
that guides the LLM toward valid configurations on retry attempts.
Currently, feedback formatting is inline in supervisor/driver.py
(the retry prompt construction). This module will extract and extend
that logic with:
- Error categorization (schema vs physics vs cross-field)
- Severity-based feedback prioritization
- History-aware feedback (avoid repeating same suggestions)
"""

from dataclasses import dataclass, field


@dataclass
class FeedbackItem:
    """Single piece of corrective feedback for the LLM."""

    category: str  # 'schema', 'physics', 'cross_field'
    severity: str  # 'error', 'warning'
    message: str
    suggestion: str = ""


@dataclass
class CorrectionFeedback:
    """Structured feedback package for a retry attempt."""

    items: list[FeedbackItem] = field(default_factory=list)
    attempt_number: int = 0
    max_attempts: int = 3

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.items if i.severity == "error")

    def format_for_prompt(self) -> str:
        """Format feedback items into text suitable for an LLM retry prompt.

        Returns:
            Formatted feedback string for insertion into retry prompt.
        """
        raise NotImplementedError(
            "CorrectionFeedback.format_for_prompt() - planned for post-migration extraction from supervisor/driver.py"
        )


class FeedbackGenerator:
    """
    Generates structured corrective feedback from validation results.

    Transforms ValidationReport errors into actionable LLM guidance,
    with categorization, prioritization, and history tracking.
    """

    def generate(self, errors: list[str], attempt: int = 1, max_attempts: int = 3) -> CorrectionFeedback:
        """Generate corrective feedback from validation errors.

        Args:
            errors: List of validation error messages.
            attempt: Current retry attempt number.
            max_attempts: Maximum allowed retry attempts.

        Returns:
            CorrectionFeedback with categorized, actionable items.
        """
        raise NotImplementedError(
            "FeedbackGenerator.generate() - planned for post-migration extraction from supervisor/driver.py"
        )
