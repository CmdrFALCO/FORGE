"""Tests for retry loop behavior using mock backend."""

import pytest

from forge.axiom import MockBackend

# Valid YAML response
VALID_RESPONSE = """
Here's the design:

```yaml
_meta:
  cell_type: prismatic
  design_intent: "Test cell"

envelope:
  external:
    height_mm: 88.8
    width_mm: 264.6
    thickness_mm: 29.6
  walls:
    top_mm: 2.0
    bottom_mm: 1.0
    front_back_mm: 0.5
    sides_mm: 0.7

stack_config:
  architecture:
    num_stacks: 2
    electrode_pairs_per_stack: 22
    end_electrode_config: "BothNegative"
  sheet_geometry:
    cathode_height_mm: 74.0
    cathode_width_mm: 251.7
    anode_offset_top_mm: 2.0
    anode_offset_bottom_mm: 2.0
    anode_offset_left_mm: 2.0
    anode_offset_right_mm: 2.0
    separator_offset_top_mm: 2.0
    separator_offset_bottom_mm: 2.0
    separator_offset_left_mm: 2.0
    separator_offset_right_mm: 2.0

electrochemistry:
  cathode:
    material_name: "NMC811"
    loading_mg_cm2: 19.674
    specific_capacity_mah_g: 193.814
    collector_thickness_um: 12.0
    coating_thickness_um: 58.24
    porosity: 0.25
  anode:
    material_name: "Graphite"
    loading_mg_cm2: 11.478
    specific_capacity_mah_g: 331.161
    collector_thickness_um: 6.0
    coating_thickness_um: 85.47
    porosity: 0.38
  separator:
    material_name: "PP"
    thickness_um: 13.0
    porosity: 0.43
    areal_weight_mgcm2: 1.25
  electrolyte:
    material_name: "LiPF6 in EC:EMC"
    density_g_cm3: 1.223
    excess_factor: 1.0

packaging:
  housing:
    case_density_g_cm3: 2.70
    header_mass_g: 88.76
  insulation:
    shell_thickness_um: 120.0
    shell_count: 2
    fixing_tape_count: 4

current_collection:
  cathode_tabs: 1
  anode_tabs: 1
```
"""


INVALID_RESPONSE_NO_YAML = """
I'm sorry, I cannot design a battery cell that violates the laws of physics.
Please provide more reasonable requirements.
"""


INVALID_RESPONSE_BAD_NP_RATIO = """
```yaml
_meta:
  cell_type: prismatic

envelope:
  external:
    height_mm: 88.8
    width_mm: 264.6
    thickness_mm: 29.6
  walls:
    top_mm: 2.0
    bottom_mm: 1.0
    front_back_mm: 0.5
    sides_mm: 0.7

stack_config:
  architecture:
    num_stacks: 2
    electrode_pairs_per_stack: 22
    end_electrode_config: "BothNegative"
  sheet_geometry:
    cathode_height_mm: 74.0
    cathode_width_mm: 251.7
    anode_offset_top_mm: 2.0
    anode_offset_bottom_mm: 2.0
    anode_offset_left_mm: 2.0
    anode_offset_right_mm: 2.0
    separator_offset_top_mm: 2.0
    separator_offset_bottom_mm: 2.0
    separator_offset_left_mm: 2.0
    separator_offset_right_mm: 2.0

electrochemistry:
  cathode:
    material_name: "NMC811"
    loading_mg_cm2: 25.0
    specific_capacity_mah_g: 200.0
    collector_thickness_um: 12.0
    coating_thickness_um: 58.24
    porosity: 0.25
  anode:
    material_name: "Graphite"
    loading_mg_cm2: 8.0
    specific_capacity_mah_g: 350.0
    collector_thickness_um: 6.0
    coating_thickness_um: 85.47
    porosity: 0.38
  separator:
    material_name: "PP"
    thickness_um: 13.0
    porosity: 0.43
    areal_weight_mgcm2: 1.25
  electrolyte:
    material_name: "LiPF6 in EC:EMC"
    density_g_cm3: 1.223
    excess_factor: 1.0

packaging:
  housing:
    case_density_g_cm3: 2.70
    header_mass_g: 88.76
  insulation:
    shell_thickness_um: 120.0
    shell_count: 2
    fixing_tape_count: 4

current_collection:
  cathode_tabs: 1
  anode_tabs: 1
```
"""


class TestRetryLogic:
    """Tests for retry loop behavior."""

    def test_parser_and_mock_integration(self):
        """Mock backend should track message history."""
        mock = MockBackend([VALID_RESPONSE])

        # Just test that mock properly tracks responses
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Design a cell"},
        ]

        response = mock.generate(messages)

        assert mock.call_count == 1
        assert response == VALID_RESPONSE
        assert mock.received_messages[0] == messages

    def test_mock_backend_sequence(self):
        """Mock backend should return responses in sequence."""
        mock = MockBackend(
            [
                "First response",
                "Second response",
                "Third response",
            ]
        )

        assert mock.generate([]) == "First response"
        assert mock.generate([]) == "Second response"
        assert mock.generate([]) == "Third response"
        assert mock.call_count == 3

    def test_mock_backend_exhaustion(self):
        """Mock backend should raise error when exhausted."""
        mock = MockBackend(["Only response"])

        mock.generate([])
        with pytest.raises(RuntimeError):
            mock.generate([])

    def test_mock_backend_tracks_messages(self):
        """Mock should track all received messages."""
        mock = MockBackend(["response1", "response2"])

        msg1 = [{"role": "user", "content": "First"}]
        msg2 = [{"role": "user", "content": "Second"}]

        mock.generate(msg1)
        mock.generate(msg2)

        assert len(mock.received_messages) == 2
        assert mock.received_messages[0] == msg1
        assert mock.received_messages[1] == msg2

    def test_parser_extracts_from_yaml_block(self):
        """Parser should extract YAML from code block in response."""
        from forge.axiom.generator.parser import extract_yaml_block

        response = VALID_RESPONSE
        result = extract_yaml_block(response)

        assert result.success
        assert result.yaml_content is not None
        assert "_meta" in result.yaml_content

    def test_parser_fails_on_no_yaml(self):
        """Parser should fail gracefully when no YAML present."""
        from forge.axiom.generator.parser import extract_yaml_block

        response = INVALID_RESPONSE_NO_YAML
        result = extract_yaml_block(response)

        assert not result.success
        assert "No YAML content found" in result.error

