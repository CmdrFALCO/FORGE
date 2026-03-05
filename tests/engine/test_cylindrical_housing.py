"""Tests for cylindrical housing calculations.

This module tests the housing mass calculations for cylindrical cells.
"""

import pytest

from forge.engine.calculations.cylindrical_housing import (
    calculate_can_body_mass,
    calculate_can_bottom_mass,
    calculate_cylindrical_housing_mass,
    calculate_tab_or_foil_mass,
    calculate_tabless_foil_extension_mass,
    calculate_traditional_tab_mass,
    create_typical_4680_header,
    create_typical_21700_header,
    estimate_4680_header_mass,
    estimate_18650_header_mass,
    estimate_21700_header_mass,
)
from forge.engine.models.cylindrical import (
    DENSITY_ALUMINUM,
    DENSITY_COPPER,
    CanMaterial,
    SimplifiedHeader,
    TabType,
    WindingConfig,
    create_4680_geometry,
    create_21700_geometry,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def geometry_21700():
    """21700 geometry fixture."""
    return create_21700_geometry()


@pytest.fixture
def geometry_4680():
    """4680 geometry fixture."""
    return create_4680_geometry()


@pytest.fixture
def traditional_winding():
    """Traditional winding fixture."""
    return WindingConfig(
        mandrel_diameter_mm=2.5,
        winding_clearance_mm=0.1,
        winding_tension_factor=0.97,
        tab_type=TabType.TRADITIONAL,
        anode_tab_width_mm=6.0,
        anode_tab_thickness_mm=0.1,
        cathode_tab_width_mm=5.0,
        cathode_tab_thickness_mm=0.1,
    )


@pytest.fixture
def tabless_winding():
    """Tabless winding fixture."""
    return WindingConfig(
        mandrel_diameter_mm=4.5,
        winding_clearance_mm=0.15,
        winding_tension_factor=0.96,
        tab_type=TabType.TABLESS,
        anode_foil_extension_mm=3.5,
        cathode_foil_extension_mm=3.5,
    )


@pytest.fixture
def simplified_header():
    """Simplified header fixture."""
    return SimplifiedHeader(total_mass_g=2.0, cap_material=CanMaterial.STEEL)


@pytest.fixture
def detailed_header():
    """Detailed header fixture."""
    return create_typical_21700_header()


# =============================================================================
# Can Body Mass Tests
# =============================================================================


class TestCanBodyMass:
    """Tests for can body mass calculation."""

    def test_steel_can_body_positive(self):
        """Test steel can body mass is positive."""
        mass = calculate_can_body_mass(
            outer_diameter_mm=21.0,
            body_length_mm=69.0,  # 70 - 1mm bottom
            wall_thickness_mm=0.25,
            material=CanMaterial.STEEL,
        )
        assert mass > 0

    def test_aluminum_lighter_than_steel(self):
        """Test aluminum can is lighter than steel."""
        steel_mass = calculate_can_body_mass(21.0, 69.0, 0.25, CanMaterial.STEEL)
        aluminum_mass = calculate_can_body_mass(21.0, 69.0, 0.25, CanMaterial.ALUMINUM)

        assert aluminum_mass < steel_mass

    def test_thicker_wall_more_mass(self):
        """Test thicker wall gives more mass."""
        thin_wall = calculate_can_body_mass(21.0, 69.0, 0.20, CanMaterial.STEEL)
        thick_wall = calculate_can_body_mass(21.0, 69.0, 0.30, CanMaterial.STEEL)

        assert thick_wall > thin_wall

    def test_larger_diameter_more_mass(self):
        """Test larger diameter gives more mass."""
        small = calculate_can_body_mass(21.0, 69.0, 0.25, CanMaterial.STEEL)
        large = calculate_can_body_mass(46.0, 79.0, 0.35, CanMaterial.STEEL)

        assert large > small

    def test_reasonable_21700_body_mass(self):
        """Test 21700 can body mass is in reasonable range."""
        # 21700 can body typically 6-10g for steel
        mass = calculate_can_body_mass(
            outer_diameter_mm=21.0,
            body_length_mm=69.6,  # 70 - 0.4mm bottom
            wall_thickness_mm=0.25,
            material=CanMaterial.NICKEL_PLATED_STEEL,
        )

        assert 5.0 <= mass <= 12.0


# =============================================================================
# Can Bottom Mass Tests
# =============================================================================


class TestCanBottomMass:
    """Tests for can bottom mass calculation."""

    def test_bottom_mass_positive(self):
        """Test can bottom mass is positive."""
        mass = calculate_can_bottom_mass(
            diameter_mm=21.0, thickness_mm=0.4, material=CanMaterial.STEEL
        )
        assert mass > 0

    def test_thicker_bottom_more_mass(self):
        """Test thicker bottom gives more mass."""
        thin = calculate_can_bottom_mass(21.0, 0.3, CanMaterial.STEEL)
        thick = calculate_can_bottom_mass(21.0, 0.5, CanMaterial.STEEL)

        assert thick > thin

    def test_bottom_much_less_than_body(self, geometry_21700):
        """Test bottom mass is much less than body mass."""
        body_mass = calculate_can_body_mass(
            geometry_21700.diameter_mm,
            geometry_21700.length_mm - geometry_21700.can_bottom_thickness_mm,
            geometry_21700.can_wall_thickness_mm,
            CanMaterial.STEEL,
        )

        bottom_mass = calculate_can_bottom_mass(
            geometry_21700.diameter_mm, geometry_21700.can_bottom_thickness_mm, CanMaterial.STEEL
        )

        # Bottom should be ~10-20% of body mass
        assert bottom_mass < body_mass * 0.3


# =============================================================================
# Tab Mass Tests
# =============================================================================


class TestTraditionalTabMass:
    """Tests for traditional tab mass calculation."""

    def test_tab_mass_positive(self):
        """Test tab mass is positive."""
        mass = calculate_traditional_tab_mass(
            tab_width_mm=6.0,
            tab_thickness_mm=0.1,
            electrode_width_mm=60.0,
            num_tabs=1,
            material_density_gcm3=DENSITY_COPPER,
        )
        assert mass > 0

    def test_more_tabs_more_mass(self):
        """Test more tabs gives more mass."""
        one_tab = calculate_traditional_tab_mass(6.0, 0.1, 60.0, 1, DENSITY_COPPER)
        two_tabs = calculate_traditional_tab_mass(6.0, 0.1, 60.0, 2, DENSITY_COPPER)

        assert abs(two_tabs - 2 * one_tab) < 0.001

    def test_copper_heavier_than_aluminum(self):
        """Test copper tab is heavier than aluminum."""
        copper = calculate_traditional_tab_mass(6.0, 0.1, 60.0, 1, DENSITY_COPPER)
        aluminum = calculate_traditional_tab_mass(6.0, 0.1, 60.0, 1, DENSITY_ALUMINUM)

        assert copper > aluminum


# =============================================================================
# Tabless Foil Extension Tests
# =============================================================================


class TestTablessFoilMass:
    """Tests for tabless foil extension mass calculation."""

    def test_foil_extension_mass_positive(self):
        """Test foil extension mass is positive."""
        mass = calculate_tabless_foil_extension_mass(
            foil_extension_mm=3.5,
            electrode_length_m=1.0,
            collector_thickness_um=10.0,
            material_density_gcm3=DENSITY_COPPER,
        )
        assert mass > 0

    def test_longer_electrode_more_mass(self):
        """Test longer electrode gives more foil mass."""
        short = calculate_tabless_foil_extension_mass(3.5, 1.0, 10.0, DENSITY_COPPER)
        long = calculate_tabless_foil_extension_mass(3.5, 2.0, 10.0, DENSITY_COPPER)

        assert abs(long - 2 * short) < 0.001

    def test_wider_extension_more_mass(self):
        """Test wider extension gives more mass."""
        narrow = calculate_tabless_foil_extension_mass(2.0, 1.0, 10.0, DENSITY_COPPER)
        wide = calculate_tabless_foil_extension_mass(4.0, 1.0, 10.0, DENSITY_COPPER)

        assert wide > narrow


# =============================================================================
# Tab/Foil Mass Combined Tests
# =============================================================================


class TestTabOrFoilMass:
    """Tests for combined tab/foil mass calculation."""

    def test_traditional_uses_tabs(self, traditional_winding):
        """Test traditional winding calculates tab mass."""
        mass = calculate_tab_or_foil_mass(
            winding=traditional_winding,
            electrode_length_m=1.0,
            electrode_width_mm=60.0,
            anode_collector_thickness_um=10.0,
            cathode_collector_thickness_um=12.0,
        )
        assert mass > 0

    def test_tabless_uses_foil(self, tabless_winding):
        """Test tabless winding calculates foil extension mass."""
        mass = calculate_tab_or_foil_mass(
            winding=tabless_winding,
            electrode_length_m=1.0,
            electrode_width_mm=70.0,
            anode_collector_thickness_um=10.0,
            cathode_collector_thickness_um=12.0,
        )
        assert mass > 0


# =============================================================================
# Housing Mass Tests
# =============================================================================


class TestCylindricalHousingMass:
    """Tests for complete housing mass calculation."""

    def test_housing_result_properties(self, geometry_21700, simplified_header):
        """Test housing result has correct properties."""
        result = calculate_cylindrical_housing_mass(
            geometry=geometry_21700,
            can_material=CanMaterial.STEEL,
            header_simplified=simplified_header,
        )

        assert result.can_body_g > 0
        assert result.can_bottom_g > 0
        assert result.header_total_g == 2.0
        assert result.total_housing_g > 0

    def test_can_total_is_body_plus_bottom(self, geometry_21700, simplified_header):
        """Test can total equals body + bottom."""
        result = calculate_cylindrical_housing_mass(
            geometry=geometry_21700,
            can_material=CanMaterial.STEEL,
            header_simplified=simplified_header,
        )

        expected = result.can_body_g + result.can_bottom_g
        assert abs(result.can_total_g - expected) < 0.001

    def test_total_housing_includes_all(self, geometry_21700, simplified_header):
        """Test total housing includes all components."""
        result = calculate_cylindrical_housing_mass(
            geometry=geometry_21700,
            can_material=CanMaterial.STEEL,
            header_simplified=simplified_header,
            bottom_insulator_mass_g=0.1,
            top_insulator_mass_g=0.1,
            tabs_mass_g=0.5,
        )

        expected = (
            result.can_body_g
            + result.can_bottom_g
            + result.header_total_g
            + result.bottom_insulator_g
            + result.top_insulator_g
            + result.tabs_g
        )

        assert abs(result.total_housing_g - expected) < 0.001

    def test_detailed_header_used(self, geometry_21700, detailed_header):
        """Test detailed header mass is used."""
        result = calculate_cylindrical_housing_mass(
            geometry=geometry_21700,
            can_material=CanMaterial.STEEL,
            header=detailed_header,
        )

        # Should use detailed header's total
        assert result.header_total_g == detailed_header.total_header_mass_g

    def test_21700_reasonable_housing_mass(self, geometry_21700, simplified_header):
        """Test 21700 housing mass is in reasonable range."""
        result = calculate_cylindrical_housing_mass(
            geometry=geometry_21700,
            can_material=CanMaterial.NICKEL_PLATED_STEEL,
            header_simplified=simplified_header,
            bottom_insulator_mass_g=0.1,
            top_insulator_mass_g=0.1,
        )

        # 21700 housing typically 8-12g total
        assert 5.0 <= result.total_housing_g <= 15.0

    def test_4680_more_than_21700(self, geometry_21700, geometry_4680):
        """Test 4680 housing mass is more than 21700."""
        header_21700 = SimplifiedHeader(total_mass_g=2.0, cap_material=CanMaterial.STEEL)
        header_4680 = SimplifiedHeader(total_mass_g=9.0, cap_material=CanMaterial.STEEL)

        result_21700 = calculate_cylindrical_housing_mass(
            geometry_21700, CanMaterial.STEEL, header_simplified=header_21700
        )

        result_4680 = calculate_cylindrical_housing_mass(
            geometry_4680, CanMaterial.STEEL, header_simplified=header_4680
        )

        assert result_4680.total_housing_g > result_21700.total_housing_g * 2


# =============================================================================
# Header Estimation Tests
# =============================================================================


class TestHeaderEstimation:
    """Tests for header mass estimation functions."""

    def test_21700_header_estimate_positive(self):
        """Test 21700 header estimate is positive."""
        mass = estimate_21700_header_mass()
        assert mass > 0

    def test_4680_header_more_than_21700(self):
        """Test 4680 header is heavier than 21700."""
        mass_21700 = estimate_21700_header_mass()
        mass_4680 = estimate_4680_header_mass()

        assert mass_4680 > mass_21700

    def test_18650_header_less_than_21700(self):
        """Test 18650 header is lighter than 21700."""
        mass_18650 = estimate_18650_header_mass()
        mass_21700 = estimate_21700_header_mass()

        assert mass_18650 < mass_21700

    def test_aluminum_cap_lighter(self):
        """Test aluminum cap gives lighter header."""
        steel = estimate_21700_header_mass(CanMaterial.STEEL)
        aluminum = estimate_21700_header_mass(CanMaterial.ALUMINUM)

        assert aluminum < steel


# =============================================================================
# Header Components Tests
# =============================================================================


class TestHeaderComponents:
    """Tests for detailed header components."""

    def test_21700_header_components(self):
        """Test 21700 header has valid components."""
        header = create_typical_21700_header()

        assert header.ptc_mass_g > 0
        assert header.cid_mass_g > 0
        assert header.vent_mass_g > 0
        assert header.gasket_mass_g > 0

    def test_4680_header_components(self):
        """Test 4680 header has valid components."""
        header = create_typical_4680_header()

        assert header.ptc_mass_g > 0
        assert header.cid_mass_g > 0
        assert header.cap_diameter_mm == 46.0

    def test_header_total_mass(self):
        """Test header total mass calculation."""
        header = create_typical_21700_header()

        # Total should include all components + calculated cap
        assert header.total_header_mass_g > 0
        assert header.total_header_mass_g > header.cap_mass_g

    def test_cap_mass_calculated(self):
        """Test cap mass is calculated from geometry."""
        header = create_typical_21700_header()

        # Cap mass should be positive and reasonable
        assert 0.5 <= header.cap_mass_g <= 3.0
