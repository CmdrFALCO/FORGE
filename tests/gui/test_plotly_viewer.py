"""Tests for Plotly visualization module."""

from pathlib import Path

import pytest

pytest.importorskip("plotly")

from forge.engine.geometry.loader import ArchetypeLoader
from forge.gui.visualization import (
    DEFAULT_COLORS,
    ColorScheme,
    GeometryBuilder,
    PlotlyViewer,
    create_box_mesh,
    create_cylinder_mesh,
)

ARCHETYPE_DIR = Path("docs")


class TestCreateBoxMesh:
    """Tests for create_box_mesh function."""

    def test_box_mesh_has_correct_vertices(self) -> None:
        """Box mesh should have 8 vertices."""
        mesh = create_box_mesh(
            x_min=0,
            x_max=10,
            y_min=0,
            y_max=20,
            z_min=0,
            z_max=5,
            color="rgba(255, 0, 0, 0.8)",
            name="test_box",
        )

        assert mesh.x is not None
        assert len(mesh.x) == 8
        assert mesh.name == "test_box"

    def test_box_mesh_bounds(self) -> None:
        """Box mesh vertices should match specified bounds."""
        mesh = create_box_mesh(
            x_min=-5,
            x_max=5,
            y_min=-10,
            y_max=10,
            z_min=0,
            z_max=3,
            color="red",
            name="bounded_box",
        )

        assert min(mesh.x) == -5
        assert max(mesh.x) == 5
        assert min(mesh.y) == -10
        assert max(mesh.y) == 10
        assert min(mesh.z) == 0
        assert max(mesh.z) == 3

    def test_box_mesh_opacity_from_color(self) -> None:
        """Box mesh should extract opacity from RGBA color."""
        mesh = create_box_mesh(
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=1,
            z_min=0,
            z_max=1,
            color="rgba(100, 100, 100, 0.5)",
            name="transparent_box",
        )

        assert mesh.opacity == 0.5

    def test_box_mesh_opacity_override(self) -> None:
        """Box mesh should use explicit opacity over color."""
        mesh = create_box_mesh(
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=1,
            z_min=0,
            z_max=1,
            color="rgba(100, 100, 100, 0.5)",
            name="explicit_opacity_box",
            opacity=0.9,
        )

        assert mesh.opacity == 0.9


class TestCreateCylinderMesh:
    """Tests for create_cylinder_mesh function."""

    def test_solid_cylinder_mesh(self) -> None:
        """Solid cylinder mesh should have correct structure."""
        mesh = create_cylinder_mesh(
            r_inner=0,
            r_outer=10,
            z_min=0,
            z_max=50,
            color="rgba(0, 0, 255, 0.8)",
            name="solid_cylinder",
        )

        assert mesh.x is not None
        assert mesh.name == "solid_cylinder"

    def test_hollow_cylinder_mesh(self) -> None:
        """Hollow cylinder mesh should have correct structure."""
        mesh = create_cylinder_mesh(
            r_inner=5,
            r_outer=10,
            z_min=0,
            z_max=50,
            color="rgba(0, 255, 0, 0.8)",
            name="hollow_cylinder",
        )

        assert mesh.x is not None
        assert mesh.name == "hollow_cylinder"

    def test_cylinder_mesh_height(self) -> None:
        """Cylinder mesh should have correct Z bounds."""
        mesh = create_cylinder_mesh(
            r_inner=0,
            r_outer=10,
            z_min=5,
            z_max=65,
            color="blue",
            name="tall_cylinder",
        )

        assert min(mesh.z) == 5
        assert max(mesh.z) == 65

    def test_cylinder_mesh_radius(self) -> None:
        """Cylinder mesh should have correct radius bounds."""
        mesh = create_cylinder_mesh(
            r_inner=0,
            r_outer=23,
            z_min=0,
            z_max=50,
            color="green",
            name="wide_cylinder",
        )

        # Radius from center should be approximately r_outer
        import numpy as np

        radii = np.sqrt(np.array(mesh.x) ** 2 + np.array(mesh.y) ** 2)
        assert max(radii) == pytest.approx(23, abs=0.01)


class TestColorScheme:
    """Tests for ColorScheme class."""

    def test_default_colors_exist(self) -> None:
        """Default color scheme should have all required colors."""
        colors = DEFAULT_COLORS

        assert colors.cathode_coating
        assert colors.anode_coating
        assert colors.cathode_collector
        assert colors.anode_collector
        assert colors.separator
        assert colors.can_wall
        assert colors.pouch_film
        assert colors.electrode_pair

    def test_chemistry_specific_colors(self) -> None:
        """Different chemistries should have different cathode colors."""
        colors = ColorScheme()

        lfp_color = colors.get_cathode_color("LFP")
        nmc811_color = colors.get_cathode_color("NMC811")

        assert lfp_color != nmc811_color
        assert "rgba" in lfp_color
        assert "rgba" in nmc811_color

    def test_ncm_nmc_normalization(self) -> None:
        """NCM and NMC should give same color."""
        colors = ColorScheme()

        ncm811 = colors.get_cathode_color("NCM811")
        nmc811 = colors.get_cathode_color("NMC811")

        assert ncm811 == nmc811

    def test_unknown_chemistry_fallback(self) -> None:
        """Unknown chemistry should return default cathode color."""
        colors = ColorScheme()

        unknown = colors.get_cathode_color("UnknownChemistry123")

        assert unknown == colors.cathode_coating

    def test_get_layer_color(self) -> None:
        """get_layer_color should return correct colors for layer types."""
        colors = ColorScheme()

        assert colors.get_layer_color("cathode_coating") == colors.cathode_coating
        assert colors.get_layer_color("anode_coating") == colors.anode_coating
        assert colors.get_layer_color("cathode_collector") == colors.cathode_collector
        assert colors.get_layer_color("anode_collector") == colors.anode_collector
        assert colors.get_layer_color("separator") == colors.separator


class TestGeometryBuilder:
    """Tests for GeometryBuilder class."""

    @pytest.fixture
    def byd_blade_geometry(self):
        """Load BYD Blade archetype for testing."""
        path = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")
        loader = ArchetypeLoader(path)
        return loader.to_detailed_geometry()

    @pytest.fixture
    def tesla_4680_geometry(self):
        """Load Tesla 4680 archetype for testing."""
        path = ARCHETYPE_DIR / "tesla_4680_archetype.json"
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")
        loader = ArchetypeLoader(path)
        return loader.to_detailed_geometry()

    def test_build_simplified_prismatic(self, byd_blade_geometry) -> None:
        """Build simplified view for prismatic cell."""
        builder = GeometryBuilder()
        traces = builder.build_simplified(byd_blade_geometry)

        assert len(traces) > 0
        assert all(hasattr(t, "x") for t in traces)

    def test_build_detailed_prismatic(self, byd_blade_geometry) -> None:
        """Build detailed view for prismatic cell."""
        builder = GeometryBuilder()
        traces = builder.build_detailed(byd_blade_geometry)

        assert len(traces) > 0
        # Detailed should have more traces than simplified
        simplified_traces = builder.build_simplified(byd_blade_geometry)
        assert len(traces) >= len(simplified_traces)

    def test_build_simplified_cylindrical(self, tesla_4680_geometry) -> None:
        """Build simplified view for cylindrical cell."""
        builder = GeometryBuilder()
        traces = builder.build_simplified(tesla_4680_geometry)

        assert len(traces) > 0

    def test_build_detailed_cylindrical(self, tesla_4680_geometry) -> None:
        """Build detailed view for cylindrical cell."""
        builder = GeometryBuilder()
        traces = builder.build_detailed(tesla_4680_geometry)

        assert len(traces) > 0


class TestPlotlyViewer:
    """Tests for PlotlyViewer class."""

    @pytest.fixture
    def byd_blade_geometry(self):
        """Load BYD Blade archetype for testing."""
        path = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")
        loader = ArchetypeLoader(path)
        return loader.to_detailed_geometry()

    @pytest.fixture
    def tesla_4680_geometry(self):
        """Load Tesla 4680 archetype for testing."""
        path = ARCHETYPE_DIR / "tesla_4680_archetype.json"
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")
        loader = ArchetypeLoader(path)
        return loader.to_detailed_geometry()

    def test_create_simplified_figure_prismatic(self, byd_blade_geometry) -> None:
        """Should create simplified figure for prismatic cell."""
        viewer = PlotlyViewer()
        fig = viewer.create_figure(byd_blade_geometry, detail_level="simplified")

        assert fig is not None
        assert len(fig.data) > 0
        assert "BYD" in fig.layout.title.text

    def test_create_detailed_figure_prismatic(self, byd_blade_geometry) -> None:
        """Should create detailed figure for prismatic cell."""
        viewer = PlotlyViewer()
        fig = viewer.create_figure(byd_blade_geometry, detail_level="detailed")

        assert fig is not None
        assert len(fig.data) > 0

    def test_create_simplified_figure_cylindrical(self, tesla_4680_geometry) -> None:
        """Should create simplified figure for cylindrical cell."""
        viewer = PlotlyViewer()
        fig = viewer.create_figure(tesla_4680_geometry, detail_level="simplified")

        assert fig is not None
        assert len(fig.data) > 0
        assert "Tesla" in fig.layout.title.text or "4680" in fig.layout.title.text

    def test_create_detailed_figure_cylindrical(self, tesla_4680_geometry) -> None:
        """Should create detailed figure for cylindrical cell."""
        viewer = PlotlyViewer()
        fig = viewer.create_figure(tesla_4680_geometry, detail_level="detailed")

        assert fig is not None
        assert len(fig.data) > 0

    def test_create_cross_section_xz(self, byd_blade_geometry) -> None:
        """Should create XZ cross-section view."""
        viewer = PlotlyViewer()
        fig = viewer.create_cross_section(byd_blade_geometry, plane="XZ")

        assert fig is not None
        assert "Side View" in fig.layout.title.text or "XZ" in fig.layout.title.text

    def test_create_cross_section_yz(self, byd_blade_geometry) -> None:
        """Should create YZ cross-section view."""
        viewer = PlotlyViewer()
        fig = viewer.create_cross_section(byd_blade_geometry, plane="YZ")

        assert fig is not None
        assert "YZ" in fig.layout.title.text

    def test_custom_figure_options(self, byd_blade_geometry) -> None:
        """Should respect custom figure options."""
        viewer = PlotlyViewer()
        fig = viewer.create_figure(
            byd_blade_geometry,
            detail_level="simplified",
            title="Custom Title",
            show_axes=False,
            show_legend=False,
            width=1000,
            height=800,
        )

        assert fig.layout.title.text == "Custom Title"
        assert fig.layout.width == 1000
        assert fig.layout.height == 800
        assert fig.layout.showlegend is False


class TestAllArchetypesRender:
    """Test that all archetype files render without errors."""

    @pytest.fixture
    def available_archetypes(self):
        """Get list of available archetype files."""
        files = list(ARCHETYPE_DIR.glob("*_archetype.json"))
        if not files:
            pytest.skip("No archetype files found in docs/")
        return files

    def test_all_archetypes_simplified(self, available_archetypes) -> None:
        """All archetypes should render in simplified mode."""
        viewer = PlotlyViewer()

        for archetype_file in available_archetypes:
            try:
                loader = ArchetypeLoader(archetype_file)
                geometry = loader.to_detailed_geometry()
                fig = viewer.create_figure(geometry, detail_level="simplified")

                assert fig is not None, f"Failed to create figure for {archetype_file.name}"
                assert len(fig.data) > 0, f"No traces in figure for {archetype_file.name}"

            except Exception as e:
                pytest.fail(f"Error rendering {archetype_file.name}: {e}")

    def test_all_archetypes_detailed(self, available_archetypes) -> None:
        """All archetypes should render in detailed mode."""
        viewer = PlotlyViewer()

        for archetype_file in available_archetypes:
            try:
                loader = ArchetypeLoader(archetype_file)
                geometry = loader.to_detailed_geometry()
                fig = viewer.create_figure(geometry, detail_level="detailed")

                assert fig is not None, f"Failed to create figure for {archetype_file.name}"
                assert len(fig.data) > 0, f"No traces in figure for {archetype_file.name}"

            except Exception as e:
                pytest.fail(f"Error rendering {archetype_file.name}: {e}")

    @pytest.mark.parametrize(
        "archetype_name",
        [
            "byd_blade_138ah_archetype.json",
            "tesla_4680_archetype.json",
            "lg_e66a_archetype.json",
            "samsung_21700_50g_archetype.json",
        ],
    )
    def test_specific_archetypes(self, archetype_name: str) -> None:
        """Test specific archetypes render correctly."""
        path = ARCHETYPE_DIR / archetype_name
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")

        loader = ArchetypeLoader(path)
        geometry = loader.to_detailed_geometry()

        viewer = PlotlyViewer()

        # Test both modes
        fig_simple = viewer.create_figure(geometry, detail_level="simplified")
        fig_detail = viewer.create_figure(geometry, detail_level="detailed")

        assert fig_simple is not None
        assert fig_detail is not None
        assert len(fig_simple.data) > 0
        assert len(fig_detail.data) > 0


class TestBOLvsEOLComparison:
    """Tests for BOL vs EOL comparison functionality."""

    @pytest.fixture
    def byd_blade_bol_eol(self):
        """Load BYD Blade in both BOL and EOL states."""
        path = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")

        loader = ArchetypeLoader(path)
        geometry_bol = loader.to_detailed_geometry(apply_swelling=False)

        loader = ArchetypeLoader(path)
        geometry_eol = loader.to_detailed_geometry(apply_swelling=True)

        return geometry_bol, geometry_eol

    def test_create_comparison_figure(self, byd_blade_bol_eol) -> None:
        """Should create comparison figure with two subplots."""
        geometry_bol, geometry_eol = byd_blade_bol_eol

        viewer = PlotlyViewer()
        fig = viewer.create_comparison_figure(geometry_bol, geometry_eol)

        assert fig is not None
        assert len(fig.data) > 0
        assert "BOL" in fig.layout.title.text or "Comparison" in fig.layout.title.text

    def test_eol_thicker_than_bol(self, byd_blade_bol_eol) -> None:
        """EOL geometry should be thicker than BOL due to swelling."""
        geometry_bol, geometry_eol = byd_blade_bol_eol

        bol_thickness = geometry_bol.total_stack_thickness_mm()
        eol_thickness = geometry_eol.total_stack_thickness_mm()

        assert eol_thickness > bol_thickness, "EOL should be thicker due to swelling"
        assert (eol_thickness - bol_thickness) / bol_thickness < 0.15, "Swelling should be < 15%"


class TestExplodedView:
    """Tests for exploded view functionality."""

    @pytest.fixture
    def byd_blade_geometry(self):
        """Load BYD Blade archetype for testing."""
        path = ARCHETYPE_DIR / "byd_blade_138ah_archetype.json"
        if not path.exists():
            pytest.skip(f"Archetype file not found: {path}")
        loader = ArchetypeLoader(path)
        return loader.to_detailed_geometry()

    def test_create_exploded_view(self, byd_blade_geometry) -> None:
        """Should create exploded view figure."""
        viewer = PlotlyViewer()
        fig = viewer.create_exploded_view(byd_blade_geometry, explosion_factor=1.5)

        assert fig is not None
        assert len(fig.data) > 0
        assert "Exploded" in fig.layout.title.text

    def test_exploded_view_max_layers(self, byd_blade_geometry) -> None:
        """Exploded view should limit layers when max_layers specified."""
        viewer = PlotlyViewer()
        fig = viewer.create_exploded_view(byd_blade_geometry, max_layers=10)

        assert fig is not None
        # Should have at most 10 layers + casing
        assert len(fig.data) <= 12


