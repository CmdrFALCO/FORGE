"""Tests for layer stack geometry calculations.

This module tests:
- Layer, LayerStackGeometry, WindingGeometry dataclasses
- StackedGeometryCalculator
- WoundGeometryCalculator
- Layer positioning and thickness calculations
"""

import pytest

from forge.engine.geometry.layer_stack import (
    Layer,
    LayerType,
    LayerStackGeometry,
    WindLayer,
    WindingGeometry,
)
from forge.engine.geometry.swelling import SwellingProfile
from forge.engine.geometry.calculators.stacked import StackedGeometryCalculator
from forge.engine.geometry.calculators.wound import WoundGeometryCalculator


class TestLayer:
    """Test Layer dataclass."""

    def test_layer_creation(self):
        """Layer should be created with all attributes."""
        layer = Layer(
            layer_type=LayerType.CATHODE_COATING,
            z_bottom_um=100.0,
            thickness_um=70.0,
            material="NMC811",
            layer_index=5,
        )

        assert layer.layer_type == LayerType.CATHODE_COATING
        assert layer.z_bottom_um == 100.0
        assert layer.thickness_um == 70.0
        assert layer.material == "NMC811"
        assert layer.layer_index == 5

    def test_layer_z_properties(self):
        """Layer should calculate z_top and z_center correctly."""
        layer = Layer(
            layer_type=LayerType.SEPARATOR,
            z_bottom_um=0.0,
            thickness_um=20.0,
            material="PP/PE/PP",
            layer_index=0,
        )

        assert layer.z_top_um == pytest.approx(20.0, rel=0.001)
        assert layer.z_center_um == pytest.approx(10.0, rel=0.001)

    def test_layer_mm_conversion(self):
        """Layer should convert to mm correctly."""
        layer = Layer(
            layer_type=LayerType.ANODE_COLLECTOR,
            z_bottom_um=1000.0,
            thickness_um=10.0,
            material="Cu",
            layer_index=0,
        )

        assert layer.z_bottom_mm == pytest.approx(1.0, rel=0.001)
        assert layer.z_top_mm == pytest.approx(1.01, rel=0.001)
        assert layer.thickness_mm == pytest.approx(0.01, rel=0.001)


class TestLayerStackGeometry:
    """Test LayerStackGeometry dataclass."""

    def test_empty_stack(self):
        """Empty stack should have zero thickness and no layers."""
        stack = LayerStackGeometry()

        assert stack.num_layers == 0
        assert stack.total_thickness_um == 0.0
        assert stack.total_thickness_mm == 0.0

    def test_get_layers_by_type(self):
        """Should filter layers by type correctly."""
        layers = [
            Layer(LayerType.SEPARATOR, 0, 20, "PP", 0),
            Layer(LayerType.ANODE_COATING, 20, 80, "Graphite", 1),
            Layer(LayerType.SEPARATOR, 100, 20, "PP", 2),
            Layer(LayerType.CATHODE_COATING, 120, 70, "NMC", 3),
        ]
        stack = LayerStackGeometry(layers=layers)

        separators = stack.get_layers_by_type(LayerType.SEPARATOR)
        assert len(separators) == 2

        cathodes = stack.get_cathode_layers()
        assert len(cathodes) == 1
        assert cathodes[0].material == "NMC"

    def test_to_z_coordinates(self):
        """Should return correct Z boundary coordinates."""
        layers = [
            Layer(LayerType.SEPARATOR, 0, 20, "PP", 0),
            Layer(LayerType.ANODE_COATING, 20, 80, "Graphite", 1),
        ]
        stack = LayerStackGeometry(layers=layers, total_thickness_um=100)

        coords = stack.to_z_coordinates_mm()

        assert coords[0] == pytest.approx(0.0, rel=0.001)
        assert coords[1] == pytest.approx(0.020, rel=0.001)  # Top of separator
        assert coords[2] == pytest.approx(0.100, rel=0.001)  # Top of anode

    def test_layer_summary(self):
        """Should return correct layer count summary."""
        layers = [
            Layer(LayerType.SEPARATOR, 0, 20, "PP", 0),
            Layer(LayerType.SEPARATOR, 20, 20, "PP", 1),
            Layer(LayerType.CATHODE_COATING, 40, 70, "NMC", 2),
        ]
        stack = LayerStackGeometry(layers=layers)

        summary = stack.to_layer_summary()

        assert summary["separator"] == 2
        assert summary["cathode_coating"] == 1


class TestStackedGeometryCalculator:
    """Test StackedGeometryCalculator for pouch/prismatic cells."""

    def test_basic_calculation(self):
        """Should generate layers for specified electrode pairs."""
        calc = StackedGeometryCalculator()
        stack = calc.calculate(
            num_electrode_pairs=2,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        # 2 pairs × 8 layers/pair + 1 final separator = 17 layers
        assert len(stack.layers) == 17
        assert stack.num_electrode_pairs == 2

    def test_layer_count_correct(self):
        """Layer count should match expected structure."""
        calc = StackedGeometryCalculator()
        stack = calc.calculate(
            num_electrode_pairs=5,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        summary = stack.to_layer_summary()

        # 5 pairs: 10 cathode coatings, 10 anode coatings, 11 separators,
        # 5 cathode collectors, 5 anode collectors
        assert summary[LayerType.CATHODE_COATING.value] == 10
        assert summary[LayerType.ANODE_COATING.value] == 10
        assert summary[LayerType.SEPARATOR.value] == 11
        assert summary[LayerType.CATHODE_COLLECTOR.value] == 5
        assert summary[LayerType.ANODE_COLLECTOR.value] == 5

    def test_z_coordinates_increasing(self):
        """Z coordinates should be monotonically increasing."""
        calc = StackedGeometryCalculator()
        stack = calc.calculate(
            num_electrode_pairs=5,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        z_coords = [layer.z_bottom_um for layer in stack.layers]
        assert z_coords == sorted(z_coords)

    def test_total_thickness_calculation(self):
        """Total thickness should equal sum of all layer thicknesses."""
        calc = StackedGeometryCalculator(SwellingProfile.no_swelling())
        stack = calc.calculate(
            num_electrode_pairs=1,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        # 1 pair: sep + anode_coat + anode_coll + anode_coat + sep +
        #         cath_coat + cath_coll + cath_coat + sep
        # = 20 + 80 + 10 + 80 + 20 + 70 + 15 + 70 + 20 = 385 µm
        expected = 20 + 80 + 10 + 80 + 20 + 70 + 15 + 70 + 20
        assert stack.total_thickness_um == pytest.approx(expected, rel=0.001)

    def test_swelling_increases_thickness(self):
        """Swelling should increase total stack thickness."""
        no_swell = StackedGeometryCalculator(SwellingProfile.no_swelling())
        with_swell = StackedGeometryCalculator(SwellingProfile.for_chemistry("NMC811"))

        kwargs = {
            "num_electrode_pairs": 5,
            "cathode_coating_um": 70,
            "cathode_collector_um": 15,
            "anode_coating_um": 80,
            "anode_collector_um": 10,
            "separator_um": 20,
        }

        stack_no_swell = no_swell.calculate(**kwargs)
        stack_swell = with_swell.calculate(**kwargs)

        assert stack_swell.total_thickness_um > stack_no_swell.total_thickness_um
        assert stack_swell.swelling_applied is True
        assert stack_no_swell.swelling_applied is False

    def test_materials_assigned(self):
        """Layers should have correct material assignments."""
        calc = StackedGeometryCalculator()
        stack = calc.calculate(
            num_electrode_pairs=1,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
            cathode_material="LFP",
            anode_material="Graphite",
            separator_material="Celgard",
        )

        cathode_layers = stack.get_cathode_layers()
        assert all(l.material == "LFP" for l in cathode_layers)

        anode_layers = stack.get_anode_layers()
        assert all(l.material == "Graphite" for l in anode_layers)

        separator_layers = stack.get_separator_layers()
        assert all(l.material == "Celgard" for l in separator_layers)

    def test_unit_cell_thickness(self):
        """Unit cell thickness calculation should be correct."""
        calc = StackedGeometryCalculator(SwellingProfile.no_swelling())

        unit_cell = calc.calculate_unit_cell_thickness(
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        # 2*sep + 2*anode_coat + anode_coll + 2*cath_coat + cath_coll
        # = 40 + 160 + 10 + 140 + 15 = 365 µm
        expected = 2*20 + 2*80 + 10 + 2*70 + 15
        assert unit_cell == pytest.approx(expected, rel=0.001)


class TestWindLayer:
    """Test WindLayer dataclass."""

    def test_wind_layer_creation(self):
        """WindLayer should store radial positions correctly."""
        wind = WindLayer(
            wind_index=0,
            r_inner_um=2500.0,
            r_outer_um=3000.0,
        )

        assert wind.wind_index == 0
        assert wind.r_inner_um == 2500.0
        assert wind.r_outer_um == 3000.0
        assert wind.thickness_um == pytest.approx(500.0, rel=0.001)

    def test_wind_layer_mm_conversion(self):
        """WindLayer should convert to mm correctly."""
        wind = WindLayer(
            wind_index=0,
            r_inner_um=2500.0,
            r_outer_um=3000.0,
        )

        assert wind.r_inner_mm == pytest.approx(2.5, rel=0.001)
        assert wind.r_outer_mm == pytest.approx(3.0, rel=0.001)
        assert wind.thickness_mm == pytest.approx(0.5, rel=0.001)


class TestWindingGeometry:
    """Test WindingGeometry dataclass."""

    def test_empty_winding(self):
        """Empty winding should have zero winds."""
        winding = WindingGeometry()

        assert winding.num_winds == 0
        assert len(winding.winds) == 0

    def test_jellyroll_thickness(self):
        """Jellyroll thickness should be half diameter difference."""
        winding = WindingGeometry(
            mandrel_diameter_mm=4.0,
            outer_diameter_mm=20.0,
        )

        assert winding.jellyroll_thickness_mm == pytest.approx(8.0, rel=0.001)

    def test_get_winds(self):
        """Should retrieve winds by index correctly."""
        winds = [
            WindLayer(wind_index=0, r_inner_um=2000, r_outer_um=2500),
            WindLayer(wind_index=1, r_inner_um=2500, r_outer_um=3000),
        ]
        winding = WindingGeometry(winds=winds, num_winds=2)

        assert winding.get_innermost_wind().wind_index == 0
        assert winding.get_outermost_wind().wind_index == 1
        assert winding.get_wind(0).r_inner_um == 2000
        assert winding.get_wind(5) is None


class TestWoundGeometryCalculator:
    """Test WoundGeometryCalculator for cylindrical cells."""

    def test_basic_calculation(self):
        """Should generate winds for specified number of turns."""
        calc = WoundGeometryCalculator()
        winding = calc.calculate(
            num_winds=10,
            mandrel_diameter_mm=4.0,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        assert winding.num_winds == 10
        assert len(winding.winds) == 10
        assert winding.mandrel_diameter_mm == 4.0

    def test_winds_ordered_radially(self):
        """Winds should be ordered from center outward."""
        calc = WoundGeometryCalculator()
        winding = calc.calculate(
            num_winds=5,
            mandrel_diameter_mm=4.0,
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        for i in range(len(winding.winds) - 1):
            assert winding.winds[i].r_outer_um <= winding.winds[i + 1].r_inner_um

    def test_outer_diameter_grows(self):
        """More winds should increase outer diameter."""
        calc = WoundGeometryCalculator()

        kwargs = {
            "mandrel_diameter_mm": 4.0,
            "cathode_coating_um": 70,
            "cathode_collector_um": 15,
            "anode_coating_um": 80,
            "anode_collector_um": 10,
            "separator_um": 20,
        }

        winding_10 = calc.calculate(num_winds=10, **kwargs)
        winding_20 = calc.calculate(num_winds=20, **kwargs)

        assert winding_20.outer_diameter_mm > winding_10.outer_diameter_mm

    def test_swelling_increases_diameter(self):
        """Swelling should increase outer diameter."""
        no_swell = WoundGeometryCalculator(SwellingProfile.no_swelling())
        with_swell = WoundGeometryCalculator(SwellingProfile.for_chemistry("NMC811"))

        kwargs = {
            "num_winds": 20,
            "mandrel_diameter_mm": 4.0,
            "cathode_coating_um": 70,
            "cathode_collector_um": 15,
            "anode_coating_um": 80,
            "anode_collector_um": 10,
            "separator_um": 20,
        }

        winding_no_swell = no_swell.calculate(**kwargs)
        winding_swell = with_swell.calculate(**kwargs)

        assert winding_swell.outer_diameter_mm > winding_no_swell.outer_diameter_mm

    def test_wind_thickness_calculation(self):
        """Wind thickness should match electrode stack thickness."""
        calc = WoundGeometryCalculator(SwellingProfile.no_swelling())

        wind_thickness = calc.calculate_wind_thickness(
            cathode_coating_um=70,
            cathode_collector_um=15,
            anode_coating_um=80,
            anode_collector_um=10,
            separator_um=20,
        )

        # anode_coll + 2*anode_coat + 2*sep + 2*cath_coat + cath_coll
        # = 10 + 160 + 40 + 140 + 15 = 365 µm
        expected = 10 + 2*80 + 2*20 + 2*70 + 15
        assert wind_thickness == pytest.approx(expected, rel=0.001)

    def test_electrode_length_estimation(self):
        """Should estimate electrode length from winding geometry."""
        calc = WoundGeometryCalculator()

        length = calc.calculate_electrode_length(
            num_winds=38,
            mandrel_diameter_mm=5.0,
            cathode_coating_um=87,
            cathode_collector_um=12,
            anode_coating_um=117,
            anode_collector_um=7,
            separator_um=20,
        )

        # Tesla 4680 has ~3300mm electrode length
        # Our estimate should be in reasonable range
        assert length > 2000  # At least 2m
        assert length < 5000  # Less than 5m
