"""Tests for pouch cell support in LLM driver.

This module tests the pouch cell extensions:
- Schema validation for pouch cells
- Physics constraint validation for pouch cells
- Conversion from pouch YAML to PouchCellInput
- Prompt builder for pouch cells
"""

import pytest

from forge.axiom.generator.prompt_builder import (
    build_retry_prompt,
    build_system_prompt,
)
from forge.engine.conversion import from_pouch_template_format
from forge.engine.validation.constraint_validator import (
    COMMON_CONSTRAINTS,
    POUCH_CONSTRAINTS,
    check_pouch_anode_offset_positive,
    check_pouch_packaging_offsets,
    check_pouch_separator_larger_than_anode,
    check_pouch_separator_offset_positive,
    validate_physics,
)
from forge.engine.validation.pipeline import validate_cell_definition
from forge.engine.validation.schema_validator import load_schema, validate_structure

# Valid pouch cell definition for testing
VALID_POUCH_CELL = {
    "_meta": {"cell_type": "pouch", "design_intent": "Test pouch cell"},
    "geometry": {
        "cathode_height_mm": 100.0,
        "cathode_width_mm": 80.0,
        "anode_offset_mm": 2.0,
        "separator_offset_mm": 2.5,
    },
    "stack_config": {
        "num_stacks": 1,
        "electrode_pairs_per_stack": 20,
        "end_electrode_config": "BothNegative",
    },
    "electrochemistry": {
        "cathode": {
            "material_name": "NMC811",
            "loading_mg_cm2": 20.0,
            "rev_spec_capacity_mahg": 195.0,
            "collector_thickness_um": 12.0,
            "coating_thickness_0pct_um": 55.0,
            "coating_thickness_100pct_um": 57.0,
            "porosity_pct": 25.0,
        },
        "anode": {
            "material_name": "Graphite",
            "loading_mg_cm2": 12.65,
            "rev_spec_capacity_mahg": 355.0,
            "collector_thickness_um": 6.0,
            "coating_thickness_0pct_um": 75.0,
            "coating_thickness_100pct_um": 80.0,
            "porosity_pct": 35.0,
            "np_ratio": 1.15,
        },
        "separator": {
            "material_name": "Ceramic-coated PE",
            "thickness_um": 14.0,
            "porosity_pct": 42.0,
            "areal_weight_mgcm2": 1.2,
        },
        "electrolyte": {
            "material_name": "LiPF6 in EC:EMC",
            "density_g_cm3": 1.22,
            "excess_factor": 1.1,
        },
    },
    "tabs": {
        "cathode": {
            "material": "Aluminum",
            "height_mm": 25.0,
            "width_mm": 30.0,
            "thickness_mm": 0.3,
        },
        "anode": {
            "material": "Nickel-plated Copper",
            "height_mm": 25.0,
            "width_mm": 25.0,
            "thickness_mm": 0.2,
        },
    },
    "packaging": {
        "pouch_thickness_mm": 0.113,
        "offset_top_mm": 8.0,
        "offset_bottom_mm": 4.0,
        "offset_sides_mm": 5.0,
    },
}


class TestPouchSchemaLoading:
    """Tests for loading the pouch schema."""

    def test_load_pouch_schema(self):
        """Test that pouch schema can be loaded."""
        schema = load_schema(cell_type="pouch")
        assert schema is not None
        assert "properties" in schema
        assert "geometry" in schema["properties"]
        assert "stack_config" in schema["properties"]
        assert "electrochemistry" in schema["properties"]
        assert "tabs" in schema["properties"]
        assert "packaging" in schema["properties"]

    def test_pouch_schema_has_correct_required_fields(self):
        """Test that pouch schema requires the correct top-level fields."""
        schema = load_schema(cell_type="pouch")
        required = schema.get("required", [])
        assert "geometry" in required
        assert "stack_config" in required
        assert "electrochemistry" in required
        assert "tabs" in required
        assert "packaging" in required

    def test_pouch_schema_geometry_structure(self):
        """Test that geometry section has pouch-specific fields."""
        schema = load_schema(cell_type="pouch")
        geo_props = schema["properties"]["geometry"]["properties"]
        assert "cathode_height_mm" in geo_props
        assert "cathode_width_mm" in geo_props
        assert "anode_offset_mm" in geo_props
        assert "separator_offset_mm" in geo_props


class TestPouchSchemaValidation:
    """Tests for pouch schema validation."""

    def test_valid_pouch_cell_passes_schema(self):
        """Test that a valid pouch cell passes schema validation."""
        result = validate_structure(VALID_POUCH_CELL, cell_type="pouch")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_missing_geometry_fails(self):
        """Test that missing geometry section fails."""
        cell = {k: v for k, v in VALID_POUCH_CELL.items() if k != "geometry"}
        result = validate_structure(cell, cell_type="pouch")
        assert not result.valid

    def test_missing_tabs_fails(self):
        """Test that missing tabs section fails."""
        cell = {k: v for k, v in VALID_POUCH_CELL.items() if k != "tabs"}
        result = validate_structure(cell, cell_type="pouch")
        assert not result.valid


class TestPouchPhysicsConstraints:
    """Tests for pouch-specific physics constraints."""

    def test_anode_offset_below_minimum(self):
        """Test that anode offset below 0.5mm fails."""
        cell = {"geometry": {"anode_offset_mm": 0.3}}
        error = check_pouch_anode_offset_positive(cell)
        assert error is not None
        assert "0.5" in error.message

    def test_anode_offset_above_maximum(self):
        """Test that anode offset above 5.0mm fails."""
        cell = {"geometry": {"anode_offset_mm": 6.0}}
        error = check_pouch_anode_offset_positive(cell)
        assert error is not None
        assert "5.0" in error.message

    def test_anode_offset_valid(self):
        """Test that valid anode offset passes."""
        cell = {"geometry": {"anode_offset_mm": 2.0}}
        error = check_pouch_anode_offset_positive(cell)
        assert error is None

    def test_separator_offset_below_anode(self):
        """Test that separator offset smaller than anode offset fails."""
        cell = {"geometry": {"anode_offset_mm": 2.5, "separator_offset_mm": 2.0}}
        error = check_pouch_separator_larger_than_anode(cell)
        assert error is not None
        assert "smaller than anode" in error.message.lower()

    def test_separator_offset_valid(self):
        """Test that valid separator offset passes."""
        cell = {"geometry": {"anode_offset_mm": 2.0, "separator_offset_mm": 2.5}}
        error = check_pouch_separator_larger_than_anode(cell)
        assert error is None

    def test_packaging_offset_below_minimum(self):
        """Test that packaging offset below 2mm fails."""
        cell = {
            "packaging": {"offset_top_mm": 1.5, "offset_bottom_mm": 4.0, "offset_sides_mm": 5.0}
        }
        error = check_pouch_packaging_offsets(cell)
        assert error is not None
        assert "2.0" in error.message

    def test_valid_pouch_passes_physics(self):
        """Test that a valid pouch cell passes physics validation."""
        result = validate_physics(VALID_POUCH_CELL, cell_type="pouch")
        assert result.valid, f"Expected valid, got errors: {result.errors}"


class TestPouchFullValidation:
    """Tests for full pouch validation pipeline."""

    def test_full_validation_passes(self):
        """Test that valid pouch cell passes full validation."""
        result = validate_cell_definition(VALID_POUCH_CELL, cell_type="pouch")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_invalid_np_ratio_fails(self):
        """Test that invalid N/P ratio fails validation (schema or physics)."""
        cell = VALID_POUCH_CELL.copy()
        cell = {**cell}  # shallow copy
        cell["electrochemistry"] = {**cell["electrochemistry"]}
        cell["electrochemistry"]["anode"] = {**cell["electrochemistry"]["anode"]}
        cell["electrochemistry"]["anode"]["np_ratio"] = 0.9  # Below minimum 1.05

        result = validate_cell_definition(cell, cell_type="pouch")
        assert not result.valid
        # Error could be from schema (min bounds) or physics (N/P ratio check)
        error_paths = [e.path for e in result.errors]
        error_messages = [e.message for e in result.errors]
        # Check that the error mentions np_ratio or the value
        assert any(
            "np_ratio" in path or "0.9" in msg for path, msg in zip(error_paths, error_messages)
        )


class TestPouchPromptBuilder:
    """Tests for pouch prompt builder."""

    def test_build_pouch_prompt(self):
        """Test that pouch system prompt is built correctly."""
        prompt = build_system_prompt(cell_type="pouch")
        assert "pouch" in prompt.lower()
        assert "geometry" in prompt
        assert "anode_offset_mm" in prompt
        assert "separator_offset_mm" in prompt

    def test_pouch_prompt_includes_example(self):
        """Test that pouch prompt includes example cell."""
        prompt = build_system_prompt(include_example=True, cell_type="pouch")
        assert "10Ah" in prompt or "pouch" in prompt.lower()
        assert "tabs:" in prompt

    def test_retry_prompt_includes_cell_type(self):
        """Test that retry prompt mentions pouch."""
        retry = build_retry_prompt("Design a pouch cell", "Validation error", cell_type="pouch")
        assert "pouch" in retry


class TestPouchConversion:
    """Tests for pouch template conversion."""

    def test_convert_valid_pouch_cell(self):
        """Test that valid pouch cell converts successfully."""
        cell_input = from_pouch_template_format(VALID_POUCH_CELL)

        assert cell_input is not None
        assert cell_input.geometry.cathode_height_mm == 100.0
        assert cell_input.geometry.cathode_width_mm == 80.0
        assert cell_input.geometry.anode_offset_y_mm == 2.0
        assert cell_input.geometry.anode_offset_x_mm == 2.0
        assert cell_input.geometry.separator_offset_y_mm == 2.5
        assert cell_input.stack_config.number_of_stacks == 1
        assert cell_input.stack_config.electrode_pairs_per_stack == 20
        assert cell_input.cathode.name == "NMC811"
        assert cell_input.anode.name == "Graphite"
        assert cell_input.cathode_tab.material == "Aluminum"
        assert cell_input.anode_tab.material == "Nickel-plated Copper"

    def test_conversion_missing_geometry_fails(self):
        """Test that missing geometry fails conversion."""
        cell = {k: v for k, v in VALID_POUCH_CELL.items() if k != "geometry"}
        with pytest.raises(Exception):  # MissingFieldError or similar
            from_pouch_template_format(cell)

    def test_conversion_tab_density_inference(self):
        """Test that tab density is inferred from material name."""
        cell_input = from_pouch_template_format(VALID_POUCH_CELL)

        # Aluminum tab should have density ~2.70
        assert cell_input.cathode_tab.density_gcm3 == pytest.approx(2.70, rel=0.01)
        # Copper tab should have density ~8.96
        assert cell_input.anode_tab.density_gcm3 == pytest.approx(8.96, rel=0.01)


class TestPouchConstraintCounts:
    """Tests for pouch constraint organization."""

    def test_pouch_constraints_exist(self):
        """Test that pouch-specific constraints are defined."""
        assert len(POUCH_CONSTRAINTS) > 0
        assert check_pouch_anode_offset_positive in POUCH_CONSTRAINTS
        assert check_pouch_separator_offset_positive in POUCH_CONSTRAINTS
        assert check_pouch_separator_larger_than_anode in POUCH_CONSTRAINTS
        assert check_pouch_packaging_offsets in POUCH_CONSTRAINTS

    def test_common_constraints_shared(self):
        """Test that common constraints are shared between cell types."""
        from forge.engine.validation.constraint_validator import check_np_ratio

        assert check_np_ratio in COMMON_CONSTRAINTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

