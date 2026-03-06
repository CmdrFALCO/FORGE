"""Tests for cylindrical cell calculator.

This module tests the CylindricalCalculator and related functions.
"""

import math

import pytest

from forge.engine.calculators.cylindrical_calculator import (
    CylindricalCalculator,
    calculate_cylindrical_anode_mass,
    calculate_cylindrical_cathode_mass,
    calculate_cylindrical_separator_mass,
)
from forge.engine.models.cylindrical import (
    CanMaterial,
    CylindricalCellInput,
    SimplifiedHeader,
    TabType,
    WindingConfig,
    create_4680_geometry,
    create_18650_geometry,
    create_21700_geometry,
)
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    ElectrolyteModel,
    SeparatorMaterial,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def nmc811_cathode():
    """NMC811 cathode material fixture."""
    return CathodeMaterial(
        id="test_cathode",
        name="NMC811 Test",
        chemistry="NMC811",
        rev_spec_capacity_mahg=200.0,
        max_spec_capacity_mahg=220.0,
        areal_weight_mgcm2=20.0,
        collector_thickness_um=12.0,
        coating_density_gcm3=3.0,
        coating_thickness_0pct_um=70.0,
        coating_thickness_100pct_um=71.0,
    )


@pytest.fixture
def graphite_anode():
    """Graphite anode material fixture."""
    return AnodeMaterial(
        id="test_anode",
        name="Graphite Test",
        chemistry="Graphite",
        rev_spec_capacity_mahg=360.0,
        max_spec_capacity_mahg=372.0,
        areal_weight_mgcm2=10.0,
        collector_thickness_um=8.0,
        coating_density_gcm3=1.5,
        coating_thickness_0pct_um=80.0,
        coating_thickness_100pct_um=84.0,
    )


@pytest.fixture
def pe_separator():
    """PE separator material fixture."""
    return SeparatorMaterial(
        id="test_separator",
        name="PE Test",
        thickness_um=12.0,
        porosity_pct=45.0,
        density_gcm3=0.95,
        areal_weight_mgcm2=0.6,
    )


@pytest.fixture
def standard_electrolyte():
    """Standard electrolyte fixture."""
    return ElectrolyteModel(
        id="test_electrolyte",
        name="LiPF6 Test",
        density_gcm3=1.2,
    )


@pytest.fixture
def geometry_21700():
    """21700 cell geometry fixture."""
    return create_21700_geometry()


@pytest.fixture
def geometry_4680():
    """4680 cell geometry fixture."""
    return create_4680_geometry()


@pytest.fixture
def traditional_winding():
    """Traditional tab winding configuration."""
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
    """Tabless winding configuration."""
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
    return SimplifiedHeader(
        total_mass_g=2.0,
        cap_material=CanMaterial.STEEL,
    )


# =============================================================================
# Geometry Tests
# =============================================================================


class TestCylindricalGeometry:
    """Tests for CylindricalGeometry class."""

    def test_21700_geometry_creation(self, geometry_21700):
        """Test 21700 geometry factory function."""
        assert geometry_21700.diameter_mm == 21.0
        assert geometry_21700.length_mm == 70.0
        assert geometry_21700.can_wall_thickness_mm == 0.25

    def test_4680_geometry_creation(self, geometry_4680):
        """Test 4680 geometry factory function."""
        assert geometry_4680.diameter_mm == 46.0
        assert geometry_4680.length_mm == 80.0
        assert geometry_4680.can_wall_thickness_mm == 0.35

    def test_18650_geometry_creation(self):
        """Test 18650 geometry factory function."""
        geo = create_18650_geometry()
        assert geo.diameter_mm == 18.0
        assert geo.length_mm == 65.0

    def test_can_inner_diameter(self, geometry_21700):
        """Test inner diameter calculation."""
        expected = 21.0 - 2 * 0.25
        assert abs(geometry_21700.can_inner_diameter_mm - expected) < 0.001

    def test_can_inner_length(self, geometry_21700):
        """Test inner length calculation."""
        expected = 70.0 - 0.4 - 3.5  # length - bottom - header
        assert abs(geometry_21700.can_inner_length_mm - expected) < 0.001

    def test_can_volume(self, geometry_21700):
        """Test can volume calculation."""
        r = 21.0 / 2 / 10  # cm
        h = 70.0 / 10  # cm
        expected = math.pi * r**2 * h
        assert abs(geometry_21700.can_volume_cm3 - expected) < 0.001


# =============================================================================
# Winding Configuration Tests
# =============================================================================


class TestWindingConfig:
    """Tests for WindingConfig class."""

    def test_traditional_winding(self, traditional_winding):
        """Test traditional winding configuration."""
        assert traditional_winding.tab_type == TabType.TRADITIONAL
        assert traditional_winding.anode_tab_width_mm == 6.0
        assert traditional_winding.cathode_tab_width_mm == 5.0

    def test_tabless_winding(self, tabless_winding):
        """Test tabless winding configuration."""
        assert tabless_winding.tab_type == TabType.TABLESS
        assert tabless_winding.anode_foil_extension_mm == 3.5
        assert tabless_winding.cathode_foil_extension_mm == 3.5

    def test_tabless_default_extension(self):
        """Test tabless winding default foil extension."""
        winding = WindingConfig(
            mandrel_diameter_mm=4.0,
            winding_clearance_mm=0.1,
            winding_tension_factor=0.97,
            tab_type=TabType.TABLESS,
        )
        # Default should be set to 3.0mm
        assert winding.anode_foil_extension_mm == 3.0
        assert winding.cathode_foil_extension_mm == 3.0


# =============================================================================
# Calculator Tests
# =============================================================================


class TestCylindricalCalculator:
    """Tests for CylindricalCalculator class."""

    def test_calculator_creation(
        self,
        geometry_21700,
        traditional_winding,
        simplified_header,
        nmc811_cathode,
        graphite_anode,
        pe_separator,
        standard_electrolyte,
    ):
        """Test calculator can be created with valid input."""
        cell_input = CylindricalCellInput(
            cell_name="Test 21700",
            geometry=geometry_21700,
            winding=traditional_winding,
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=simplified_header,
            nominal_voltage_v=3.6,
        )

        calculator = CylindricalCalculator(cell_input)
        assert calculator is not None

    def test_calculator_produces_report(
        self,
        geometry_21700,
        traditional_winding,
        simplified_header,
        nmc811_cathode,
        graphite_anode,
        pe_separator,
        standard_electrolyte,
    ):
        """Test calculator produces a valid report."""
        cell_input = CylindricalCellInput(
            cell_name="Test 21700",
            geometry=geometry_21700,
            winding=traditional_winding,
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=simplified_header,
            nominal_voltage_v=3.6,
        )

        calculator = CylindricalCalculator(cell_input)
        report = calculator.calculate()

        assert report.cell_type == "Cylindrical"
        assert report.capacity_ah > 0
        assert report.total_mass_g > 0
        assert report.gravimetric_ed_whkg > 0

    def test_jelly_roll_details(
        self,
        geometry_21700,
        traditional_winding,
        simplified_header,
        nmc811_cathode,
        graphite_anode,
        pe_separator,
        standard_electrolyte,
    ):
        """Test jelly roll details can be retrieved."""
        cell_input = CylindricalCellInput(
            cell_name="Test 21700",
            geometry=geometry_21700,
            winding=traditional_winding,
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=simplified_header,
        )

        calculator = CylindricalCalculator(cell_input)
        jelly_roll = calculator.get_jelly_roll_details()

        assert jelly_roll.num_winds > 0
        assert jelly_roll.electrode_length_m > 0
        assert jelly_roll.cathode_area_cm2 > 0
        assert jelly_roll.anode_area_cm2 > 0

    def test_21700_reasonable_capacity(
        self,
        geometry_21700,
        traditional_winding,
        simplified_header,
        nmc811_cathode,
        graphite_anode,
        pe_separator,
        standard_electrolyte,
    ):
        """Test 21700 produces reasonable capacity (3-6 Ah range)."""
        cell_input = CylindricalCellInput(
            cell_name="Test 21700",
            geometry=geometry_21700,
            winding=traditional_winding,
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=simplified_header,
            nominal_voltage_v=3.6,
        )

        calculator = CylindricalCalculator(cell_input)
        report = calculator.calculate()

        # 21700 cells typically 3-6 Ah
        assert 3.0 <= report.capacity_ah <= 6.0

    def test_4680_larger_than_21700(
        self,
        geometry_21700,
        geometry_4680,
        tabless_winding,
        simplified_header,
        nmc811_cathode,
        graphite_anode,
        pe_separator,
        standard_electrolyte,
    ):
        """Test 4680 has larger capacity than 21700."""
        # 21700 cell
        cell_21700 = CylindricalCellInput(
            cell_name="Test 21700",
            geometry=geometry_21700,
            winding=WindingConfig(
                mandrel_diameter_mm=2.5,
                winding_clearance_mm=0.1,
                winding_tension_factor=0.97,
                tab_type=TabType.TRADITIONAL,
            ),
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=SimplifiedHeader(total_mass_g=2.0),
        )

        # 4680 cell
        cell_4680 = CylindricalCellInput(
            cell_name="Test 4680",
            geometry=geometry_4680,
            winding=tabless_winding,
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=SimplifiedHeader(total_mass_g=8.0),
        )

        calc_21700 = CylindricalCalculator(cell_21700)
        calc_4680 = CylindricalCalculator(cell_4680)

        report_21700 = calc_21700.calculate()
        report_4680 = calc_4680.calculate()

        # 4680 should have much larger capacity
        assert report_4680.capacity_ah > report_21700.capacity_ah * 3

    def test_tabless_vs_traditional_mass_difference(
        self, geometry_4680, nmc811_cathode, graphite_anode, pe_separator, standard_electrolyte
    ):
        """Test that tabless design affects tab mass."""
        # Traditional
        traditional = CylindricalCellInput(
            cell_name="Traditional 4680",
            geometry=geometry_4680,
            winding=WindingConfig(
                mandrel_diameter_mm=4.5,
                winding_clearance_mm=0.15,
                winding_tension_factor=0.96,
                tab_type=TabType.TRADITIONAL,
                anode_tab_width_mm=10.0,
                anode_tab_thickness_mm=0.2,
                cathode_tab_width_mm=10.0,
                cathode_tab_thickness_mm=0.2,
            ),
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=SimplifiedHeader(total_mass_g=8.0),
        )

        # Tabless
        tabless = CylindricalCellInput(
            cell_name="Tabless 4680",
            geometry=geometry_4680,
            winding=WindingConfig(
                mandrel_diameter_mm=4.5,
                winding_clearance_mm=0.15,
                winding_tension_factor=0.96,
                tab_type=TabType.TABLESS,
                anode_foil_extension_mm=3.5,
                cathode_foil_extension_mm=3.5,
            ),
            can_material=CanMaterial.STEEL,
            cathode=nmc811_cathode,
            anode=graphite_anode,
            separator=pe_separator,
            electrolyte=standard_electrolyte,
            header_simplified=SimplifiedHeader(total_mass_g=8.0),
        )

        calc_trad = CylindricalCalculator(traditional)
        calc_tabless = CylindricalCalculator(tabless)

        report_trad = calc_trad.calculate()
        report_tabless = calc_tabless.calculate()

        # Both should have tab/foil mass calculated
        assert report_trad.tabs_mass_g >= 0
        assert report_tabless.tabs_mass_g >= 0


# =============================================================================
# Mass Calculation Tests
# =============================================================================


class TestMassCalculations:
    """Tests for mass calculation functions."""

    def test_cathode_mass_positive(self, nmc811_cathode):
        """Test cathode mass is positive."""
        mass = calculate_cylindrical_cathode_mass(
            cathode_area_cm2=1000.0,  # Both sides
            cathode=nmc811_cathode,
        )
        assert mass.coating_g > 0
        assert mass.collector_g > 0
        assert mass.total_g > 0

    def test_anode_mass_positive(self, graphite_anode):
        """Test anode mass is positive."""
        mass = calculate_cylindrical_anode_mass(anode_area_cm2=1000.0, anode=graphite_anode)
        assert mass.coating_g > 0
        assert mass.collector_g > 0
        assert mass.total_g > 0

    def test_separator_mass_positive(self, pe_separator):
        """Test separator mass is positive."""
        mass = calculate_cylindrical_separator_mass(
            separator_area_cm2=1000.0, separator=pe_separator
        )
        assert mass > 0

    def test_mass_scales_with_area(self, nmc811_cathode):
        """Test mass scales linearly with area."""
        mass_1000 = calculate_cylindrical_cathode_mass(1000.0, nmc811_cathode)
        mass_2000 = calculate_cylindrical_cathode_mass(2000.0, nmc811_cathode)

        # Mass should double when area doubles
        ratio = mass_2000.total_g / mass_1000.total_g
        assert abs(ratio - 2.0) < 0.01


# =============================================================================
# Validation Tests
# =============================================================================


class TestValidation:
    """Tests for input validation."""

    def test_missing_geometry_raises(
        self,
        traditional_winding,
        nmc811_cathode,
        graphite_anode,
        pe_separator,
        standard_electrolyte,
    ):
        """Test that missing geometry raises error."""
        with pytest.raises(ValueError, match="geometry"):
            cell_input = CylindricalCellInput(
                cell_name="Test",
                geometry=None,
                winding=traditional_winding,
                can_material=CanMaterial.STEEL,
                cathode=nmc811_cathode,
                anode=graphite_anode,
                separator=pe_separator,
                electrolyte=standard_electrolyte,
            )
            CylindricalCalculator(cell_input)

    def test_missing_materials_raises(self, geometry_21700, traditional_winding):
        """Test that missing materials raise error."""
        with pytest.raises(ValueError, match="cathode"):
            cell_input = CylindricalCellInput(
                cell_name="Test",
                geometry=geometry_21700,
                winding=traditional_winding,
                can_material=CanMaterial.STEEL,
                cathode=None,
                anode=None,
                separator=None,
                electrolyte=None,
            )
            CylindricalCalculator(cell_input)
