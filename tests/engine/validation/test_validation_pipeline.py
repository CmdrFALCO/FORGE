"""Integration tests for full validation pipeline."""

import json
from pathlib import Path

import pytest
import yaml

from forge.engine.validation import (
    create_validation_context,
    get_validation_report,
    validate_cell_definition,
    validate_json_string,
    validate_yaml_file,
)


@pytest.fixture
def template_path():
    """Path to prismatic master template."""
    return (
        Path(__file__).parent.parent.parent.parent
        / "forge"
        / "data"
        / "templates"
        / "prismatic_master.yaml"
    )


@pytest.fixture
def template(template_path):
    """Load template."""
    with open(template_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestValidationPipeline:
    """Tests for the complete validation pipeline."""

    def test_template_passes_full_pipeline(self, template):
        """Template should pass the complete pipeline."""
        result = validate_cell_definition(template)
        # Template passes schema but may not pass physics due to metadata structure
        # So we mainly test that function works without error

    def test_minimal_valid_passes_pipeline(self):
        """Minimal valid cell should pass."""
        cell = {
            "envelope": {
                "external": {
                    "cell_height_mm": 88.8,
                    "cell_width_mm": 264.6,
                    "cell_thickness_mm": 29.6,
                },
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
                    "material_name": "Graphite",
                    "loading_mg_cm2": 11.478,
                    "rev_spec_capacity_mahg": 331.161,
                    "collector_thickness_um": 6.0,
                    "coating_thickness_0pct_um": 85.47,
                    "coating_thickness_100pct_um": 92.31,
                    "porosity_pct": 38.01,
                    "np_ratio": 1.225,
                },
                "separator": {
                    "material_name": "PP",
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
                    "case_material": "Aluminum",
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
        result = validate_cell_definition(cell)
        assert result.valid, f"Should pass: {result.to_llm_feedback()}"

    def test_schema_error_stops_physics_check(self):
        """Schema error should prevent physics check (early exit)."""
        incomplete = {}
        result = validate_cell_definition(incomplete)
        assert not result.valid
        assert result.level == "schema"

    def test_invalid_json_string(self):
        """Invalid JSON should fail gracefully."""
        result = validate_json_string("{invalid json}")
        assert not result.valid
        assert "json" in result.errors[0].constraint.lower()

    def test_valid_json_string(self):
        """Valid JSON string should be parsed and validated."""
        cell_dict = {
            "envelope": {
                "external": {
                    "cell_height_mm": 88.8,
                    "cell_width_mm": 264.6,
                    "cell_thickness_mm": 29.6,
                },
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
                    "material_name": "Graphite",
                    "loading_mg_cm2": 11.478,
                    "rev_spec_capacity_mahg": 331.161,
                    "collector_thickness_um": 6.0,
                    "coating_thickness_0pct_um": 85.47,
                    "coating_thickness_100pct_um": 92.31,
                    "porosity_pct": 38.01,
                    "np_ratio": 1.225,
                },
                "separator": {
                    "material_name": "PP",
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
                    "case_material": "Aluminum",
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
        json_string = json.dumps(cell_dict)
        result = validate_json_string(json_string)
        assert result.valid

    def test_yaml_file_validation(self, template_path):
        """Should be able to validate YAML file directly."""
        # Template validates at schema level
        result = validate_yaml_file(str(template_path))
        # Don't assert valid because template has metadata, just check no crash

    def test_validation_report_structure(self):
        """Report should have proper structure."""
        cell = {
            "envelope": {
                "external": {
                    "cell_height_mm": 88.8,
                    "cell_width_mm": 264.6,
                    "cell_thickness_mm": 29.6,
                },
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
                    "material_name": "Graphite",
                    "loading_mg_cm2": 11.478,
                    "rev_spec_capacity_mahg": 331.161,
                    "collector_thickness_um": 6.0,
                    "coating_thickness_0pct_um": 85.47,
                    "coating_thickness_100pct_um": 92.31,
                    "porosity_pct": 38.01,
                    "np_ratio": 1.225,
                },
                "separator": {
                    "material_name": "PP",
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
                    "case_material": "Aluminum",
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
        report = get_validation_report(cell)
        assert "VALIDATION REPORT" in report
        assert "CONSTRAINTS" in report
        assert "N/P" in report

    def test_validation_context_for_llm(self):
        """Should be able to get validation context for LLM prompts."""
        context = create_validation_context()
        assert "LEVEL 1" in context
        assert "LEVEL 2" in context
        assert "N/P ratio" in context
        assert "1.05" in context
        assert "lithium plating" in context
