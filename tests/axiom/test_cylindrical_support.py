"""Tests for cylindrical cell support in LLM driver.

This module tests the cylindrical cell extensions:
- Schema validation for cylindrical cells
- Physics constraint validation for cylindrical cells
- Conversion from cylindrical YAML to CylindricalCellInput
- Prompt builder for cylindrical cells
"""

import pytest

from forge.engine.conversion import from_cylindrical_template_format
from forge.axiom.generator.prompt_builder import (
    CYLINDRICAL_PARAMETER_SCHEMA,
    build_retry_prompt,
    build_system_prompt,
)
from forge.engine.validation.constraint_validator import (
    COMMON_CONSTRAINTS,
    CYLINDRICAL_CONSTRAINTS,
    check_cylindrical_can_material_valid,
    check_cylindrical_format_consistency,
    check_cylindrical_header_height,
    check_cylindrical_jelly_roll_fits,
    check_cylindrical_mandrel_diameter,
    check_cylindrical_tab_type_valid,
    check_cylindrical_tension_factor,
    check_cylindrical_winding_clearance,
    validate_physics,
)
from forge.engine.validation.pipeline import validate_cell_definition
from forge.engine.validation.schema_validator import load_schema, validate_structure


# Valid 21700 cylindrical cell definition for testing
VALID_CYLINDRICAL_CELL = {
    "_meta": {
        "cell_type": "cylindrical",
        "format": "21700",
        "design_intent": "Test 21700 cylindrical cell",
    },
    "geometry": {
        "diameter_mm": 21.0,
        "length_mm": 70.0,
        "can_wall_thickness_mm": 0.25,
        "can_bottom_thickness_mm": 0.4,
        "header_height_mm": 3.5,
    },
    "winding": {
        "mandrel_diameter_mm": 3.5,
        "winding_clearance_mm": 0.15,
        "winding_tension_factor": 0.95,
        "tab_type": "traditional",
        "anode_tab_width_mm": 6.0,
        "anode_tab_thickness_mm": 0.1,
        "cathode_tab_width_mm": 5.0,
        "cathode_tab_thickness_mm": 0.15,
    },
    "electrochemistry": {
        "cathode": {
            "material_name": "NMC811",
            "loading_mg_cm2": 22.0,
            "rev_spec_capacity_mahg": 200.0,
            "collector_thickness_um": 12.0,
            "coating_thickness_0pct_um": 60.0,
            "coating_thickness_100pct_um": 62.0,
            "porosity_pct": 25.0,
        },
        "anode": {
            "material_name": "Graphite",
            "loading_mg_cm2": 12.5,
            "rev_spec_capacity_mahg": 355.0,
            "collector_thickness_um": 8.0,
            "coating_thickness_0pct_um": 85.0,
            "coating_thickness_100pct_um": 90.0,
            "porosity_pct": 32.0,
            "np_ratio": 1.12,
        },
        "separator": {
            "material_name": "Ceramic-coated PE",
            "thickness_um": 12.0,
            "porosity_pct": 42.0,
            "areal_weight_mgcm2": 1.0,
        },
        "electrolyte": {
            "material_name": "LiPF6 in EC:EMC",
            "density_g_cm3": 1.22,
            "excess_factor": 1.05,
        },
    },
    "housing": {
        "can_material": "nickel_plated_steel",
        "header_mass_g": 2.0,
        "bottom_insulator_mass_g": 0.1,
        "top_insulator_mass_g": 0.1,
    },
}


# Valid 4680 tabless cell for testing
VALID_4680_TABLESS_CELL = {
    "_meta": {
        "cell_type": "cylindrical",
        "format": "4680",
        "design_intent": "Test 4680 tabless cell",
    },
    "geometry": {
        "diameter_mm": 46.0,
        "length_mm": 80.0,
        "can_wall_thickness_mm": 0.35,
        "can_bottom_thickness_mm": 0.5,
        "header_height_mm": 4.0,
    },
    "winding": {
        "mandrel_diameter_mm": 5.0,
        "winding_clearance_mm": 0.2,
        "winding_tension_factor": 0.95,
        "tab_type": "tabless",
        "anode_foil_extension_mm": 3.0,
        "cathode_foil_extension_mm": 3.0,
    },
    "electrochemistry": {
        "cathode": {
            "material_name": "NMC811",
            "loading_mg_cm2": 24.0,
            "rev_spec_capacity_mahg": 195.0,
            "collector_thickness_um": 14.0,
            "coating_thickness_0pct_um": 65.0,
            "coating_thickness_100pct_um": 68.0,
            "porosity_pct": 24.0,
        },
        "anode": {
            "material_name": "Graphite-SiO",
            "loading_mg_cm2": 11.5,
            "rev_spec_capacity_mahg": 420.0,
            "collector_thickness_um": 8.0,
            "coating_thickness_0pct_um": 70.0,
            "coating_thickness_100pct_um": 75.0,
            "porosity_pct": 30.0,
            "np_ratio": 1.15,
        },
        "separator": {
            "material_name": "Ceramic-coated PE",
            "thickness_um": 14.0,
            "porosity_pct": 45.0,
            "areal_weight_mgcm2": 1.2,
        },
        "electrolyte": {
            "material_name": "LiPF6 in EC:EMC",
            "density_g_cm3": 1.22,
            "excess_factor": 1.08,
        },
    },
    "housing": {
        "can_material": "aluminum",
        "header_mass_g": 5.0,
        "bottom_insulator_mass_g": 0.3,
        "top_insulator_mass_g": 0.3,
    },
}


class TestCylindricalSchemaLoading:
    """Tests for loading the cylindrical schema."""

    def test_load_cylindrical_schema(self):
        """Test that cylindrical schema can be loaded."""
        schema = load_schema(cell_type="cylindrical")
        assert schema is not None
        assert "properties" in schema
        assert "geometry" in schema["properties"]
        assert "winding" in schema["properties"]
        assert "electrochemistry" in schema["properties"]
        assert "housing" in schema["properties"]

    def test_cylindrical_schema_has_correct_required_fields(self):
        """Test that cylindrical schema requires the correct top-level fields."""
        schema = load_schema(cell_type="cylindrical")
        required = schema.get("required", [])
        assert "geometry" in required
        assert "winding" in required
        assert "electrochemistry" in required
        assert "housing" in required

    def test_cylindrical_schema_geometry_structure(self):
        """Test that geometry section has cylindrical-specific fields."""
        schema = load_schema(cell_type="cylindrical")
        geo_props = schema["properties"]["geometry"]["properties"]
        assert "diameter_mm" in geo_props
        assert "length_mm" in geo_props
        assert "can_wall_thickness_mm" in geo_props
        assert "can_bottom_thickness_mm" in geo_props
        assert "header_height_mm" in geo_props

    def test_cylindrical_schema_winding_structure(self):
        """Test that winding section has required fields."""
        schema = load_schema(cell_type="cylindrical")
        winding_props = schema["properties"]["winding"]["properties"]
        assert "mandrel_diameter_mm" in winding_props
        assert "winding_clearance_mm" in winding_props
        assert "winding_tension_factor" in winding_props
        assert "tab_type" in winding_props


class TestCylindricalSchemaValidation:
    """Tests for cylindrical schema validation."""

    def test_valid_cylindrical_cell_passes_schema(self):
        """Test that a valid cylindrical cell passes schema validation."""
        result = validate_structure(VALID_CYLINDRICAL_CELL, cell_type="cylindrical")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_valid_4680_tabless_passes_schema(self):
        """Test that a valid 4680 tabless cell passes schema validation."""
        result = validate_structure(VALID_4680_TABLESS_CELL, cell_type="cylindrical")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_missing_geometry_fails(self):
        """Test that missing geometry section fails."""
        cell = {k: v for k, v in VALID_CYLINDRICAL_CELL.items() if k != "geometry"}
        result = validate_structure(cell, cell_type="cylindrical")
        assert not result.valid

    def test_missing_winding_fails(self):
        """Test that missing winding section fails."""
        cell = {k: v for k, v in VALID_CYLINDRICAL_CELL.items() if k != "winding"}
        result = validate_structure(cell, cell_type="cylindrical")
        assert not result.valid

    def test_missing_housing_fails(self):
        """Test that missing housing section fails."""
        cell = {k: v for k, v in VALID_CYLINDRICAL_CELL.items() if k != "housing"}
        result = validate_structure(cell, cell_type="cylindrical")
        assert not result.valid


class TestCylindricalPhysicsConstraints:
    """Tests for cylindrical-specific physics constraints."""

    def test_mandrel_below_minimum(self):
        """Test that mandrel diameter below 1.5mm fails."""
        cell = {"winding": {"mandrel_diameter_mm": 1.0}}
        error = check_cylindrical_mandrel_diameter(cell)
        assert error is not None
        assert "1.5" in error.message

    def test_mandrel_above_maximum(self):
        """Test that mandrel diameter above 8.0mm fails."""
        cell = {"winding": {"mandrel_diameter_mm": 9.0}}
        error = check_cylindrical_mandrel_diameter(cell)
        assert error is not None
        assert "8.0" in error.message

    def test_mandrel_valid(self):
        """Test that valid mandrel diameter passes."""
        cell = {"winding": {"mandrel_diameter_mm": 3.5}}
        error = check_cylindrical_mandrel_diameter(cell)
        assert error is None

    def test_winding_clearance_below_minimum(self):
        """Test that winding clearance below 0.05mm fails."""
        cell = {"winding": {"winding_clearance_mm": 0.02}}
        error = check_cylindrical_winding_clearance(cell)
        assert error is not None
        assert "0.05" in error.message

    def test_winding_clearance_above_maximum(self):
        """Test that winding clearance above 0.5mm fails."""
        cell = {"winding": {"winding_clearance_mm": 0.7}}
        error = check_cylindrical_winding_clearance(cell)
        assert error is not None
        assert "0.5" in error.message

    def test_winding_clearance_valid(self):
        """Test that valid winding clearance passes."""
        cell = {"winding": {"winding_clearance_mm": 0.15}}
        error = check_cylindrical_winding_clearance(cell)
        assert error is None

    def test_tension_factor_below_minimum(self):
        """Test that tension factor below 0.90 fails."""
        cell = {"winding": {"winding_tension_factor": 0.85}}
        error = check_cylindrical_tension_factor(cell)
        assert error is not None
        assert "0.90" in error.message

    def test_tension_factor_above_maximum(self):
        """Test that tension factor above 1.0 fails."""
        cell = {"winding": {"winding_tension_factor": 1.05}}
        error = check_cylindrical_tension_factor(cell)
        assert error is not None
        assert "1.0" in error.message

    def test_tension_factor_valid(self):
        """Test that valid tension factor passes."""
        cell = {"winding": {"winding_tension_factor": 0.95}}
        error = check_cylindrical_tension_factor(cell)
        assert error is None

    def test_invalid_tab_type(self):
        """Test that invalid tab type fails."""
        cell = {"winding": {"tab_type": "invalid"}}
        error = check_cylindrical_tab_type_valid(cell)
        assert error is not None
        assert "invalid" in error.message.lower()

    def test_valid_traditional_tab_type(self):
        """Test that traditional tab type passes."""
        cell = {"winding": {"tab_type": "traditional"}}
        error = check_cylindrical_tab_type_valid(cell)
        assert error is None

    def test_valid_tabless_tab_type(self):
        """Test that tabless tab type passes."""
        cell = {"winding": {"tab_type": "tabless"}}
        error = check_cylindrical_tab_type_valid(cell)
        assert error is None

    def test_invalid_can_material(self):
        """Test that invalid can material fails."""
        cell = {"housing": {"can_material": "plastic"}}
        error = check_cylindrical_can_material_valid(cell)
        assert error is not None
        assert "plastic" in error.message.lower()

    def test_valid_can_materials(self):
        """Test that valid can materials pass."""
        for material in ["steel", "aluminum", "nickel_plated_steel"]:
            cell = {"housing": {"can_material": material}}
            error = check_cylindrical_can_material_valid(cell)
            assert error is None, f"Material {material} should be valid"

    def test_jelly_roll_does_not_fit(self):
        """Test that jelly roll that doesn't fit fails."""
        cell = {
            "geometry": {"diameter_mm": 18.0, "can_wall_thickness_mm": 0.25},
            "winding": {
                "mandrel_diameter_mm": 15.0,  # Too large
                "winding_clearance_mm": 0.5,
            },
        }
        error = check_cylindrical_jelly_roll_fits(cell)
        assert error is not None
        assert "insufficient" in error.message.lower()

    def test_jelly_roll_fits(self):
        """Test that valid jelly roll configuration passes."""
        cell = {
            "geometry": {"diameter_mm": 21.0, "can_wall_thickness_mm": 0.25},
            "winding": {"mandrel_diameter_mm": 3.5, "winding_clearance_mm": 0.15},
        }
        error = check_cylindrical_jelly_roll_fits(cell)
        assert error is None

    def test_header_height_below_minimum(self):
        """Test that header height below 2.0mm fails."""
        cell = {"geometry": {"header_height_mm": 1.5}}
        error = check_cylindrical_header_height(cell)
        assert error is not None
        assert "2.0" in error.message

    def test_header_height_above_maximum(self):
        """Test that header height above 6.0mm fails."""
        cell = {"geometry": {"header_height_mm": 7.0}}
        error = check_cylindrical_header_height(cell)
        assert error is not None
        assert "6.0" in error.message

    def test_header_height_valid(self):
        """Test that valid header height passes."""
        cell = {"geometry": {"header_height_mm": 3.5}}
        error = check_cylindrical_header_height(cell)
        assert error is None

    def test_format_consistency_21700_valid(self):
        """Test that correct 21700 dimensions pass."""
        cell = {"_meta": {"format": "21700"}, "geometry": {"diameter_mm": 21.0, "length_mm": 70.0}}
        error = check_cylindrical_format_consistency(cell)
        assert error is None

    def test_format_consistency_21700_wrong_diameter(self):
        """Test that wrong diameter for 21700 fails."""
        cell = {
            "_meta": {"format": "21700"},
            "geometry": {
                "diameter_mm": 18.0,  # Should be ~21
                "length_mm": 70.0,
            },
        }
        error = check_cylindrical_format_consistency(cell)
        assert error is not None
        assert "diameter" in error.path

    def test_format_consistency_custom_any_dimensions(self):
        """Test that custom format allows any dimensions."""
        cell = {"_meta": {"format": "custom"}, "geometry": {"diameter_mm": 25.0, "length_mm": 55.0}}
        error = check_cylindrical_format_consistency(cell)
        assert error is None

    def test_valid_cylindrical_passes_physics(self):
        """Test that a valid cylindrical cell passes physics validation."""
        result = validate_physics(VALID_CYLINDRICAL_CELL, cell_type="cylindrical")
        assert result.valid, f"Expected valid, got errors: {result.errors}"


class TestCylindricalFullValidation:
    """Tests for full cylindrical validation pipeline."""

    def test_full_validation_passes(self):
        """Test that valid cylindrical cell passes full validation."""
        result = validate_cell_definition(VALID_CYLINDRICAL_CELL, cell_type="cylindrical")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_4680_full_validation_passes(self):
        """Test that valid 4680 tabless cell passes full validation."""
        result = validate_cell_definition(VALID_4680_TABLESS_CELL, cell_type="cylindrical")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_invalid_np_ratio_fails(self):
        """Test that invalid N/P ratio fails validation."""
        cell = VALID_CYLINDRICAL_CELL.copy()
        cell = {**cell}
        cell["electrochemistry"] = {**cell["electrochemistry"]}
        cell["electrochemistry"]["anode"] = {**cell["electrochemistry"]["anode"]}
        cell["electrochemistry"]["anode"]["np_ratio"] = 0.9  # Below minimum 1.05

        result = validate_cell_definition(cell, cell_type="cylindrical")
        assert not result.valid


class TestCylindricalPromptBuilder:
    """Tests for cylindrical prompt builder."""

    def test_build_cylindrical_prompt(self):
        """Test that cylindrical system prompt is built correctly."""
        prompt = build_system_prompt(cell_type="cylindrical")
        assert "cylindrical" in prompt.lower()
        assert "geometry" in prompt
        assert "winding" in prompt
        assert "mandrel" in prompt
        assert "tab_type" in prompt

    def test_cylindrical_prompt_includes_example(self):
        """Test that cylindrical prompt includes example cell."""
        prompt = build_system_prompt(include_example=True, cell_type="cylindrical")
        assert "21700" in prompt or "4680" in prompt
        assert "winding" in prompt.lower()

    def test_retry_prompt_includes_cell_type(self):
        """Test that retry prompt mentions cylindrical."""
        retry = build_retry_prompt(
            "Design a 21700 cell", "Validation error", cell_type="cylindrical"
        )
        assert "cylindrical" in retry

    def test_cylindrical_parameter_schema_content(self):
        """Test that cylindrical parameter schema has key fields."""
        assert "diameter_mm" in CYLINDRICAL_PARAMETER_SCHEMA
        assert "length_mm" in CYLINDRICAL_PARAMETER_SCHEMA
        assert "mandrel_diameter_mm" in CYLINDRICAL_PARAMETER_SCHEMA
        assert "tab_type" in CYLINDRICAL_PARAMETER_SCHEMA
        assert "can_material" in CYLINDRICAL_PARAMETER_SCHEMA


class TestCylindricalConversion:
    """Tests for cylindrical template conversion."""

    def test_convert_valid_cylindrical_cell(self):
        """Test that valid cylindrical cell converts successfully."""
        cell_input = from_cylindrical_template_format(VALID_CYLINDRICAL_CELL)

        assert cell_input is not None
        assert cell_input.geometry.diameter_mm == 21.0
        assert cell_input.geometry.length_mm == 70.0
        assert cell_input.geometry.can_wall_thickness_mm == 0.25
        assert cell_input.geometry.header_height_mm == 3.5
        assert cell_input.winding.mandrel_diameter_mm == 3.5
        assert cell_input.winding.winding_tension_factor == 0.95
        assert cell_input.cathode.name == "NMC811"
        assert cell_input.anode.name == "Graphite"

    def test_convert_valid_4680_tabless_cell(self):
        """Test that valid 4680 tabless cell converts successfully."""
        cell_input = from_cylindrical_template_format(VALID_4680_TABLESS_CELL)

        assert cell_input is not None
        assert cell_input.geometry.diameter_mm == 46.0
        assert cell_input.geometry.length_mm == 80.0
        assert cell_input.winding.mandrel_diameter_mm == 5.0
        # Check tab type is tabless
        from forge.engine.models.cylindrical import TabType

        assert cell_input.winding.tab_type == TabType.TABLESS

    def test_conversion_missing_geometry_fails(self):
        """Test that missing geometry fails conversion."""
        cell = {k: v for k, v in VALID_CYLINDRICAL_CELL.items() if k != "geometry"}
        with pytest.raises(Exception):  # MissingFieldError or similar
            from_cylindrical_template_format(cell)

    def test_conversion_missing_winding_fails(self):
        """Test that missing winding fails conversion."""
        cell = {k: v for k, v in VALID_CYLINDRICAL_CELL.items() if k != "winding"}
        with pytest.raises(Exception):  # MissingFieldError or similar
            from_cylindrical_template_format(cell)

    def test_conversion_can_material_mapping(self):
        """Test that can material is mapped correctly."""
        cell_input = from_cylindrical_template_format(VALID_CYLINDRICAL_CELL)
        from forge.engine.models.cylindrical import CanMaterial

        assert cell_input.can_material == CanMaterial.NICKEL_PLATED_STEEL

    def test_conversion_header_simplified_created(self):
        """Test that simplified header is created from housing."""
        cell_input = from_cylindrical_template_format(VALID_CYLINDRICAL_CELL)
        assert cell_input.header_simplified is not None
        assert cell_input.header_simplified.total_mass_g == 2.0


class TestCylindricalConstraintCounts:
    """Tests for cylindrical constraint organization."""

    def test_cylindrical_constraints_exist(self):
        """Test that cylindrical-specific constraints are defined."""
        assert len(CYLINDRICAL_CONSTRAINTS) > 0
        assert check_cylindrical_mandrel_diameter in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_winding_clearance in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_tension_factor in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_tab_type_valid in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_can_material_valid in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_jelly_roll_fits in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_header_height in CYLINDRICAL_CONSTRAINTS
        assert check_cylindrical_format_consistency in CYLINDRICAL_CONSTRAINTS

    def test_common_constraints_shared(self):
        """Test that common constraints are shared between cell types."""
        from forge.engine.validation.constraint_validator import check_np_ratio

        assert check_np_ratio in COMMON_CONSTRAINTS


class TestCylindricalFormats:
    """Tests for standard cylindrical format (18650, 21700, 4680) support."""

    def test_18650_format_dimensions(self):
        """Test that 18650 format expects correct dimensions."""
        cell = {"_meta": {"format": "18650"}, "geometry": {"diameter_mm": 18.0, "length_mm": 65.0}}
        error = check_cylindrical_format_consistency(cell)
        assert error is None

    def test_21700_format_dimensions(self):
        """Test that 21700 format expects correct dimensions."""
        cell = {"_meta": {"format": "21700"}, "geometry": {"diameter_mm": 21.0, "length_mm": 70.0}}
        error = check_cylindrical_format_consistency(cell)
        assert error is None

    def test_4680_format_dimensions(self):
        """Test that 4680 format expects correct dimensions."""
        cell = {"_meta": {"format": "4680"}, "geometry": {"diameter_mm": 46.0, "length_mm": 80.0}}
        error = check_cylindrical_format_consistency(cell)
        assert error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

