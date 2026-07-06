"""Tests for physics constraint validation (Level 2)."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from forge.engine.validation import validate_physics


@pytest.fixture
def template():
    """Load prismatic_master.yaml."""
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
def valid_cell(template):
    """Create a valid cell using template structure."""
    # Copy a minimal version with all required fields
    return {
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


@pytest.fixture
def valid_cell_balanced(valid_cell):
    """valid_cell with anode loading set so the COMPUTED N/P sits mid-band (~1.125).

    Separate from valid_cell so the negative N/P tests in this module keep the
    original (intentionally inconsistent) loadings and continue to fail-as-designed.
    """
    cell = deepcopy(valid_cell)
    cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 12.954
    return cell


class TestPhysicsConstraints:
    """Tests for physics constraint validation."""

    def test_valid_cell_passes(self, valid_cell_balanced):
        """Valid cell should pass all physics constraints."""
        result = validate_physics(valid_cell_balanced)
        assert result.valid, f"Should pass physics: {result.to_llm_feedback()}"

    def test_np_ratio_below_minimum(self, valid_cell):
        """Computed N/P ratio below 1.05 should fail (lithium plating risk)."""
        # anode 11.514 mg/cm² x 331.161 mAh/g / cathode areal capacity -> computed N/P ~1.000
        valid_cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 11.514
        valid_cell["electrochemistry"]["anode"]["np_ratio"] = 1.00
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("N/P" in str(e) for e in result.errors)
        assert any("1.05" in str(e) for e in result.errors)

    def test_np_ratio_above_maximum(self, valid_cell):
        """Computed N/P ratio above 1.25 should fail (interface instability)."""
        # anode 14.969 mg/cm² -> computed N/P ~1.300
        valid_cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 14.969
        valid_cell["electrochemistry"]["anode"]["np_ratio"] = 1.30
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("N/P" in str(e) for e in result.errors)
        assert any("1.25" in str(e) for e in result.errors)

    def test_np_ratio_at_boundary_min(self, valid_cell):
        """Computed N/P ratio just inside the 1.05 boundary should pass."""
        # anode 12.091 mg/cm² -> computed N/P ~1.0501 (float-safe margin above 1.05)
        valid_cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 12.091
        valid_cell["electrochemistry"]["anode"]["np_ratio"] = 1.05
        result = validate_physics(valid_cell)
        assert not any("N/P" in str(e) for e in result.errors)

    def test_np_ratio_at_boundary_max(self, valid_cell):
        """Computed N/P ratio just inside the 1.25 boundary should pass."""
        # anode 14.392 mg/cm² -> computed N/P ~1.2499 (float-safe margin below 1.25)
        valid_cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 14.392
        valid_cell["electrochemistry"]["anode"]["np_ratio"] = 1.25
        result = validate_physics(valid_cell)
        assert not any("N/P" in str(e) for e in result.errors)

    def test_cathode_loading_out_of_range(self, valid_cell):
        """Cathode loading outside [5, 30] should fail."""
        valid_cell["electrochemistry"]["cathode"]["loading_mg_cm2"] = 50.0
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("loading" in str(e).lower() for e in result.errors)

    def test_anode_loading_out_of_range(self, valid_cell):
        """Anode loading outside [5, 20] should fail."""
        valid_cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 25.0
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("loading" in str(e).lower() for e in result.errors)

    def test_separator_porosity_too_low(self, valid_cell):
        """Separator porosity below 30% should fail."""
        valid_cell["electrochemistry"]["separator"]["porosity_pct"] = 25.0
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("porosity" in str(e).lower() for e in result.errors)

    def test_separator_porosity_too_high(self, valid_cell):
        """Separator porosity above 55% should fail."""
        valid_cell["electrochemistry"]["separator"]["porosity_pct"] = 60.0
        result = validate_physics(valid_cell)
        assert not result.valid

    def test_electrolyte_concentration_out_of_range(self, valid_cell):
        """Electrolyte concentration outside [0.8, 1.5] M should fail."""
        valid_cell["electrochemistry"]["electrolyte"]["salt_concentration_m"] = 0.5
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("concentration" in str(e).lower() for e in result.errors)

    def test_internal_height_negative(self, valid_cell):
        """Walls thicker than cell height should fail."""
        valid_cell["envelope"]["walls"]["wall_top_mm"] = 50.0
        valid_cell["envelope"]["walls"]["wall_bottom_mm"] = 50.0
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("internal" in str(e).lower() for e in result.errors)

    def test_cathode_exceeds_cavity(self, valid_cell):
        """Cathode taller than cavity should fail."""
        valid_cell["stack_config"]["sheet_geometry"]["cathode_height_mm"] = (
            100.0  # Cell height - walls is only ~86mm
        )
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("cathode" in str(e).lower() for e in result.errors)

    def test_stacks_zero_fails(self, valid_cell):
        """Zero stacks should fail."""
        valid_cell["stack_config"]["architecture"]["num_stacks"] = 0
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("stack" in str(e).lower() for e in result.errors)

    def test_electrode_pairs_below_minimum(self, valid_cell):
        """Less than 10 pairs should fail."""
        valid_cell["stack_config"]["architecture"]["electrode_pairs_per_stack"] = 5
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("pair" in str(e).lower() for e in result.errors)

    def test_end_electrode_config_invalid(self, valid_cell):
        """Invalid end electrode config should fail."""
        valid_cell["stack_config"]["architecture"]["end_electrode_config"] = "InvalidConfig"
        result = validate_physics(valid_cell)
        assert not result.valid
        assert any("config" in str(e).lower() for e in result.errors)

    def test_error_feedback_helpful(self, valid_cell):
        """Error feedback should help LLM correct the issue."""
        # anode 10.939 mg/cm² -> computed N/P ~0.950
        valid_cell["electrochemistry"]["anode"]["loading_mg_cm2"] = 10.939
        valid_cell["electrochemistry"]["anode"]["np_ratio"] = 0.95
        result = validate_physics(valid_cell)
        feedback = result.to_llm_feedback()
        assert "N/P" in feedback
        assert "1.05" in feedback
        assert "increase" in feedback.lower() or "decrease" in feedback.lower()


class TestConstraintDescriptions:
    """Tests for constraint documentation."""

    def test_get_constraint_descriptions(self):
        """Should be able to get human-readable constraint descriptions."""
        from forge.engine.validation import get_constraint_descriptions

        desc = get_constraint_descriptions()
        assert "GEOMETRY" in desc
        assert "ELECTROCHEMISTRY" in desc
        assert "N/P ratio" in desc
        assert "lithium plating" in desc
