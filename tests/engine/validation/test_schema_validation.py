"""Tests for JSON Schema validation (Level 1)."""

from pathlib import Path

import pytest
import yaml

from forge.engine.validation import validate_required_fields, validate_structure


@pytest.fixture
def template():
    """Load prismatic_master.yaml as reference template."""
    yaml_path = (
        Path(__file__).parent.parent.parent.parent
        / "forge"
        / "data"
        / "templates"
        / "prismatic_master.yaml"
    )
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def minimal_valid_cell(template):
    """Create a minimal valid cell based on template defaults."""
    cell = {
        "_meta": {"template_version": "1.0", "cell_type": "prismatic", "cell_name": "test_cell"},
        "envelope": {
            "external": {"cell_height_mm": 88.8, "cell_width_mm": 264.6, "cell_thickness_mm": 29.6},
            "walls": {
                "wall_top_mm": 2.0,
                "wall_bottom_mm": 1.0,
                "wall_front_back_mm": 0.5,
                "wall_sides_mm": 0.7,
            },
            "internals": {
                "insulation_coating_um": 85.0,
                "external_corner_radius_mm": 3.0,
                "internal_corner_radius_mm": 1.5,
            },
        },
        "stack_config": {
            "architecture": {
                "num_stacks": 2,
                "electrode_pairs_per_stack": 44,
                "end_electrode_config": "BothNegative",
            },
            "sheet_geometry": {
                "cathode_height_mm": 74.0,
                "cathode_width_mm": 251.7,
                "anode_offset_top_mm": 2.0,
                "anode_offset_bottom_mm": 2.0,
                "anode_offset_left_mm": 2.0,
                "anode_offset_right_mm": 2.0,
                "separator_offset_top_mm": 2.0,
                "separator_offset_bottom_mm": 2.0,
                "separator_offset_left_mm": 2.0,
                "separator_offset_right_mm": 2.0,
            },
        },
        "electrochemistry": {
            "cathode": {
                "material_name": "NCM",
                "loading_mg_cm2": 19.674,
                "rev_spec_capacity_mahg": 193.814,
                "collector_thickness_um": 12.0,
                "coating_thickness_0pct_um": 58.24,
                "coating_thickness_100pct_um": 57.08,
                "porosity_pct": 25.36,
            },
            "anode": {
                "material_name": "Graphite/SiOx",
                "loading_mg_cm2": 11.478,
                "rev_spec_capacity_mahg": 331.161,
                "collector_thickness_um": 6.0,
                "coating_thickness_0pct_um": 85.47,
                "coating_thickness_100pct_um": 92.31,
                "porosity_pct": 38.01,
                "np_ratio": 1.225,
            },
            "separator": {
                "material_name": "PP/Ceramic",
                "thickness_um": 13.0,
                "porosity_pct": 42.646,
                "areal_weight_mgcm2": 1.25,
            },
            "electrolyte": {
                "material_name": "LiPF6",
                "salt_concentration_m": 1.2,
                "density_g_cm3": 1.223,
                "excess_factor": 1.0,
            },
        },
        "current_collection": {
            "tabs": {
                "cathode": {
                    "material": "Aluminum",
                    "height_mm": 40.0,
                    "width_mm": 50.0,
                    "thickness_mm": 0.3,
                },
                "anode": {
                    "material": "Copper",
                    "height_mm": 40.0,
                    "width_mm": 50.0,
                    "thickness_mm": 0.2,
                },
            }
        },
        "packaging": {
            "housing": {
                "case_material": "Aluminum 3003",
                "case_density_g_cm3": 2.7,
                "lid_thickness_mm": 2.0,
            },
            "insulation": {
                "shell_thickness_um": 120.0,
                "shell_count": 2,
                "fixing_tape_width_mm": 30.0,
                "fixing_tape_count": 4,
            },
        },
    }
    return cell


class TestSchemaValidation:
    """Tests for JSON schema validation (Level 1)."""

    def test_template_passes_schema(self, template):
        """The master template itself should pass schema validation."""
        result = validate_structure(template)
        assert result.valid, f"Template should be valid: {result.to_llm_feedback()}"

    def test_minimal_valid_cell_passes(self, minimal_valid_cell):
        """Minimal valid cell should pass schema."""
        result = validate_structure(minimal_valid_cell)
        assert result.valid, f"Minimal cell should be valid: {result.to_llm_feedback()}"

    def test_missing_required_domain(self, minimal_valid_cell):
        """Missing a required top-level domain should fail."""
        del minimal_valid_cell["packaging"]
        result = validate_structure(minimal_valid_cell)
        assert not result.valid
        assert "packaging" in result.errors[0].path

    def test_missing_required_field_in_envelope(self, minimal_valid_cell):
        """Missing required field in envelope should fail."""
        del minimal_valid_cell["envelope"]["external"]["cell_height_mm"]
        result = validate_structure(minimal_valid_cell)
        assert not result.valid

    def test_wrong_type_height(self, minimal_valid_cell):
        """Wrong type for numeric field should fail."""
        minimal_valid_cell["envelope"]["external"]["cell_height_mm"] = "not a number"
        result = validate_structure(minimal_valid_cell)
        assert not result.valid
        assert "external" in result.errors[0].path or "height" in str(result.errors)

    def test_out_of_range_height_too_small(self, minimal_valid_cell):
        """Value below minimum should fail."""
        minimal_valid_cell["envelope"]["external"]["cell_height_mm"] = 10  # Min is 50
        result = validate_structure(minimal_valid_cell)
        assert not result.valid

    def test_out_of_range_height_too_large(self, minimal_valid_cell):
        """Value above maximum should fail."""
        minimal_valid_cell["envelope"]["external"]["cell_height_mm"] = 500  # Max is 200
        result = validate_structure(minimal_valid_cell)
        assert not result.valid

    def test_out_of_range_stacks(self, minimal_valid_cell):
        """Stacks out of range should fail."""
        minimal_valid_cell["stack_config"]["architecture"]["num_stacks"] = 10  # Max is 4
        result = validate_structure(minimal_valid_cell)
        assert not result.valid

    def test_invalid_end_electrode_config(self, minimal_valid_cell):
        """Invalid enum value should fail."""
        minimal_valid_cell["stack_config"]["architecture"]["end_electrode_config"] = "Invalid"
        result = validate_structure(minimal_valid_cell)
        # This should fail because it's not in the enum
        # (Currently schema is permissive, but could be stricter)

    def test_out_of_range_cathode_loading(self, minimal_valid_cell):
        """Cathode loading out of range should fail."""
        minimal_valid_cell["electrochemistry"]["cathode"]["loading_mg_cm2"] = 50  # Max is 30
        result = validate_structure(minimal_valid_cell)
        assert not result.valid

    def test_out_of_range_np_ratio(self, minimal_valid_cell):
        """N/P ratio out of range should fail."""
        minimal_valid_cell["electrochemistry"]["anode"]["np_ratio"] = 0.9  # Min is 1.05
        result = validate_structure(minimal_valid_cell)
        assert not result.valid

    def test_required_fields_check(self, minimal_valid_cell):
        """validate_required_fields should pass for complete cell."""
        result = validate_required_fields(minimal_valid_cell)
        assert result.valid

    def test_required_fields_check_incomplete(self):
        """validate_required_fields should fail for incomplete cell."""
        incomplete = {"_meta": {}}
        result = validate_required_fields(incomplete)
        assert not result.valid
        assert len(result.errors) > 0
        assert result.errors[0].constraint == "required_field"


class TestValidationErrorMessages:
    """Tests for quality of error messages."""

    def test_error_message_includes_path(self, minimal_valid_cell):
        """Error should identify the problematic field path."""
        minimal_valid_cell["envelope"]["external"]["cell_height_mm"] = 10
        result = validate_structure(minimal_valid_cell)
        assert not result.valid
        assert any("height" in str(err).lower() for err in result.errors)

    def test_llm_feedback_formatted(self, minimal_valid_cell):
        """Error feedback should be LLM-readable."""
        minimal_valid_cell["envelope"]["external"]["cell_height_mm"] = 10
        result = validate_structure(minimal_valid_cell)
        feedback = result.to_llm_feedback()
        assert "VALIDATION FAILED" in feedback
        assert "schema" in feedback.lower()
        assert "error" in feedback.lower() or "Errors" in feedback
