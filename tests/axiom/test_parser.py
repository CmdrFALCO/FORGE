"""Unit tests for YAML extraction from LLM responses."""

from forge.axiom.generator.parser import extract_yaml_block


class TestExtractYamlBlock:
    """Tests for extract_yaml_block function."""

    def test_extracts_yaml_code_block(self):
        """Standard yaml code block should be extracted."""
        response = """
Here's a cell design:

```yaml
_meta:
  cell_type: prismatic
envelope:
  external:
    height_mm: 100.0
```

This design achieves good energy density.
"""
        result = extract_yaml_block(response)

        assert result.success
        assert result.yaml_content["_meta"]["cell_type"] == "prismatic"
        assert result.yaml_content["envelope"]["external"]["height_mm"] == 100.0

    def test_extracts_generic_code_block(self):
        """Generic code block with YAML content should work."""
        response = """
```
_meta:
  cell_type: prismatic
envelope:
  external:
    height_mm: 100.0
```
"""
        result = extract_yaml_block(response)

        assert result.success
        assert result.yaml_content["envelope"]["external"]["height_mm"] == 100.0

    def test_handles_multiple_code_blocks(self):
        """Should extract the YAML block, not other code."""
        response = """
Here's some Python code:

```python
print("hello")
```

And here's the cell definition:

```yaml
_meta:
  cell_type: prismatic
envelope:
  external:
    height_mm: 100.0
```
"""
        result = extract_yaml_block(response)

        assert result.success
        assert "envelope" in result.yaml_content

    def test_fails_on_no_yaml(self):
        """Should fail gracefully when no YAML present."""
        response = "I cannot design that cell because it violates physics."

        result = extract_yaml_block(response)

        assert not result.success
        assert "No YAML content found" in result.error

    def test_fails_on_invalid_yaml(self):
        """Should report parse errors for malformed YAML."""
        response = """
```yaml
_meta:
  cell_type: prismatic
  invalid: [unclosed bracket
```
"""
        result = extract_yaml_block(response)

        assert not result.success
        assert "parse error" in result.error.lower()

    def test_extracts_raw_yaml_without_code_block(self):
        """Raw YAML without code blocks should be detected."""
        response = """_meta:
  cell_type: prismatic
envelope:
  external:
    height_mm: 100.0
"""
        result = extract_yaml_block(response)

        assert result.success
        assert result.yaml_content["envelope"]["external"]["height_mm"] == 100.0

    def test_preserves_raw_yaml_content(self):
        """Should preserve the raw YAML string."""
        response = """
```yaml
_meta:
  cell_type: prismatic
```
"""
        result = extract_yaml_block(response)

        assert result.success
        assert "_meta:" in result.raw_yaml
        assert "cell_type: prismatic" in result.raw_yaml

    def test_handles_nested_yaml(self):
        """Should handle complex nested YAML structures."""
        response = """
```yaml
electrochemistry:
  cathode:
    material_name: "NMC811"
    loading_mg_cm2: 19.674
    specific_capacity_mah_g: 193.814
  anode:
    material_name: "Graphite"
    loading_mg_cm2: 11.478
```
"""
        result = extract_yaml_block(response)

        assert result.success
        assert result.yaml_content["electrochemistry"]["cathode"]["material_name"] == "NMC811"
        assert result.yaml_content["electrochemistry"]["anode"]["loading_mg_cm2"] == 11.478

