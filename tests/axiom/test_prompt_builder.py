"""Unit tests for prompt construction."""

from forge.axiom.generator.prompt_builder import (
    build_retry_prompt,
    build_system_prompt,
)


class TestBuildSystemPrompt:
    """Tests for system prompt construction."""

    def test_includes_parameter_schema(self):
        """System prompt should include parameter schema."""
        prompt = build_system_prompt()
        assert "height_mm" in prompt
        assert "loading_mg_cm2" in prompt

    def test_includes_validation_rules(self):
        """System prompt should include validation rules."""
        prompt = build_system_prompt()
        assert "N/P Ratio" in prompt
        assert "1.05-1.25" in prompt

    def test_includes_example_by_default(self):
        """System prompt should include example cell by default."""
        prompt = build_system_prompt(include_example=True)
        assert "```yaml" in prompt
        assert "LFP" in prompt

    def test_can_exclude_example(self):
        """Should be able to exclude example cell."""
        prompt = build_system_prompt(include_example=False)
        # Should still have schema
        assert "height_mm" in prompt
        # Should not have the full example section
        assert "Example:" not in prompt

    def test_includes_output_format(self):
        """System prompt should include output format guidance."""
        prompt = build_system_prompt()
        assert "```yaml" in prompt
        assert "Output Format" in prompt or "output" in prompt.lower()

    def test_includes_design_tradeoffs(self):
        """System prompt should include design trade-offs."""
        prompt = build_system_prompt()
        assert "Energy vs Power" in prompt or "Tradeoff" in prompt.lower()

    def test_is_reasonable_length(self):
        """System prompt should be substantial but not excessive."""
        prompt = build_system_prompt(include_example=True)
        # Should be at least 2000 chars (has content)
        # Should be less than 50000 chars (not bloated)
        assert 2000 < len(prompt) < 50000


class TestBuildRetryPrompt:
    """Tests for retry prompt construction."""

    def test_includes_feedback(self):
        """Retry prompt should include validation feedback."""
        prompt = build_retry_prompt(
            original_request="Design a 100Ah cell",
            validation_feedback="N/P ratio 0.9 is below minimum 1.05",
        )

        assert "N/P ratio" in prompt
        assert "0.9" in prompt
        assert "100Ah" in prompt

    def test_asks_for_correction(self):
        """Retry prompt should ask for corrected design."""
        prompt = build_retry_prompt(original_request="Design a cell", validation_feedback="Error")

        assert (
            "corrected" in prompt.lower() or "fix" in prompt.lower() or "address" in prompt.lower()
        )

    def test_references_original_request(self):
        """Retry prompt should reference the original request."""
        original = "Design a 50Ah NMC cell"
        prompt = build_retry_prompt(original_request=original, validation_feedback="Error")

        assert original in prompt

    def test_asks_for_yaml_block(self):
        """Retry prompt should ask for YAML in code block."""
        prompt = build_retry_prompt(original_request="Design a cell", validation_feedback="Error")

        assert "```yaml" in prompt or "code block" in prompt.lower()

