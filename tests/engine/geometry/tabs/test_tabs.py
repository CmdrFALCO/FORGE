"""Tests for tab geometry calculation."""

from pathlib import Path

import pytest

from forge.engine.geometry.loader import ArchetypeLoader
from forge.engine.geometry.tabs import (
    CylindricalTabCalculator,
    PouchTabCalculator,
    PrismaticTabCalculator,
    TabGeometry,
    TabPolarity,
    TabStrip,
    calculate_tab_geometry,
)
from forge.engine.geometry.tabs.models import Point3D, TabMaterial

ARCHETYPE_DIR = Path("docs")


@pytest.fixture
def byd_blade_geometry():
    """Load BYD Blade prismatic cell geometry."""
    loader = ArchetypeLoader(ARCHETYPE_DIR / "byd_blade_138ah_archetype.json")
    return loader.to_detailed_geometry()


@pytest.fixture
def tesla_4680_geometry():
    """Load Tesla 4680 cylindrical cell geometry."""
    loader = ArchetypeLoader(ARCHETYPE_DIR / "tesla_4680_archetype.json")
    return loader.to_detailed_geometry()


@pytest.fixture
def lg_e66a_geometry():
    """Load LG E66A pouch cell geometry."""
    loader = ArchetypeLoader(ARCHETYPE_DIR / "lg_e66a_archetype.json")
    return loader.to_detailed_geometry()


class TestTabModels:
    """Tests for tab geometry data models."""

    def test_point3d_to_tuple(self):
        """Point3D should convert to tuple."""
        p = Point3D(1.0, 2.0, 3.0)
        assert p.to_tuple() == (1.0, 2.0, 3.0)

    def test_point3d_addition(self):
        """Point3D should support addition."""
        p1 = Point3D(1.0, 2.0, 3.0)
        p2 = Point3D(4.0, 5.0, 6.0)
        result = p1 + p2
        assert result.x == 5.0
        assert result.y == 7.0
        assert result.z == 9.0

    def test_tab_strip_creation(self):
        """Should create valid tab strip."""
        tab = TabStrip(
            polarity=TabPolarity.POSITIVE,
            material=TabMaterial.ALUMINUM,
            attachment_point=Point3D(100, 0, 0),
            attachment_width_mm=40.0,
            attachment_height_mm=10.0,
            strip_width_mm=30.0,
            strip_thickness_mm=0.2,
            strip_length_mm=20.0,
        )

        assert tab.polarity == TabPolarity.POSITIVE
        assert tab.material == TabMaterial.ALUMINUM
        assert tab.strip_width_mm == 30.0

    def test_tab_strip_to_dict(self):
        """TabStrip should serialize to dict."""
        tab = TabStrip(
            polarity=TabPolarity.NEGATIVE,
            material=TabMaterial.COPPER,
            attachment_point=Point3D(0, 0, 0),
            attachment_width_mm=30.0,
            attachment_height_mm=5.0,
            strip_width_mm=20.0,
            strip_thickness_mm=0.1,
            strip_length_mm=15.0,
            exit_direction="z+",
        )
        d = tab.to_dict()

        assert d["polarity"] == "negative"
        assert d["material"] == "copper"
        assert d["attachment_point"] == (0, 0, 0)

    def test_tab_geometry_properties(self):
        """TabGeometry should compute properties correctly."""
        tab_geom = TabGeometry(cell_type="pouch")

        tab_geom.positive_tabs.append(
            TabStrip(
                polarity=TabPolarity.POSITIVE,
                material=TabMaterial.ALUMINUM,
                attachment_point=Point3D(0, 0, 0),
                attachment_width_mm=30.0,
                attachment_height_mm=10.0,
                strip_width_mm=20.0,
                strip_thickness_mm=0.2,
                strip_length_mm=15.0,
            )
        )

        tab_geom.negative_tabs.append(
            TabStrip(
                polarity=TabPolarity.NEGATIVE,
                material=TabMaterial.COPPER,
                attachment_point=Point3D(0, 0, 0),
                attachment_width_mm=30.0,
                attachment_height_mm=10.0,
                strip_width_mm=20.0,
                strip_thickness_mm=0.2,
                strip_length_mm=15.0,
            )
        )

        assert tab_geom.total_tab_count == 2
        assert len(tab_geom.get_all_tabs()) == 2
        assert not tab_geom.has_busbars

    def test_tab_geometry_to_dict(self):
        """Should serialize to dict."""
        tab_geom = TabGeometry(cell_type="prismatic")
        d = tab_geom.to_dict()

        assert "cell_type" in d
        assert d["cell_type"] == "prismatic"
        assert "positive_tabs" in d
        assert "negative_tabs" in d


class TestPouchTabCalculator:
    """Tests for pouch cell tab calculator."""

    def test_calculate_standard(self, lg_e66a_geometry):
        """Should calculate standard pouch tabs."""
        calc = PouchTabCalculator(tabs_per_polarity=2, configuration="standard")
        tab_geom = calc.calculate(lg_e66a_geometry)

        assert tab_geom.cell_type == "pouch"
        assert len(tab_geom.positive_tabs) == 2
        assert len(tab_geom.negative_tabs) == 2
        assert tab_geom.positive_tabs[0].polarity == TabPolarity.POSITIVE
        assert tab_geom.negative_tabs[0].polarity == TabPolarity.NEGATIVE

    def test_calculate_single_tab(self, lg_e66a_geometry):
        """Should calculate single tab per polarity."""
        calc = PouchTabCalculator(tabs_per_polarity=1, configuration="standard")
        tab_geom = calc.calculate(lg_e66a_geometry)

        assert len(tab_geom.positive_tabs) == 1
        assert len(tab_geom.negative_tabs) == 1

    def test_calculate_staggered(self, lg_e66a_geometry):
        """Should calculate staggered configuration."""
        calc = PouchTabCalculator(tabs_per_polarity=2, configuration="staggered")
        tab_geom = calc.calculate(lg_e66a_geometry)

        assert tab_geom.configuration == "staggered"
        assert len(tab_geom.positive_tabs) == 2
        assert len(tab_geom.negative_tabs) == 2

    def test_calculate_same_side(self, lg_e66a_geometry):
        """Should calculate same_side configuration."""
        calc = PouchTabCalculator(tabs_per_polarity=2, configuration="same_side")
        tab_geom = calc.calculate(lg_e66a_geometry)

        assert tab_geom.configuration == "same_side"
        # All tabs should exit in same direction
        all_tabs = tab_geom.get_all_tabs()
        exit_dirs = {t.exit_direction for t in all_tabs}
        assert len(exit_dirs) == 1  # All same direction

    def test_terminal_posts_created(self, lg_e66a_geometry):
        """Should create terminal posts."""
        calc = PouchTabCalculator()
        tab_geom = calc.calculate(lg_e66a_geometry)

        assert tab_geom.positive_terminal is not None
        assert tab_geom.negative_terminal is not None
        assert tab_geom.positive_terminal.polarity == TabPolarity.POSITIVE
        assert tab_geom.negative_terminal.polarity == TabPolarity.NEGATIVE

    def test_tab_materials(self, lg_e66a_geometry):
        """Positive tabs should be aluminum, negative should be nickel-plated copper."""
        calc = PouchTabCalculator()
        tab_geom = calc.calculate(lg_e66a_geometry)

        for tab in tab_geom.positive_tabs:
            assert tab.material == TabMaterial.ALUMINUM

        for tab in tab_geom.negative_tabs:
            assert tab.material == TabMaterial.NICKEL_PLATED_COPPER


class TestPrismaticTabCalculator:
    """Tests for prismatic cell tab calculator."""

    def test_calculate_with_busbars(self, byd_blade_geometry):
        """Should calculate prismatic tabs with busbars."""
        calc = PrismaticTabCalculator(tabs_per_polarity=4)
        tab_geom = calc.calculate(byd_blade_geometry)

        assert tab_geom.cell_type == "prismatic"
        assert len(tab_geom.positive_tabs) == 4
        assert len(tab_geom.negative_tabs) == 4
        assert tab_geom.has_busbars
        assert tab_geom.positive_busbar is not None
        assert tab_geom.negative_busbar is not None

    def test_busbar_connects_tabs(self, byd_blade_geometry):
        """Busbar should have connection points for all tabs."""
        calc = PrismaticTabCalculator(tabs_per_polarity=4)
        tab_geom = calc.calculate(byd_blade_geometry)

        assert tab_geom.positive_busbar is not None
        assert len(tab_geom.positive_busbar.tab_connection_points) == 4

    def test_terminal_on_top(self, byd_blade_geometry):
        """Terminals should be on top face (same Z)."""
        calc = PrismaticTabCalculator()
        tab_geom = calc.calculate(byd_blade_geometry)

        assert tab_geom.positive_terminal is not None
        assert tab_geom.negative_terminal is not None
        # Terminals at same height (top)
        assert (
            tab_geom.positive_terminal.position.z
            == tab_geom.negative_terminal.position.z
        )

    def test_tabs_exit_upward(self, byd_blade_geometry):
        """Prismatic tabs should exit in Z+ direction."""
        calc = PrismaticTabCalculator()
        tab_geom = calc.calculate(byd_blade_geometry)

        for tab in tab_geom.get_all_tabs():
            assert tab.exit_direction == "z+"


class TestCylindricalTabCalculator:
    """Tests for cylindrical cell tab calculator."""

    def test_calculate_tabless(self, tesla_4680_geometry):
        """Should calculate tabless (4680) configuration."""
        calc = CylindricalTabCalculator(configuration="tabless")
        tab_geom = calc.calculate(tesla_4680_geometry)

        assert tab_geom.cell_type == "cylindrical"
        assert tab_geom.configuration == "tabless"
        assert len(tab_geom.positive_tabs) > 0  # Virtual contact points
        assert len(tab_geom.negative_tabs) > 0
        assert "tabless" in tab_geom.notes[0].lower()

    def test_calculate_traditional(self, tesla_4680_geometry):
        """Should calculate traditional tabbed configuration."""
        calc = CylindricalTabCalculator(configuration="traditional")
        tab_geom = calc.calculate(tesla_4680_geometry)

        assert tab_geom.configuration == "traditional"
        assert len(tab_geom.positive_tabs) == 1
        assert len(tab_geom.negative_tabs) == 1

    def test_positive_exits_up_negative_down(self, tesla_4680_geometry):
        """Positive should exit Z+, negative should exit Z-."""
        calc = CylindricalTabCalculator(configuration="tabless")
        tab_geom = calc.calculate(tesla_4680_geometry)

        for tab in tab_geom.positive_tabs:
            assert tab.exit_direction == "z+"

        for tab in tab_geom.negative_tabs:
            assert tab.exit_direction == "z-"

    def test_terminals_at_ends(self, tesla_4680_geometry):
        """Terminals should be at top (+) and bottom (-)."""
        calc = CylindricalTabCalculator()
        tab_geom = calc.calculate(tesla_4680_geometry)

        assert tab_geom.positive_terminal is not None
        assert tab_geom.negative_terminal is not None
        # Positive on top (higher Z), negative on bottom (lower Z)
        assert (
            tab_geom.positive_terminal.position.z
            > tab_geom.negative_terminal.position.z
        )


class TestCalculateTabGeometry:
    """Tests for the convenience function."""

    def test_auto_detect_pouch(self, lg_e66a_geometry):
        """Should auto-detect pouch cell type."""
        tab_geom = calculate_tab_geometry(lg_e66a_geometry)
        assert tab_geom.cell_type == "pouch"

    def test_auto_detect_prismatic(self, byd_blade_geometry):
        """Should auto-detect prismatic cell type."""
        tab_geom = calculate_tab_geometry(byd_blade_geometry)
        assert tab_geom.cell_type == "prismatic"

    def test_auto_detect_cylindrical(self, tesla_4680_geometry):
        """Should auto-detect cylindrical cell type."""
        tab_geom = calculate_tab_geometry(tesla_4680_geometry)
        assert tab_geom.cell_type == "cylindrical"

    def test_custom_configuration(self, lg_e66a_geometry):
        """Should apply custom configuration."""
        tab_geom = calculate_tab_geometry(lg_e66a_geometry, configuration="staggered")
        assert tab_geom.configuration == "staggered"

    def test_custom_tabs_per_polarity(self, lg_e66a_geometry):
        """Should apply custom tab count."""
        tab_geom = calculate_tab_geometry(lg_e66a_geometry, tabs_per_polarity=3)
        assert len(tab_geom.positive_tabs) == 3
        assert len(tab_geom.negative_tabs) == 3

    def test_unsupported_cell_type(self, lg_e66a_geometry):
        """Should raise error for unsupported cell type."""
        lg_e66a_geometry.cell_type = "unknown"
        with pytest.raises(ValueError, match="Unsupported cell type"):
            calculate_tab_geometry(lg_e66a_geometry)


class TestDetailedGeometryIntegration:
    """Tests for integration with DetailedGeometry."""

    def test_calculate_tabs_method(self, lg_e66a_geometry):
        """DetailedGeometry.calculate_tabs should work."""
        assert lg_e66a_geometry.tab_geometry is None

        result = lg_e66a_geometry.calculate_tabs()

        assert result is not None
        assert lg_e66a_geometry.tab_geometry is result
        assert result.cell_type == "pouch"

    def test_calculate_tabs_with_config(self, byd_blade_geometry):
        """Should pass configuration to calculator."""
        result = byd_blade_geometry.calculate_tabs(tabs_per_polarity=6)
        assert len(result.positive_tabs) == 6

    def test_tab_geometry_persists(self, tesla_4680_geometry):
        """Tab geometry should persist on DetailedGeometry."""
        tesla_4680_geometry.calculate_tabs()
        assert tesla_4680_geometry.tab_geometry is not None

        # Verify it's the same object
        first = tesla_4680_geometry.tab_geometry
        tesla_4680_geometry.calculate_tabs()
        second = tesla_4680_geometry.tab_geometry

        # Should be replaced (not mutated)
        assert first is not second
