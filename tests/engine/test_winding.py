"""Tests for jelly roll winding calculations.

This module tests the winding calculation functions for cylindrical cells.
"""

import pytest

from forge.engine.calculations.winding import (
    calculate_compressed_thickness,
    calculate_electrode_length_analytical,
    calculate_electrode_length_iterative,
    calculate_electrode_width,
    calculate_jelly_roll,
    calculate_jelly_roll_pore_volume,
    calculate_layer_thickness,
    calculate_number_of_winds,
    estimate_jelly_roll_volume,
)
from forge.engine.models.cylindrical import (
    TabType,
    WindingConfig,
    create_4680_geometry,
    create_21700_geometry,
)
from forge.engine.models.materials import (
    AnodeMaterial,
    CathodeMaterial,
    SeparatorMaterial,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def test_cathode():
    """Test cathode material."""
    return CathodeMaterial(
        id="test_cathode",
        name="Test Cathode",
        chemistry="NMC",
        rev_spec_capacity_mahg=180.0,
        max_spec_capacity_mahg=200.0,
        areal_weight_mgcm2=18.0,
        collector_thickness_um=12.0,
        coating_density_gcm3=3.0,
        coating_thickness_0pct_um=60.0,
        coating_thickness_100pct_um=61.0,
    )


@pytest.fixture
def test_anode():
    """Test anode material."""
    return AnodeMaterial(
        id="test_anode",
        name="Test Anode",
        chemistry="Graphite",
        rev_spec_capacity_mahg=350.0,
        max_spec_capacity_mahg=372.0,
        areal_weight_mgcm2=9.0,
        collector_thickness_um=8.0,
        coating_density_gcm3=1.4,
        coating_thickness_0pct_um=70.0,
        coating_thickness_100pct_um=73.0,
    )


@pytest.fixture
def test_separator():
    """Test separator material."""
    return SeparatorMaterial(
        id="test_separator",
        name="Test Separator",
        thickness_um=12.0,
        porosity_pct=45.0,
        density_gcm3=0.95,
        areal_weight_mgcm2=0.6,
    )


@pytest.fixture
def geometry_21700():
    """21700 geometry."""
    return create_21700_geometry()


@pytest.fixture
def geometry_4680():
    """4680 geometry."""
    return create_4680_geometry()


@pytest.fixture
def traditional_winding():
    """Traditional winding config."""
    return WindingConfig(
        mandrel_diameter_mm=2.5,
        winding_clearance_mm=0.1,
        winding_tension_factor=0.97,
        tab_type=TabType.TRADITIONAL,
    )


@pytest.fixture
def tabless_winding():
    """Tabless winding config."""
    return WindingConfig(
        mandrel_diameter_mm=4.5,
        winding_clearance_mm=0.15,
        winding_tension_factor=0.96,
        tab_type=TabType.TABLESS,
        anode_foil_extension_mm=3.5,
        cathode_foil_extension_mm=3.5,
    )


# =============================================================================
# Layer Thickness Tests
# =============================================================================


class TestLayerThickness:
    """Tests for layer thickness calculations."""

    def test_layer_thickness_calculation(self, test_cathode, test_anode, test_separator):
        """Test layer thickness is calculated correctly."""
        layer_thk = calculate_layer_thickness(test_cathode, test_anode, test_separator)

        # Check individual components
        assert layer_thk.cathode_collector_um == 12.0
        assert layer_thk.cathode_coating_single_um == 60.0
        assert layer_thk.anode_collector_um == 8.0
        assert layer_thk.anode_coating_single_um == 70.0
        assert layer_thk.separator_um == 12.0

    def test_cathode_total_thickness(self, test_cathode, test_anode, test_separator):
        """Test cathode total includes collector and both sides coating."""
        layer_thk = calculate_layer_thickness(test_cathode, test_anode, test_separator)

        # 12 (collector) + 2×60 (coatings) = 132 µm
        expected = 12.0 + 2 * 60.0
        assert layer_thk.cathode_total_um == expected

    def test_anode_total_thickness(self, test_cathode, test_anode, test_separator):
        """Test anode total includes collector and both sides coating."""
        layer_thk = calculate_layer_thickness(test_cathode, test_anode, test_separator)

        # 8 (collector) + 2×70 (coatings) = 148 µm
        expected = 8.0 + 2 * 70.0
        assert layer_thk.anode_total_um == expected

    def test_single_layer_thickness(self, test_cathode, test_anode, test_separator):
        """Test single wound layer includes all components."""
        layer_thk = calculate_layer_thickness(test_cathode, test_anode, test_separator)

        # cathode_total + anode_total + 2×separator
        expected = (12.0 + 2 * 60.0) + (8.0 + 2 * 70.0) + 2 * 12.0
        assert layer_thk.single_layer_um == expected

    def test_single_layer_mm_conversion(self, test_cathode, test_anode, test_separator):
        """Test mm conversion is correct."""
        layer_thk = calculate_layer_thickness(test_cathode, test_anode, test_separator)

        assert layer_thk.single_layer_mm == layer_thk.single_layer_um / 1000.0


# =============================================================================
# Compression Model Tests
# =============================================================================


class TestCompression:
    """Tests for compression model."""

    def test_no_compression_at_outer_wind(self):
        """Test outermost wind has no compression."""
        compressed = calculate_compressed_thickness(
            theoretical_thickness_um=100.0,
            wind_number=99,  # Last wind
            total_winds=100,
            max_compression_pct=5.0,
        )

        # Outermost should be very close to theoretical
        assert abs(compressed - 100.0) < 0.1

    def test_max_compression_at_inner_wind(self):
        """Test innermost wind has max compression."""
        compressed = calculate_compressed_thickness(
            theoretical_thickness_um=100.0,
            wind_number=0,  # First wind
            total_winds=100,
            max_compression_pct=5.0,
        )

        # Should be 95µm (5% compressed)
        expected = 100.0 * (1 - 5.0 / 100)
        assert abs(compressed - expected) < 0.1

    def test_linear_gradient(self):
        """Test compression follows linear gradient."""
        total_winds = 100
        max_comp = 5.0

        # Check middle wind
        middle_compressed = calculate_compressed_thickness(100.0, 50, total_winds, max_comp)

        # Middle should have ~2.5% compression
        expected = 100.0 * (1 - 2.5 / 100)
        assert abs(middle_compressed - expected) < 0.5

    def test_single_wind_no_crash(self):
        """Test single wind doesn't cause division by zero."""
        compressed = calculate_compressed_thickness(100.0, 0, 1, 5.0)
        assert compressed > 0


# =============================================================================
# Number of Winds Tests
# =============================================================================


class TestNumberOfWinds:
    """Tests for number of winds calculation."""

    def test_simple_case(self):
        """Test simple number of winds calculation."""
        # 10mm available, 1mm layer thickness → 10 winds
        n_winds = calculate_number_of_winds(
            inner_radius_mm=5.0,
            outer_radius_mm=15.0,  # 10mm radial space
            layer_thickness_mm=1.0,
            tension_factor=1.0,
        )

        assert abs(n_winds - 10.0) < 0.001

    def test_compression_increases_winds(self):
        """Test compression allows more winds."""
        no_compression = calculate_number_of_winds(5.0, 15.0, 1.0, 1.0)
        with_compression = calculate_number_of_winds(5.0, 15.0, 1.0, 0.9)

        assert with_compression > no_compression

    def test_zero_thickness_returns_zero(self):
        """Test zero layer thickness returns zero winds."""
        n_winds = calculate_number_of_winds(5.0, 15.0, 0.0, 1.0)
        assert n_winds == 0.0

    def test_negative_space_returns_zero(self):
        """Test inner > outer returns zero winds."""
        n_winds = calculate_number_of_winds(15.0, 5.0, 1.0, 1.0)
        assert n_winds == 0.0


# =============================================================================
# Electrode Length Tests
# =============================================================================


class TestElectrodeLength:
    """Tests for electrode length calculations."""

    def test_analytical_length_positive(self):
        """Test analytical length is positive."""
        length = calculate_electrode_length_analytical(
            num_winds=50.0, inner_radius_mm=2.5, layer_thickness_mm=0.3, tension_factor=0.97
        )

        assert length > 0

    def test_iterative_length_positive(self):
        """Test iterative length is positive."""
        length = calculate_electrode_length_iterative(
            num_winds=50, inner_radius_mm=2.5, layer_thickness_mm=0.3, tension_factor=0.97
        )

        assert length > 0

    def test_methods_agree(self):
        """Test analytical and iterative methods give similar results."""
        params = {
            "num_winds": 50,
            "inner_radius_mm": 2.5,
            "layer_thickness_mm": 0.3,
            "tension_factor": 0.97,
        }

        analytical = calculate_electrode_length_analytical(
            params["num_winds"],
            params["inner_radius_mm"],
            params["layer_thickness_mm"],
            params["tension_factor"],
        )

        iterative = calculate_electrode_length_iterative(
            int(params["num_winds"]),
            params["inner_radius_mm"],
            params["layer_thickness_mm"],
            params["tension_factor"],
        )

        # Should be within 5%
        relative_diff = abs(analytical - iterative) / analytical
        assert relative_diff < 0.05

    def test_zero_winds_returns_zero(self):
        """Test zero winds returns zero length."""
        length = calculate_electrode_length_analytical(0, 2.5, 0.3, 1.0)
        assert length == 0.0


# =============================================================================
# Electrode Width Tests
# =============================================================================


class TestElectrodeWidth:
    """Tests for electrode width calculations."""

    def test_traditional_equal_widths(self):
        """Test traditional design has equal widths."""
        sep_w, cat_w, ano_w = calculate_electrode_width(
            can_inner_length_mm=65.0,
            header_clearance_mm=1.0,
            bottom_clearance_mm=0.5,
            tab_type=TabType.TRADITIONAL,
        )

        # All should be equal for traditional
        assert sep_w == cat_w == ano_w

    def test_tabless_different_widths(self):
        """Test tabless design has different widths."""
        sep_w, cat_w, ano_w = calculate_electrode_width(
            can_inner_length_mm=65.0,
            header_clearance_mm=1.0,
            bottom_clearance_mm=0.5,
            tab_type=TabType.TABLESS,
            anode_foil_extension_mm=3.0,
            cathode_foil_extension_mm=3.0,
        )

        # Separator should be widest (no extension)
        assert sep_w > cat_w
        assert sep_w > ano_w

    def test_clearances_reduce_width(self):
        """Test clearances reduce available width."""
        sep_w, _, _ = calculate_electrode_width(
            can_inner_length_mm=65.0,
            header_clearance_mm=1.0,
            bottom_clearance_mm=0.5,
            tab_type=TabType.TRADITIONAL,
        )

        expected = 65.0 - 1.0 - 0.5
        assert abs(sep_w - expected) < 0.001


# =============================================================================
# Jelly Roll Calculation Tests
# =============================================================================


class TestJellyRollCalculation:
    """Tests for complete jelly roll calculation."""

    def test_21700_jelly_roll(
        self, geometry_21700, traditional_winding, test_cathode, test_anode, test_separator
    ):
        """Test 21700 jelly roll calculation."""
        result = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        assert result.num_winds > 20  # Should have many winds
        assert result.electrode_length_m > 0.5  # At least 0.5m
        assert result.cathode_area_cm2 > 0
        assert result.anode_area_cm2 > 0

    def test_4680_more_winds_than_21700(
        self,
        geometry_21700,
        geometry_4680,
        traditional_winding,
        tabless_winding,
        test_cathode,
        test_anode,
        test_separator,
    ):
        """Test 4680 has more winds than 21700."""
        result_21700 = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        result_4680 = calculate_jelly_roll(
            geometry=geometry_4680,
            winding=tabless_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        # 4680 should have more winds (larger diameter)
        assert result_4680.num_winds > result_21700.num_winds

    def test_compression_ratio_less_than_one(
        self, geometry_21700, test_cathode, test_anode, test_separator
    ):
        """Test compression ratio is less than 1 when tension applied."""
        winding = WindingConfig(
            mandrel_diameter_mm=2.5,
            winding_clearance_mm=0.1,
            winding_tension_factor=0.95,  # 5% compression
            tab_type=TabType.TRADITIONAL,
        )

        result = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        # Compression ratio should match tension factor
        assert abs(result.compression_ratio - 0.95) < 0.01

    def test_outer_diameter_within_can(
        self, geometry_21700, traditional_winding, test_cathode, test_anode, test_separator
    ):
        """Test jelly roll outer diameter fits within can."""
        result = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        max_od = geometry_21700.can_inner_diameter_mm - 2 * traditional_winding.winding_clearance_mm
        assert result.jelly_roll_outer_diameter_mm <= max_od + 0.1  # Small tolerance


# =============================================================================
# Pore Volume Tests
# =============================================================================


class TestPoreVolume:
    """Tests for pore volume calculations."""

    def test_pore_volumes_positive(
        self, geometry_21700, traditional_winding, test_cathode, test_anode, test_separator
    ):
        """Test all pore volumes are positive."""
        jelly_roll = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        cat_pores, ano_pores, sep_pores = calculate_jelly_roll_pore_volume(
            jelly_roll=jelly_roll,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
            cathode_porosity_pct=30.0,
            anode_porosity_pct=35.0,
        )

        assert cat_pores > 0
        assert ano_pores > 0
        assert sep_pores > 0

    def test_higher_porosity_more_pores(
        self, geometry_21700, traditional_winding, test_cathode, test_anode, test_separator
    ):
        """Test higher porosity gives more pore volume."""
        jelly_roll = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        low_porosity = calculate_jelly_roll_pore_volume(
            jelly_roll, test_cathode, test_anode, test_separator, 20.0, 25.0
        )

        high_porosity = calculate_jelly_roll_pore_volume(
            jelly_roll, test_cathode, test_anode, test_separator, 40.0, 45.0
        )

        # Higher porosity should give more pore volume
        assert sum(high_porosity) > sum(low_porosity)


# =============================================================================
# Volume Estimation Tests
# =============================================================================


class TestVolumeEstimation:
    """Tests for jelly roll volume estimation."""

    def test_volume_positive(
        self, geometry_21700, traditional_winding, test_cathode, test_anode, test_separator
    ):
        """Test volume is positive."""
        jelly_roll = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        volume = estimate_jelly_roll_volume(
            jelly_roll=jelly_roll, mandrel_diameter_mm=traditional_winding.mandrel_diameter_mm
        )

        assert volume > 0

    def test_volume_less_than_can_volume(
        self, geometry_21700, traditional_winding, test_cathode, test_anode, test_separator
    ):
        """Test jelly roll volume is less than can volume."""
        jelly_roll = calculate_jelly_roll(
            geometry=geometry_21700,
            winding=traditional_winding,
            cathode=test_cathode,
            anode=test_anode,
            separator=test_separator,
        )

        jr_volume = estimate_jelly_roll_volume(jelly_roll, traditional_winding.mandrel_diameter_mm)

        assert jr_volume < geometry_21700.can_volume_cm3
