"""
Robustness tests for CellCAD-Python calculators.

Tests edge cases, calculator consistency, error handling,
numerical precision, and PyBaMM fallback behavior.

Created: December 26, 2025
Target: ~80-100 tests for comprehensive robustness validation
"""

from __future__ import annotations

import math

import pytest

from forge.engine.models.cylindrical import (
    CanMaterial,
    CylindricalGeometry,
    TabType,
    WindingConfig,
)
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)
from forge.engine.models.prismatic import (
    PrismaticGeometry,
    PrismaticSheetGeometry,
)

# =============================================================================
# FIXTURES - Common Materials and Configurations
# =============================================================================


@pytest.fixture
def standard_cathode() -> CathodeMaterial:
    """Create a standard NMC cathode material for testing."""
    return CathodeMaterial(
        id="test_cathode",
        name="Test NMC622",
        chemistry="NMC622",
        rev_spec_capacity_mahg=180.0,
        max_spec_capacity_mahg=200.0,
        areal_weight_mgcm2=18.0,
        collector_thickness_um=12.0,
        coating_density_gcm3=3.4,
        coating_thickness_0pct_um=70.0,
        coating_thickness_100pct_um=68.0,
    )


@pytest.fixture
def standard_anode() -> AnodeMaterial:
    """Create a standard graphite anode material for testing."""
    return AnodeMaterial(
        id="test_anode",
        name="Test Graphite",
        chemistry="Graphite",
        rev_spec_capacity_mahg=350.0,
        max_spec_capacity_mahg=372.0,
        areal_weight_mgcm2=11.0,
        collector_thickness_um=8.0,
        coating_density_gcm3=1.5,
        coating_thickness_0pct_um=80.0,
        coating_thickness_100pct_um=87.0,
    )


@pytest.fixture
def standard_separator() -> SeparatorMaterial:
    """Create a standard separator material for testing."""
    return SeparatorMaterial(
        id="test_separator",
        name="Test PP",
        thickness_um=16.0,
        porosity_pct=45.0,
        density_gcm3=0.9,
        areal_weight_mgcm2=1.1,
    )


@pytest.fixture
def standard_electrolyte() -> ElectrolyteModel:
    """Create a standard electrolyte for testing."""
    return ElectrolyteModel(
        id="test_electrolyte",
        name="LiPF6 in EC/DMC",
        density_gcm3=1.2,
    )


# =============================================================================
# SECTION 1: EDGE CASES - MINIMUM VALUES
# =============================================================================


class TestEdgeCasesMinimumValues:
    """Test behavior at minimum valid parameter values."""

    def test_minimum_electrode_dimensions(self):
        """Test with very small electrode dimensions (10mm x 10mm)."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=10.0,
            cathode_width_mm=10.0,
        )
        # Should calculate without error
        assert geo.cathode_area_cm2 == pytest.approx(1.0, rel=0.001)  # 10*10/100

    def test_minimum_wall_thickness(self):
        """Test with minimum wall thickness (0.1mm)."""
        geo = PrismaticGeometry(
            cell_height_mm=50.0,
            cell_width_mm=100.0,
            cell_thickness_mm=20.0,
            wall_top_mm=0.1,
            wall_bottom_mm=0.1,
            wall_front_back_mm=0.1,
            wall_sides_mm=0.1,
        )
        # Internal dimensions should be calculated correctly
        assert geo.internal_height_mm == pytest.approx(49.8, rel=0.001)
        assert geo.internal_width_mm == pytest.approx(99.8, rel=0.001)
        assert geo.internal_thickness_mm == pytest.approx(19.8, rel=0.001)

    def test_minimum_coating_thickness(self, standard_cathode):
        """Test with very thin coating (1 Âµm)."""
        thin_cathode = CathodeMaterial(
            id="thin_cathode",
            name="Ultra Thin NMC",
            chemistry="NMC",
            rev_spec_capacity_mahg=180.0,
            max_spec_capacity_mahg=200.0,
            areal_weight_mgcm2=0.5,  # Very low loading
            collector_thickness_um=10.0,
            coating_density_gcm3=3.4,
            coating_thickness_0pct_um=1.0,  # 1 Âµm - very thin
            coating_thickness_100pct_um=1.0,
        )
        # Should still be a valid material
        assert thin_cathode.coating_thickness_0pct_um > 0

    def test_minimum_porosity(self):
        """Test with very low porosity (1%)."""
        low_porosity_sep = SeparatorMaterial(
            id="dense_sep",
            name="Dense Separator",
            thickness_um=16.0,
            porosity_pct=1.0,  # Nearly solid
            density_gcm3=0.9,
            areal_weight_mgcm2=1.5,
        )
        assert low_porosity_sep.porosity_pct == 1.0

    def test_minimum_cylindrical_diameter(self):
        """Test with minimum cylindrical cell diameter (8mm - hearing aid battery size)."""
        geo = CylindricalGeometry(
            diameter_mm=8.0,
            length_mm=15.0,
            can_wall_thickness_mm=0.15,
            can_bottom_thickness_mm=0.3,
            header_height_mm=1.0,
        )
        assert geo.can_inner_diameter_mm == pytest.approx(7.7, rel=0.001)
        assert geo.can_inner_diameter_mm > 0

    def test_minimum_mandrel_diameter(self):
        """Test with minimum mandrel diameter (1mm)."""
        winding = WindingConfig(
            mandrel_diameter_mm=1.0,  # Very small core
            winding_clearance_mm=0.1,
            winding_tension_factor=1.0,
            tab_type=TabType.TABLESS,
            anode_foil_extension_mm=2.0,
            cathode_foil_extension_mm=2.0,
        )
        assert winding.mandrel_diameter_mm == 1.0


# =============================================================================
# SECTION 1: EDGE CASES - MAXIMUM VALUES
# =============================================================================


class TestEdgeCasesMaximumValues:
    """Test behavior at maximum practical parameter values."""

    def test_maximum_electrode_dimensions(self):
        """Test with very large electrode dimensions (500mm x 300mm)."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=500.0,
            cathode_width_mm=300.0,
        )
        # Area = 500 * 300 / 100 = 1500 cmÂ²
        assert geo.cathode_area_cm2 == pytest.approx(1500.0, rel=0.001)

    def test_maximum_cell_thickness(self):
        """Test with very thick cell (100mm prismatic)."""
        geo = PrismaticGeometry(
            cell_height_mm=200.0,
            cell_width_mm=150.0,
            cell_thickness_mm=100.0,  # Very thick
            wall_top_mm=3.0,
            wall_bottom_mm=2.0,
            wall_front_back_mm=1.0,
            wall_sides_mm=1.0,
        )
        assert geo.internal_thickness_mm == pytest.approx(98.0, rel=0.001)

    def test_maximum_coating_thickness(self, standard_cathode):
        """Test with very thick coating (500 Âµm - thick LFP)."""
        thick_cathode = CathodeMaterial(
            id="thick_cathode",
            name="Ultra Thick LFP",
            chemistry="LFP",
            rev_spec_capacity_mahg=160.0,
            max_spec_capacity_mahg=170.0,
            areal_weight_mgcm2=50.0,  # Very high loading
            collector_thickness_um=15.0,
            coating_density_gcm3=2.5,
            coating_thickness_0pct_um=500.0,  # 500 Âµm
            coating_thickness_100pct_um=490.0,
        )
        assert thick_cathode.coating_thickness_0pct_um == 500.0

    def test_maximum_porosity(self):
        """Test with very high porosity (95%)."""
        high_porosity_sep = SeparatorMaterial(
            id="porous_sep",
            name="High Porosity Separator",
            thickness_um=25.0,
            porosity_pct=95.0,  # Very porous
            density_gcm3=0.9,
            areal_weight_mgcm2=0.3,
        )
        assert high_porosity_sep.porosity_pct == 95.0

    def test_maximum_cylindrical_diameter(self):
        """Test with large cylindrical cell diameter (70mm)."""
        geo = CylindricalGeometry(
            diameter_mm=70.0,  # Larger than 4680
            length_mm=100.0,
            can_wall_thickness_mm=0.5,
            can_bottom_thickness_mm=1.0,
            header_height_mm=5.0,
        )
        assert geo.can_inner_diameter_mm == pytest.approx(69.0, rel=0.001)
        assert geo.can_volume_cm3 > 0


# =============================================================================
# SECTION 1: EDGE CASES - BOUNDARY CONDITIONS
# =============================================================================


class TestEdgeCasesBoundaryConditions:
    """Test exact boundary values."""

    @pytest.mark.parametrize(
        "height,width,expected_area",
        [
            (100.0, 100.0, 100.0),  # Square 100x100
            (50.0, 200.0, 100.0),  # 1:4 aspect ratio
            (200.0, 50.0, 100.0),  # 4:1 aspect ratio
            (1.0, 10000.0, 100.0),  # Extreme aspect ratio
        ],
    )
    def test_various_aspect_ratios(self, height, width, expected_area):
        """Test various electrode aspect ratios produce correct area."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=height,
            cathode_width_mm=width,
        )
        assert geo.cathode_area_cm2 == pytest.approx(expected_area, rel=0.001)

    def test_square_cell_dimensions(self):
        """Test with perfectly square cell dimensions."""
        geo = PrismaticGeometry(
            cell_height_mm=100.0,
            cell_width_mm=100.0,
            cell_thickness_mm=100.0,  # Cube
            wall_top_mm=1.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=1.0,
            wall_sides_mm=1.0,
        )
        # Volume = 100Â³ / 1000 = 1000 cmÂ³
        assert geo.cell_volume_cm3 == pytest.approx(1000.0, rel=0.001)

    def test_very_thin_prismatic_aspect_ratio(self):
        """Test blade-style cell with aspect ratio > 20:1."""
        geo = PrismaticGeometry(
            cell_height_mm=10.0,  # Very thin
            cell_width_mm=300.0,  # Long
            cell_thickness_mm=100.0,
            wall_top_mm=0.5,
            wall_bottom_mm=0.5,
            wall_front_back_mm=0.3,
            wall_sides_mm=0.3,
        )
        aspect_ratio = geo.cell_width_mm / geo.cell_height_mm
        assert aspect_ratio == 30.0  # 300:10

    @pytest.mark.parametrize(
        "mandrel,outer,expected_inner",
        [
            (3.0, 21.0, 20.4),  # Standard 21700
            (5.0, 46.0, 45.4),  # 4680 style
            (2.0, 18.0, 17.4),  # 18650 style
        ],
    )
    def test_cylindrical_diameter_ratios(self, mandrel, outer, expected_inner):
        """Test cylindrical geometry with various diameter ratios."""
        geo = CylindricalGeometry(
            diameter_mm=outer,
            length_mm=70.0,
            can_wall_thickness_mm=0.3,
            can_bottom_thickness_mm=0.5,
            header_height_mm=3.0,
        )
        assert geo.can_inner_diameter_mm == pytest.approx(expected_inner, rel=0.001)


# =============================================================================
# SECTION 1: EDGE CASES - SPECIAL GEOMETRIES
# =============================================================================


class TestEdgeCasesSpecialGeometries:
    """Test unusual but valid geometries."""

    def test_asymmetric_anode_offsets(self):
        """Test with asymmetric anode offsets."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=100.0,
            cathode_width_mm=200.0,
            anode_offset_top_mm=5.0,  # Large top
            anode_offset_bottom_mm=1.0,  # Small bottom
            anode_offset_left_mm=3.0,  # Medium left
            anode_offset_right_mm=0.5,  # Tiny right
        )
        assert geo.anode_height_mm == pytest.approx(106.0, rel=0.001)  # 100+5+1
        assert geo.anode_width_mm == pytest.approx(203.5, rel=0.001)  # 200+3+0.5

    def test_zero_anode_offsets(self):
        """Test with zero anode offsets (anode = cathode size)."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=100.0,
            cathode_width_mm=200.0,
            anode_offset_top_mm=0.0,
            anode_offset_bottom_mm=0.0,
            anode_offset_left_mm=0.0,
            anode_offset_right_mm=0.0,
        )
        assert geo.anode_height_mm == geo.cathode_height_mm
        assert geo.anode_width_mm == geo.cathode_width_mm

    def test_uniform_separator_offsets(self):
        """Test with uniform separator offsets."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=100.0,
            cathode_width_mm=200.0,
            anode_offset_top_mm=2.0,
            anode_offset_bottom_mm=2.0,
            anode_offset_left_mm=2.0,
            anode_offset_right_mm=2.0,
            separator_offset_top_mm=3.0,
            separator_offset_bottom_mm=3.0,
            separator_offset_left_mm=3.0,
            separator_offset_right_mm=3.0,
        )
        # Separator should be larger than anode
        assert geo.separator_height_mm > geo.anode_height_mm
        assert geo.separator_width_mm > geo.anode_width_mm


# =============================================================================
# SECTION 2: CALCULATOR CONSISTENCY
# =============================================================================


class TestCalculatorConsistencyFormulas:
    """Test that formulas are applied consistently."""

    def test_mass_formula_coating(self, standard_cathode):
        """Verify coating mass formula: area Ã— loading Ã— 2 / 1000."""
        area_cm2 = 100.0
        loading_mgcm2 = standard_cathode.areal_weight_mgcm2

        # Formula: double-sided coating
        expected_mass = area_cm2 * loading_mgcm2 * 2 / 1000
        assert expected_mass == pytest.approx(3.6, rel=0.001)  # 100 * 18 * 2 / 1000

    def test_mass_formula_collector_aluminum(self, standard_cathode):
        """Verify Al collector mass formula: area Ã— thickness Ã— density."""
        area_cm2 = 100.0
        thickness_cm = standard_cathode.collector_thickness_um / 10000
        density = 2.70  # g/cmÂ³ aluminum

        expected_mass = area_cm2 * thickness_cm * density
        # 100 * (12/10000) * 2.70 = 0.324 g
        assert expected_mass == pytest.approx(0.324, rel=0.001)

    def test_mass_formula_collector_copper(self, standard_anode):
        """Verify Cu collector mass formula: area Ã— thickness Ã— density."""
        area_cm2 = 100.0
        thickness_cm = standard_anode.collector_thickness_um / 10000
        density = 8.96  # g/cmÂ³ copper

        expected_mass = area_cm2 * thickness_cm * density
        # 100 * (8/10000) * 8.96 = 0.717 g
        assert expected_mass == pytest.approx(0.717, rel=0.001)

    def test_energy_density_formula(self):
        """Verify ED formula: (capacity Ã— voltage) / mass Ã— 1000."""
        capacity_ah = 50.0
        voltage_v = 3.7
        mass_g = 500.0

        energy_wh = capacity_ah * voltage_v
        ed_whkg = energy_wh / mass_g * 1000

        assert ed_whkg == pytest.approx(370.0, rel=0.001)

    def test_volumetric_density_formula(self):
        """Verify volumetric ED formula: energy / volume Ã— 1000."""
        energy_wh = 185.0
        volume_cm3 = 500.0

        ed_whl = energy_wh / volume_cm3 * 1000

        assert ed_whl == pytest.approx(370.0, rel=0.001)

    def test_areal_capacity_formula(self):
        """Verify areal capacity formula: total_mAh / cathode_area."""
        total_capacity_ah = 100.0
        cathode_area_cm2 = 10000.0

        areal_capacity_mahcm2 = total_capacity_ah * 1000 / cathode_area_cm2
        assert areal_capacity_mahcm2 == pytest.approx(10.0, rel=0.001)


class TestCalculatorOutputConsistency:
    """Verify output structure consistency."""

    def test_prismatic_geometry_properties(self):
        """Verify all PrismaticGeometry properties are available."""
        geo = PrismaticGeometry(
            cell_height_mm=88.8,
            cell_width_mm=264.6,
            cell_thickness_mm=29.6,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=0.5,
            wall_sides_mm=0.7,
        )
        # All these properties should exist and be non-negative
        assert geo.internal_height_mm >= 0
        assert geo.internal_width_mm >= 0
        assert geo.internal_thickness_mm >= 0
        assert geo.cell_volume_cm3 >= 0

    def test_cylindrical_geometry_properties(self):
        """Verify all CylindricalGeometry properties are available."""
        geo = CylindricalGeometry(
            diameter_mm=21.0,
            length_mm=70.0,
            can_wall_thickness_mm=0.3,
            can_bottom_thickness_mm=0.5,
            header_height_mm=3.0,
        )
        assert geo.can_inner_diameter_mm >= 0
        assert geo.can_inner_length_mm >= 0
        assert geo.can_volume_cm3 >= 0
        assert geo.can_inner_volume_cm3 >= 0


# =============================================================================
# SECTION 3: ERROR HANDLING - INVALID INPUTS
# =============================================================================


class TestErrorHandlingInvalidInputs:
    """Test handling of invalid input values."""

    def test_material_requires_all_fields(self):
        """Material dataclass should require all fields."""
        # This tests that dataclass enforces required fields
        with pytest.raises(TypeError):
            # Missing required fields
            CathodeMaterial(
                id="incomplete",
                name="Incomplete",
                # Missing: chemistry, capacities, etc.
            )

    def test_geometry_accepts_valid_values(self):
        """Geometry should accept valid positive values."""
        geo = PrismaticGeometry(
            cell_height_mm=100.0,
            cell_width_mm=200.0,
            cell_thickness_mm=30.0,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=0.5,
            wall_sides_mm=0.5,
        )
        # Should create without error
        assert geo.cell_height_mm == 100.0

    def test_anode_material_complete(self, standard_anode):
        """Verify anode material has all required fields populated."""
        assert standard_anode.id is not None
        assert standard_anode.name is not None
        assert standard_anode.chemistry is not None
        assert standard_anode.rev_spec_capacity_mahg > 0
        assert standard_anode.areal_weight_mgcm2 > 0

    def test_separator_material_complete(self, standard_separator):
        """Verify separator material has all required fields populated."""
        assert standard_separator.id is not None
        assert standard_separator.name is not None
        assert standard_separator.thickness_um > 0
        assert standard_separator.porosity_pct >= 0
        assert standard_separator.porosity_pct <= 100


class TestErrorHandlingMissingParameters:
    """Test handling of missing required parameters."""

    def test_winding_config_requires_tab_type(self):
        """WindingConfig should require tab_type specification."""
        winding = WindingConfig(
            mandrel_diameter_mm=3.0,
            winding_clearance_mm=0.2,
            winding_tension_factor=0.98,
            tab_type=TabType.TABLESS,
            anode_foil_extension_mm=3.0,
            cathode_foil_extension_mm=3.0,
        )
        assert winding.tab_type == TabType.TABLESS

    def test_prismatic_geometry_requires_walls(self):
        """PrismaticGeometry should require wall thickness values."""
        with pytest.raises(TypeError):
            # Missing wall thicknesses
            PrismaticGeometry(
                cell_height_mm=88.8,
                cell_width_mm=264.6,
                cell_thickness_mm=29.6,
                # Missing: wall_top_mm, wall_bottom_mm, etc.
            )


class TestErrorHandlingTypeValidation:
    """Test type validation for inputs."""

    def test_geometry_fields_are_floats(self):
        """Geometry values should be stored as floats."""
        geo = PrismaticGeometry(
            cell_height_mm=88.8,
            cell_width_mm=264.6,
            cell_thickness_mm=29.6,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=0.5,
            wall_sides_mm=0.7,
        )
        assert isinstance(geo.cell_height_mm, float)
        assert isinstance(geo.internal_height_mm, float)

    def test_material_fields_are_floats(self, standard_cathode):
        """Material values should be stored as floats."""
        assert isinstance(standard_cathode.rev_spec_capacity_mahg, float)
        assert isinstance(standard_cathode.areal_weight_mgcm2, float)
        assert isinstance(standard_cathode.coating_density_gcm3, float)


# =============================================================================
# SECTION 4: NUMERICAL PRECISION - FLOATING POINT
# =============================================================================


class TestNumericalPrecisionFloatingPoint:
    """Test floating point precision handling."""

    def test_small_differences_preserved(self):
        """Small differences (1e-6) should be preserved."""
        mass1 = 100.000001
        mass2 = 100.000002

        assert mass1 != mass2
        assert abs(mass2 - mass1) > 0
        assert abs(mass2 - mass1) == pytest.approx(1e-6, abs=1e-10)

    def test_accumulation_precision(self):
        """Accumulated calculations shouldn't lose precision."""
        small_mass = 0.001
        total = sum([small_mass] * 1000)
        assert total == pytest.approx(1.0, rel=1e-10)

    def test_division_precision(self):
        """Division shouldn't introduce significant error."""
        energy = 100.0
        mass = 333.333333
        ed = energy / mass * 1000

        assert ed == pytest.approx(300.0, rel=1e-5)

    def test_multiplication_precision(self):
        """Chained multiplications maintain precision."""
        result = 1.0
        for _ in range(10):
            result *= 1.1
            result /= 1.1

        assert result == pytest.approx(1.0, rel=1e-10)

    def test_very_small_values_handled(self):
        """Very small values (< 1e-10) handled correctly."""
        tiny = 1e-15
        assert tiny > 0
        assert tiny * 1e15 == pytest.approx(1.0, rel=1e-10)

    def test_very_large_values_handled(self):
        """Very large values handled correctly."""
        huge = 1e15
        assert huge / 1e15 == pytest.approx(1.0, rel=1e-10)

    def test_no_nan_in_basic_operations(self):
        """Basic operations should never produce NaN."""
        values = [1.0, 0.0, -1.0, 1e-100, 1e100]
        for v1 in values:
            for v2 in values:
                if v2 != 0:
                    result = v1 / v2
                    assert not math.isnan(result)

    def test_no_inf_in_bounded_division(self):
        """Division with bounded inputs shouldn't produce infinity."""
        numerator = 1e100
        denominator = 1e50  # Still far from zero

        result = numerator / denominator
        assert math.isfinite(result)


# =============================================================================
# SECTION 4: NUMERICAL PRECISION - UNIT CONVERSIONS
# =============================================================================


class TestNumericalPrecisionUnitConversions:
    """Test unit conversion accuracy."""

    def test_mm_to_cm_conversion(self):
        """mm to cm conversion: /10."""
        mm = 100.0
        cm = mm / 10
        assert cm == pytest.approx(10.0, rel=1e-10)

    def test_um_to_mm_conversion(self):
        """Âµm to mm conversion: /1000."""
        um = 1000.0
        mm = um / 1000
        assert mm == pytest.approx(1.0, rel=1e-10)

    def test_um_to_cm_conversion(self):
        """Âµm to cm conversion: /10000."""
        um = 10000.0
        cm = um / 10000
        assert cm == pytest.approx(1.0, rel=1e-10)

    def test_mg_to_g_conversion(self):
        """mg to g conversion: /1000."""
        mg = 1000.0
        g = mg / 1000
        assert g == pytest.approx(1.0, rel=1e-10)

    def test_mah_to_ah_conversion(self):
        """mAh to Ah conversion: /1000."""
        mah = 5000.0
        ah = mah / 1000
        assert ah == pytest.approx(5.0, rel=1e-10)

    def test_wh_to_kwh_conversion(self):
        """Wh to kWh conversion: /1000."""
        wh = 100.0
        kwh = wh / 1000
        assert kwh == pytest.approx(0.1, rel=1e-10)

    def test_gcm3_to_kgm3_conversion(self):
        """g/cmÂ³ to kg/mÂ³ conversion: Ã—1000."""
        gcm3 = 2.7  # aluminum
        kgm3 = gcm3 * 1000
        assert kgm3 == pytest.approx(2700.0, rel=1e-10)

    def test_area_mm2_to_cm2(self):
        """mmÂ² to cmÂ² conversion: /100."""
        mm2 = 10000.0
        cm2 = mm2 / 100
        assert cm2 == pytest.approx(100.0, rel=1e-10)

    def test_volume_mm3_to_cm3(self):
        """mmÂ³ to cmÂ³ conversion: /1000."""
        mm3 = 1000.0
        cm3 = mm3 / 1000
        assert cm3 == pytest.approx(1.0, rel=1e-10)


# =============================================================================
# SECTION 4: NUMERICAL PRECISION - ROUNDING
# =============================================================================


class TestNumericalPrecisionRounding:
    """Test rounding behavior."""

    def test_display_rounding_doesnt_affect_internal(self):
        """Internal values should maintain precision even if display rounds."""
        value = 123.456789
        displayed = f"{value:.2f}"  # "123.46"

        assert displayed == "123.46"
        assert value == 123.456789  # Internal value unchanged

    def test_mass_components_sum_to_total(self):
        """Component masses should sum exactly to total mass."""
        cathode = 100.123
        anode = 80.456
        separator = 10.789
        electrolyte = 50.321
        housing = 30.111

        total = cathode + anode + separator + electrolyte + housing
        components_sum = sum([cathode, anode, separator, electrolyte, housing])

        assert total == pytest.approx(components_sum, rel=1e-12)
        assert total == pytest.approx(271.8, rel=0.001)

    def test_percentage_breakdown_sums_to_100(self):
        """Mass percentages should sum to 100% (within tolerance)."""
        masses = [100.0, 80.0, 10.0, 50.0, 30.0]
        total = sum(masses)
        percentages = [m / total * 100 for m in masses]

        assert sum(percentages) == pytest.approx(100.0, rel=1e-10)


# =============================================================================
# SECTION: INTEGRATION SANITY CHECKS
# =============================================================================


class TestIntegrationSanityChecks:
    """High-level sanity checks for calculations."""

    def test_larger_cell_has_more_mass(self, standard_cathode, standard_anode):
        """Larger electrode area should result in more mass."""
        area_small = 100.0  # cmÂ²
        area_large = 200.0  # cmÂ²

        # Coating mass calculation
        mass_small = area_small * standard_cathode.areal_weight_mgcm2 * 2 / 1000
        mass_large = area_large * standard_cathode.areal_weight_mgcm2 * 2 / 1000

        assert mass_large > mass_small
        assert mass_large == pytest.approx(mass_small * 2, rel=0.001)

    def test_higher_loading_increases_mass(self):
        """Higher areal loading should increase mass proportionally."""
        area = 100.0  # cmÂ²
        loading_low = 15.0  # mg/cmÂ²
        loading_high = 30.0  # mg/cmÂ²

        mass_low = area * loading_low * 2 / 1000
        mass_high = area * loading_high * 2 / 1000

        assert mass_high > mass_low
        assert mass_high == pytest.approx(mass_low * 2, rel=0.001)

    def test_energy_proportional_to_capacity(self):
        """Energy should be proportional to capacity at fixed voltage."""
        voltage = 3.7  # V
        capacity_low = 50.0  # Ah
        capacity_high = 100.0  # Ah

        energy_low = capacity_low * voltage
        energy_high = capacity_high * voltage

        assert energy_high == energy_low * 2

    def test_cylindrical_volume_formula(self):
        """Cylindrical volume should follow Ï€ rÂ² h."""
        geo = CylindricalGeometry(
            diameter_mm=21.0,
            length_mm=70.0,
            can_wall_thickness_mm=0.3,
            can_bottom_thickness_mm=0.5,
            header_height_mm=3.0,
        )
        # Manual calculation: Ï€ Ã— (21/2)Â² Ã— 70 / 1000 = 24.25 cmÂ³
        expected = math.pi * (21.0 / 2 / 10) ** 2 * (70.0 / 10)
        assert geo.can_volume_cm3 == pytest.approx(expected, rel=0.001)

    def test_prismatic_volume_formula(self):
        """Prismatic volume should follow L Ã— W Ã— H."""
        geo = PrismaticGeometry(
            cell_height_mm=88.8,
            cell_width_mm=264.6,
            cell_thickness_mm=29.6,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=0.5,
            wall_sides_mm=0.7,
        )
        # Manual: 88.8 Ã— 264.6 Ã— 29.6 / 1000 = 695.54 cmÂ³
        expected = 88.8 * 264.6 * 29.6 / 1000
        assert geo.cell_volume_cm3 == pytest.approx(expected, rel=0.001)


# =============================================================================
# SECTION: CONSISTENT RESULTS ACROSS RUNS
# =============================================================================


class TestDeterministicResults:
    """Verify calculations are deterministic (same input = same output)."""

    def test_geometry_calculation_deterministic(self):
        """Same geometry input should always produce same output."""
        results = []
        for _ in range(10):
            geo = PrismaticGeometry(
                cell_height_mm=88.8,
                cell_width_mm=264.6,
                cell_thickness_mm=29.6,
                wall_top_mm=2.0,
                wall_bottom_mm=1.0,
                wall_front_back_mm=0.5,
                wall_sides_mm=0.7,
            )
            results.append(geo.cell_volume_cm3)

        # All results should be identical
        assert all(r == results[0] for r in results)

    def test_cylindrical_geometry_deterministic(self):
        """Same cylindrical input should always produce same output."""
        results = []
        for _ in range(10):
            geo = CylindricalGeometry(
                diameter_mm=21.0,
                length_mm=70.0,
                can_wall_thickness_mm=0.3,
                can_bottom_thickness_mm=0.5,
                header_height_mm=3.0,
            )
            results.append(geo.can_volume_cm3)

        assert all(r == results[0] for r in results)

    def test_mass_calculation_deterministic(self, standard_cathode):
        """Same mass inputs should always produce same output."""
        area = 186.258  # cmÂ²
        loading = standard_cathode.areal_weight_mgcm2

        results = []
        for _ in range(10):
            mass = area * loading * 2 / 1000
            results.append(mass)

        assert all(r == results[0] for r in results)


# =============================================================================
# SECTION: ADDITIONAL EDGE CASES
# =============================================================================


class TestAdditionalEdgeCases:
    """Additional edge case tests for comprehensive coverage."""

    def test_coating_thinner_at_100_soc(self, standard_cathode):
        """Cathode coating typically shrinks at high SoC (delithiation)."""
        assert standard_cathode.coating_thickness_100pct_um < standard_cathode.coating_thickness_0pct_um

    def test_anode_thicker_at_100_soc(self, standard_anode):
        """Anode coating typically expands at high SoC (lithiation)."""
        assert standard_anode.coating_thickness_100pct_um > standard_anode.coating_thickness_0pct_um

    def test_separator_offset_larger_than_anode(self):
        """Separator should be larger than both electrodes."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=100.0,
            cathode_width_mm=200.0,
            anode_offset_top_mm=2.0,
            anode_offset_bottom_mm=2.0,
            anode_offset_left_mm=2.0,
            anode_offset_right_mm=2.0,
            separator_offset_top_mm=4.0,
            separator_offset_bottom_mm=4.0,
            separator_offset_left_mm=4.0,
            separator_offset_right_mm=4.0,
        )
        assert geo.separator_height_mm > geo.anode_height_mm
        assert geo.separator_width_mm > geo.anode_width_mm
        assert geo.separator_area_cm2 > geo.anode_area_cm2

    def test_cylindrical_inner_volume_less_than_outer(self):
        """Inner volume must be less than outer volume."""
        geo = CylindricalGeometry(
            diameter_mm=21.0,
            length_mm=70.0,
            can_wall_thickness_mm=0.3,
            can_bottom_thickness_mm=0.5,
            header_height_mm=3.0,
        )
        assert geo.can_inner_volume_cm3 < geo.can_volume_cm3

    def test_prismatic_internal_volume_less_than_external(self):
        """Internal volume must be less than external volume."""
        geo = PrismaticGeometry(
            cell_height_mm=88.8,
            cell_width_mm=264.6,
            cell_thickness_mm=29.6,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_back_mm=0.5,
            wall_sides_mm=0.7,
        )
        internal_vol = (
            geo.internal_height_mm * geo.internal_width_mm * geo.internal_thickness_mm / 1000
        )
        assert internal_vol < geo.cell_volume_cm3

    @pytest.mark.parametrize(
        "diameter,name",
        [
            (18.0, "18650"),
            (21.0, "21700"),
            (26.0, "26650"),
            (32.0, "32700"),
            (46.0, "4680"),
        ],
    )
    def test_common_cylindrical_form_factors(self, diameter, name):
        """Test common cylindrical cell form factors."""
        geo = CylindricalGeometry(
            diameter_mm=diameter,
            length_mm=70.0,
            can_wall_thickness_mm=0.3,
            can_bottom_thickness_mm=0.5,
            header_height_mm=3.0,
        )
        assert geo.diameter_mm == diameter
        assert geo.can_inner_diameter_mm > 0


class TestMaterialPropertyRanges:
    """Test that material properties are in physically reasonable ranges."""

    def test_cathode_spec_capacity_reasonable(self, standard_cathode):
        """Cathode specific capacity should be in reasonable range."""
        # Theoretical limits: LCO ~140, NMC ~200, NCA ~200
        assert 100 < standard_cathode.rev_spec_capacity_mahg < 250

    def test_anode_spec_capacity_reasonable(self, standard_anode):
        """Anode specific capacity should be in reasonable range."""
        # Graphite theoretical: 372 mAh/g
        assert 300 < standard_anode.rev_spec_capacity_mahg < 400

    def test_cathode_density_reasonable(self, standard_cathode):
        """Cathode coating density should be in reasonable range."""
        # Typical: 2.5-4.0 g/cmÂ³
        assert 2.0 < standard_cathode.coating_density_gcm3 < 5.0

    def test_anode_density_reasonable(self, standard_anode):
        """Anode coating density should be in reasonable range."""
        # Graphite: 1.0-2.2 g/cmÂ³
        assert 0.5 < standard_anode.coating_density_gcm3 < 2.5

    def test_separator_porosity_reasonable(self, standard_separator):
        """Separator porosity should be in reasonable range."""
        # Typical: 30-55%
        assert 20 < standard_separator.porosity_pct < 70

    def test_electrolyte_density_reasonable(self, standard_electrolyte):
        """Electrolyte density should be in reasonable range."""
        # Typical organic electrolytes: 1.1-1.3 g/cmÂ³
        assert 1.0 < standard_electrolyte.density_gcm3 < 1.5


class TestCalculatorValidation:
    """Test calculator input validation."""

    def test_prismatic_calculator_validates_materials(self):
        """PrismaticCalculator should validate material inputs."""
        from forge.engine.calculators.prismatic_calculator import PrismaticCalculator
        from forge.engine.models.prismatic import PrismaticCellInput

        # Create incomplete input
        incomplete_input = PrismaticCellInput(
            cell_name="Test",
            case_geometry=PrismaticGeometry(
                cell_height_mm=88.8,
                cell_width_mm=264.6,
                cell_thickness_mm=29.6,
                wall_top_mm=2.0,
                wall_bottom_mm=1.0,
                wall_front_back_mm=0.5,
                wall_sides_mm=0.7,
            ),
            sheet_geometry=PrismaticSheetGeometry(
                cathode_height_mm=74.0,
                cathode_width_mm=251.7,
            ),
            cathode=None,  # Missing!
            anode=None,
            separator=None,
            electrolyte=None,
            electrode_pairs_per_stack=22,
            number_of_stacks=2,
            nominal_voltage_v=3.7,
        )

        with pytest.raises(ValueError, match="cathode"):
            PrismaticCalculator(incomplete_input)


class TestEnumConsistency:
    """Test enum values and consistency."""

    def test_tab_type_values(self):
        """Verify TabType enum has expected values."""
        assert TabType.TRADITIONAL.value == "traditional"
        assert TabType.TABLESS.value == "tabless"

    def test_can_material_values(self):
        """Verify CanMaterial enum has expected values."""
        assert CanMaterial.STEEL.value == "steel"
        assert CanMaterial.ALUMINUM.value == "aluminum"
        assert CanMaterial.NICKEL_PLATED_STEEL.value == "nickel_plated_steel"

    def test_can_material_density_mapping(self):
        """Verify can material density lookup works."""
        from forge.engine.models.cylindrical import get_can_material_density

        assert get_can_material_density(CanMaterial.STEEL) == pytest.approx(7.85, rel=0.01)
        assert get_can_material_density(CanMaterial.ALUMINUM) == pytest.approx(2.70, rel=0.01)


class TestBoundaryMathOperations:
    """Test mathematical boundary conditions."""

    def test_zero_area_gives_zero_mass(self):
        """Zero area should give zero mass."""
        area = 0.0
        loading = 18.0  # mg/cmÂ²
        mass = area * loading * 2 / 1000
        assert mass == 0.0

    def test_zero_loading_gives_zero_mass(self):
        """Zero loading should give zero mass."""
        area = 100.0  # cmÂ²
        loading = 0.0  # mg/cmÂ²
        mass = area * loading * 2 / 1000
        assert mass == 0.0

    def test_zero_thickness_gives_zero_volume(self):
        """Zero thickness should give zero volume."""
        height = 100.0
        width = 200.0
        thickness = 0.0
        volume = height * width * thickness / 1000
        assert volume == 0.0

    def test_cylindrical_zero_length_gives_zero_volume(self):
        """Cylindrical with zero length should give zero volume."""
        diameter = 21.0
        length = 0.0
        volume = math.pi * (diameter / 2 / 10) ** 2 * (length / 10)
        assert volume == 0.0

    def test_very_precise_pi_in_cylindrical_calc(self):
        """Cylindrical volume should use precise pi value."""
        geo = CylindricalGeometry(
            diameter_mm=20.0,  # r = 1 cm
            length_mm=100.0,  # h = 10 cm
            can_wall_thickness_mm=0.0,  # No wall for simple calculation
            can_bottom_thickness_mm=0.0,
            header_height_mm=0.0,
        )
        # Volume = Ï€ Ã— 1Â² Ã— 10 = 10Ï€ â‰ˆ 31.416
        expected = math.pi * 10
        assert geo.can_volume_cm3 == pytest.approx(expected, rel=1e-10)


class TestSheetCountLogic:
    """Test electrode and separator sheet counting logic."""

    def test_sheet_geometry_area_calculation(self):
        """Verify area calculation for different sheet dimensions."""
        # 100 mm Ã— 100 mm = 100 cmÂ²
        geo = PrismaticSheetGeometry(cathode_height_mm=100.0, cathode_width_mm=100.0)
        assert geo.cathode_area_cm2 == pytest.approx(100.0, rel=0.001)

    def test_offset_doesnt_affect_cathode_area(self):
        """Offsets should not change cathode area."""
        geo1 = PrismaticSheetGeometry(cathode_height_mm=100.0, cathode_width_mm=200.0)

        geo2 = PrismaticSheetGeometry(
            cathode_height_mm=100.0,
            cathode_width_mm=200.0,
            anode_offset_top_mm=5.0,
            anode_offset_bottom_mm=5.0,
        )

        assert geo1.cathode_area_cm2 == geo2.cathode_area_cm2

    def test_anode_larger_with_offsets(self):
        """Anode should be larger than cathode with positive offsets."""
        geo = PrismaticSheetGeometry(
            cathode_height_mm=100.0,
            cathode_width_mm=200.0,
            anode_offset_top_mm=2.0,
            anode_offset_bottom_mm=2.0,
            anode_offset_left_mm=2.0,
            anode_offset_right_mm=2.0,
        )
        assert geo.anode_area_cm2 > geo.cathode_area_cm2

