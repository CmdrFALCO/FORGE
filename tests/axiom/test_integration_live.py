"""Live integration tests for LLM driver with real API calls.

These tests require:
- ANTHROPIC_API_KEY environment variable set
- Valid API key with available credits
- Internet connectivity to Anthropic API

Run with: pytest tests/llm_driver/test_integration_live.py -v -s
Run all live tests: pytest -m live -v -s
"""

import os

import pytest

from forge.axiom import (
    ClaudeBackend,
    OllamaBackend,
    generate_cell_design,
)

# Mark all tests in this module as requiring live API
pytestmark = pytest.mark.live


class TestClaudeBackendLive:
    """Live tests with Claude API."""

    def test_claude_backend_available(self):
        """Claude API key should be configured."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        assert api_key is not None, "ANTHROPIC_API_KEY environment variable not set"
        assert len(api_key) > 0, "ANTHROPIC_API_KEY is empty"

    def test_claude_backend_initialization(self):
        """ClaudeBackend should initialize with valid API key."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        backend = ClaudeBackend(api_key=api_key)
        assert backend is not None
        assert backend.api_key == api_key

    def test_claude_generates_valid_response(self):
        """Claude should generate a response to a simple request."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        backend = ClaudeBackend(api_key=api_key)
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Respond with exactly: HELLO_WORLD",
            },
            {"role": "user", "content": "Say hello"},
        ]

        response = backend.generate(messages)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_claude_understands_context(self):
        """Claude should understand system prompt context."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")

        backend = ClaudeBackend(api_key=api_key)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a battery engineer. When asked to design a cell, "
                    "output exactly: BATTERY_DESIGN_ACKNOWLEDGED"
                ),
            },
            {"role": "user", "content": "Design a cell"},
        ]

        response = backend.generate(messages)

        assert "BATTERY_DESIGN_ACKNOWLEDGED" in response


class TestGenerateCellDesignLive:
    """Live integration tests for generate_cell_design()."""

    @pytest.fixture
    def skip_if_no_api_key(self):
        """Skip test if API key not configured."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not set")
        return api_key

    def test_generate_simple_lfp_cell(self, skip_if_no_api_key):
        """Should generate a valid LFP cell design."""
        result = generate_cell_design(
            "Design a 100Ah LFP prismatic cell for stationary energy storage",
            backend="claude",
        )

        assert result is not None
        assert isinstance(result.success, bool)
        assert result.attempts >= 1
        assert result.attempts <= 3

    def test_generate_nmc_cell(self, skip_if_no_api_key):
        """Should generate a valid NMC cell design."""
        result = generate_cell_design(
            "Design a 50Ah NMC811 prismatic cell for electric vehicle application",
            backend="claude",
        )

        assert result is not None
        if result.success:
            assert result.calculation_result is not None
            assert result.calculation_result.capacity_ah > 0
            assert result.calculation_result.energy_wh > 0

    def test_generate_with_specific_dimensions(self, skip_if_no_api_key):
        """Should generate a cell with specific dimensions."""
        result = generate_cell_design(
            (
                "Design a prismatic cell with external dimensions "
                "100mm height x 200mm width x 30mm thickness"
            ),
            backend="claude",
        )

        assert result is not None
        if result.success:
            assert result.cell_input is not None
            # Check that dimensions are approximately specified
            assert result.cell_input.geometry.external_height_mm > 90
            assert result.cell_input.geometry.external_height_mm < 110

    def test_result_contains_yaml(self, skip_if_no_api_key):
        """Successful result should contain YAML content."""
        result = generate_cell_design(
            "Design a 100Ah LFP cell",
            backend="claude",
        )

        assert result is not None
        if result.success:
            assert result.yaml_content is not None
            assert "_meta:" in result.yaml_content
            assert "cell_type: prismatic" in result.yaml_content

    def test_result_contains_parsed_input(self, skip_if_no_api_key):
        """Successful result should contain parsed cell input."""
        result = generate_cell_design(
            "Design a 100Ah LFP cell",
            backend="claude",
        )

        assert result is not None
        if result.success:
            assert result.cell_input is not None
            assert result.cell_input.cathode is not None
            assert result.cell_input.anode is not None

    def test_result_contains_calculations(self, skip_if_no_api_key):
        """Successful result should contain calculation results."""
        result = generate_cell_design(
            "Design a 100Ah LFP cell",
            backend="claude",
        )

        assert result is not None
        if result.success:
            assert result.calculation_result is not None
            calc = result.calculation_result
            assert calc.capacity_ah > 0
            assert calc.energy_wh > 0
            assert calc.total_mass_g > 0
            assert calc.gravimetric_ed_whkg > 0

    def test_retry_on_invalid_design(self, skip_if_no_api_key):
        """Should retry if LLM generates invalid design."""
        # Request an ambiguous design that might fail validation
        result = generate_cell_design(
            "Design a cell with very high energy density and very long cycle life",
            backend="claude",
        )

        assert result is not None
        # If it failed, it should have attempted retries
        if not result.success:
            assert result.attempts > 1, "Should have retried on failure"
            assert len(result.retry_reasons) > 0

    def test_skip_calculation_option(self, skip_if_no_api_key):
        """Should be able to skip calculation step."""
        result = generate_cell_design(
            "Design a 100Ah LFP cell",
            backend="claude",
            calculate=False,
        )

        assert result is not None
        if result.success:
            assert result.cell_input is not None
            # Calculation should be skipped
            assert result.calculation_result is None


class TestOllamaBackendLive:
    """Live tests with local Ollama backend."""

    @pytest.fixture
    def skip_if_ollama_unavailable(self):
        """Skip test if Ollama not available."""
        import requests

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                pytest.skip("Ollama not available")
            # Check if qwen2.5-coder model is available
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            if not any("qwen2.5-coder" in m for m in models):
                pytest.skip("qwen2.5-coder model not available in Ollama")
        except (requests.ConnectionError, requests.Timeout):
            pytest.skip("Ollama not running on localhost:11434")

    def test_ollama_backend_available(self, skip_if_ollama_unavailable):
        """Ollama should be available."""
        # If we reach here, skip fixture passed
        assert True

    def test_ollama_backend_initialization(self, skip_if_ollama_unavailable):
        """OllamaBackend should initialize."""
        backend = OllamaBackend()
        assert backend is not None

    def test_ollama_generates_response(self, skip_if_ollama_unavailable):
        """Ollama should generate a response."""
        backend = OllamaBackend()
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Be concise.",
            },
            {"role": "user", "content": "Say hello"},
        ]

        response = backend.generate(messages)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_generate_cell_with_ollama(self, skip_if_ollama_unavailable):
        """Should be able to generate cell designs with Ollama."""
        result = generate_cell_design(
            "Design a 100Ah LFP cell",
            backend="ollama",
        )

        assert result is not None
        # Ollama may not always succeed, but should attempt
        assert result.attempts >= 1


class TestErrorHandling:
    """Tests for error handling in live scenarios."""

    def test_invalid_api_key_error(self):
        """Should raise error with invalid API key."""
        with pytest.raises(Exception):  # Could be auth error or other
            generate_cell_design(
                "Design a cell",
                backend="claude",
                api_key="sk-invalid-key-12345",
            )

    def test_missing_api_key_error(self):
        """Should raise error if API key not provided and not in environment."""
        # Temporarily remove API key from environment
        original_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with pytest.raises((ValueError, KeyError)):
                backend = ClaudeBackend(api_key=None)
                # If backend initialized, try to generate
                if backend:
                    backend.generate(
                        [
                            {
                                "role": "system",
                                "content": "test",
                            }
                        ]
                    )
        finally:
            # Restore API key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key

