"""Unit tests for value extraction functions in template_to_input module."""

import pytest

from forge.engine.conversion.template_to_input import _extract_value, _get_nested


class TestExtractValue:
    """Tests for _extract_value function handling dual format."""

    def test_extract_template_format(self):
        """Extract value from template metadata dict."""
        template = {
            "_default": 88.8,
            "_type": "number",
            "min": 50,
            "max": 200,
        }
        result = _extract_value(template)
        assert result == 88.8

    def test_extract_instance_format(self):
        """Extract direct value in instance format."""
        result = _extract_value(88.8)
        assert result == 88.8

    def test_extract_string_direct(self):
        """Extract string value in instance format."""
        result = _extract_value("NCM")
        assert result == "NCM"

    def test_extract_int_direct(self):
        """Extract integer value in instance format."""
        result = _extract_value(22)
        assert result == 22

    def test_extract_none_value(self):
        """Handle None value."""
        result = _extract_value(None)
        assert result is None


class TestGetNested:
    """Tests for _get_nested function."""

    def test_get_simple_path(self):
        """Get value from simple nested path."""
        data = {"envelope": {"cell_height_mm": 88.8}}
        result = _get_nested(data, "envelope.cell_height_mm")
        assert result == 88.8

    def test_get_deep_path(self):
        """Get value from deeply nested path."""
        data = {
            "electrochemistry": {
                "cathode": {
                    "name": "NCA_Cathode",
                    "loading_mg_cm2": 120.5,
                }
            }
        }
        result = _get_nested(data, "electrochemistry.cathode.name")
        assert result == "NCA_Cathode"

    def test_get_with_template_format(self):
        """Extract value from template format in nested path."""
        data = {
            "envelope": {
                "cell_height_mm": {
                    "_default": 88.8,
                    "_type": "number",
                }
            }
        }
        result = _get_nested(data, "envelope.cell_height_mm")
        assert result == 88.8

    def test_get_with_default(self):
        """Return default when path not found."""
        data = {"envelope": {}}
        result = _get_nested(data, "envelope.missing_field", default=25.36)
        assert result == 25.36

    def test_get_raises_key_error(self):
        """Raise KeyError when path not found and no default."""
        data = {"envelope": {}}
        with pytest.raises(KeyError):
            _get_nested(data, "envelope.missing_field")

    def test_get_path_not_found_at_root(self):
        """Raise KeyError when root path missing."""
        data = {"envelope": {}}
        with pytest.raises(KeyError):
            _get_nested(data, "stack_config.stacks")

    def test_get_with_none_default(self):
        """Return None when explicitly provided as default."""
        data = {"envelope": {}}
        result = _get_nested(data, "envelope.missing_field", default=None)
        assert result is None
