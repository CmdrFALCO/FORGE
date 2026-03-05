"""Tests for Prismatic CAD geometry export functionality."""

import pytest

from forge.engine.models.prismatic import (
    PrismaticCADExport,
    PrismaticCADFeatures,
    TerminalGeometry,
    VentGeometry,
)


class TestTerminalGeometry:
    """Tests for TerminalGeometry dataclass."""

    def test_default_values(self):
        """Test that defaults are industry standard."""
        term = TerminalGeometry()
        assert term.positive_diameter_mm == 16.0
        assert term.negative_diameter_mm == 16.0
        assert term.positive_height_mm == 10.0
        assert term.negative_height_mm == 10.0

    def test_auto_position_calculation(self):
        """Test automatic position calculation when None."""
        term = TerminalGeometry()  # All positions None
        cell_width = 200.0
        cell_thickness = 50.0

        pos = term.get_positions(cell_width, cell_thickness)

        # Positive at 30% from left
        assert pos["positive_x_mm"] == pytest.approx(60.0)  # 200 * 0.3
        # Negative at 70% from left
        assert pos["negative_x_mm"] == pytest.approx(140.0)  # 200 * 0.7
        # Both centered front-back
        assert pos["positive_y_mm"] == pytest.approx(25.0)  # 50 / 2
        assert pos["negative_y_mm"] == pytest.approx(25.0)

    def test_explicit_position_override(self):
        """Test that explicit positions override auto-calculation."""
        term = TerminalGeometry(
            positive_x_mm=45.0,
            negative_x_mm=155.0,
        )
        cell_width = 200.0
        cell_thickness = 50.0

        pos = term.get_positions(cell_width, cell_thickness)

        assert pos["positive_x_mm"] == 45.0  # Explicit value used
        assert pos["negative_x_mm"] == 155.0  # Explicit value used

    def test_mixed_explicit_and_auto(self):
        """Test mix of explicit and auto positions."""
        term = TerminalGeometry(
            positive_x_mm=50.0,
            # negative_x_mm stays None for auto
            positive_y_mm=20.0,
            # negative_y_mm stays None for auto
        )
        cell_width = 300.0
        cell_thickness = 60.0

        pos = term.get_positions(cell_width, cell_thickness)

        assert pos["positive_x_mm"] == 50.0  # Explicit
        assert pos["negative_x_mm"] == 210.0  # Auto: 300 * 0.7
        assert pos["positive_y_mm"] == 20.0  # Explicit
        assert pos["negative_y_mm"] == 30.0  # Auto: 60 / 2


class TestVentGeometry:
    """Tests for VentGeometry dataclass."""

    def test_default_values(self):
        """Test vent defaults."""
        vent = VentGeometry()
        assert vent.diameter_mm == 5.0
        assert vent.x_mm is None
        assert vent.y_mm is None

    def test_auto_center_position(self):
        """Test automatic centering when position not specified."""
        vent = VentGeometry()
        cell_width = 200.0
        cell_thickness = 50.0

        pos = vent.get_position(cell_width, cell_thickness)

        assert pos["x_mm"] == pytest.approx(100.0)  # Centered
        assert pos["y_mm"] == pytest.approx(25.0)  # Centered

    def test_explicit_offset_position(self):
        """Test explicit offset from center."""
        vent = VentGeometry(
            x_mm=80.0,
            y_mm=15.0,
        )
        cell_width = 200.0
        cell_thickness = 50.0

        pos = vent.get_position(cell_width, cell_thickness)

        assert pos["x_mm"] == 80.0
        assert pos["y_mm"] == 15.0

    def test_partial_explicit_position(self):
        """Test override only X position, auto Y."""
        vent = VentGeometry(x_mm=120.0)
        cell_width = 300.0
        cell_thickness = 60.0

        pos = vent.get_position(cell_width, cell_thickness)

        assert pos["x_mm"] == 120.0  # Explicit
        assert pos["y_mm"] == 30.0  # Auto: 60 / 2


class TestPrismaticCADFeatures:
    """Tests for PrismaticCADFeatures dataclass."""

    def test_default_corner_radii(self):
        """Test default corner radii are reasonable."""
        cad = PrismaticCADFeatures()
        assert cad.external_corner_radius_mm == 3.0
        assert cad.internal_corner_radius_mm == 1.5
        assert cad.lid_corner_radius_mm == 2.0

    def test_default_lid_thickness(self):
        """Test lid thickness default."""
        cad = PrismaticCADFeatures()
        assert cad.lid_thickness_mm == 2.0

    def test_default_weld_seam_width(self):
        """Test weld seam width default."""
        cad = PrismaticCADFeatures()
        assert cad.weld_seam_width_mm == 1.5

    def test_nested_defaults(self):
        """Test that nested objects get defaults."""
        cad = PrismaticCADFeatures()
        assert cad.terminals.positive_diameter_mm == 16.0
        assert cad.vent.diameter_mm == 5.0

    def test_custom_terminal_geometry(self):
        """Test passing custom terminal geometry."""
        custom_terminals = TerminalGeometry(
            positive_diameter_mm=20.0,
            negative_diameter_mm=18.0,
        )
        cad = PrismaticCADFeatures(terminals=custom_terminals)

        assert cad.terminals.positive_diameter_mm == 20.0
        assert cad.terminals.negative_diameter_mm == 18.0

    def test_custom_vent_geometry(self):
        """Test passing custom vent geometry."""
        custom_vent = VentGeometry(diameter_mm=8.0)
        cad = PrismaticCADFeatures(vent=custom_vent)

        assert cad.vent.diameter_mm == 8.0


class TestPrismaticCADExport:
    """Tests for PrismaticCADExport dataclass."""

    def test_dataclass_creation(self):
        """Test that CAD export can be created with all fields."""
        export = PrismaticCADExport(
            cell_height_mm=100.0,
            cell_width_mm=200.0,
            cell_thickness_mm=50.0,
            external_corner_radius_mm=3.0,
            internal_corner_radius_mm=1.5,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_mm=0.5,
            wall_back_mm=0.5,
            wall_left_mm=0.7,
            wall_right_mm=0.7,
            cavity_height_mm=97.0,
            cavity_width_mm=198.6,
            cavity_thickness_mm=49.0,
            lid_thickness_mm=2.0,
            lid_corner_radius_mm=2.0,
            positive_terminal_x_mm=60.0,
            positive_terminal_y_mm=100.0,
            positive_terminal_z_mm=25.0,
            positive_terminal_diameter_mm=16.0,
            positive_terminal_height_mm=10.0,
            negative_terminal_x_mm=140.0,
            negative_terminal_y_mm=100.0,
            negative_terminal_z_mm=25.0,
            negative_terminal_diameter_mm=16.0,
            negative_terminal_height_mm=10.0,
            vent_x_mm=100.0,
            vent_y_mm=100.0,
            vent_z_mm=25.0,
            vent_diameter_mm=5.0,
            stack_height_mm=95.0,
            stack_width_mm=196.0,
            stack_thickness_dry_mm=45.0,
            stack_thickness_soc0_mm=46.0,
            stack_thickness_soc100_mm=47.0,
            stack_count=2,
            gap_to_wall_dry_mm=2.0,
            gap_to_wall_soc100_mm=0.5,
        )

        assert export.cell_height_mm == 100.0
        assert export.positive_terminal_diameter_mm == 16.0
        assert export.stack_count == 2
        assert export.vent_diameter_mm == 5.0

    def test_cavity_dimensions_consistency(self):
        """Test that cavity dimensions are consistent with walls."""
        export = PrismaticCADExport(
            cell_height_mm=100.0,
            cell_width_mm=200.0,
            cell_thickness_mm=50.0,
            external_corner_radius_mm=3.0,
            internal_corner_radius_mm=1.5,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_mm=0.5,
            wall_back_mm=0.5,
            wall_left_mm=0.7,
            wall_right_mm=0.7,
            cavity_height_mm=97.0,  # 100 - 2 - 1
            cavity_width_mm=198.6,  # 200 - 0.7 - 0.7
            cavity_thickness_mm=49.0,  # 50 - 0.5 - 0.5
            lid_thickness_mm=2.0,
            lid_corner_radius_mm=2.0,
            positive_terminal_x_mm=60.0,
            positive_terminal_y_mm=100.0,
            positive_terminal_z_mm=25.0,
            positive_terminal_diameter_mm=16.0,
            positive_terminal_height_mm=10.0,
            negative_terminal_x_mm=140.0,
            negative_terminal_y_mm=100.0,
            negative_terminal_z_mm=25.0,
            negative_terminal_diameter_mm=16.0,
            negative_terminal_height_mm=10.0,
            vent_x_mm=100.0,
            vent_y_mm=100.0,
            vent_z_mm=25.0,
            vent_diameter_mm=5.0,
            stack_height_mm=95.0,
            stack_width_mm=196.0,
            stack_thickness_dry_mm=45.0,
            stack_thickness_soc0_mm=46.0,
            stack_thickness_soc100_mm=47.0,
            stack_count=2,
            gap_to_wall_dry_mm=2.0,
            gap_to_wall_soc100_mm=0.5,
        )

        # Verify cavity is smaller than envelope
        assert export.cavity_height_mm < export.cell_height_mm
        assert export.cavity_width_mm < export.cell_width_mm
        assert export.cavity_thickness_mm < export.cell_thickness_mm

    def test_terminal_positions_on_lid(self):
        """Test that terminals are positioned on the lid (Y = cell_height)."""
        export = PrismaticCADExport(
            cell_height_mm=100.0,
            cell_width_mm=200.0,
            cell_thickness_mm=50.0,
            external_corner_radius_mm=3.0,
            internal_corner_radius_mm=1.5,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_mm=0.5,
            wall_back_mm=0.5,
            wall_left_mm=0.7,
            wall_right_mm=0.7,
            cavity_height_mm=97.0,
            cavity_width_mm=198.6,
            cavity_thickness_mm=49.0,
            lid_thickness_mm=2.0,
            lid_corner_radius_mm=2.0,
            positive_terminal_x_mm=60.0,
            positive_terminal_y_mm=100.0,
            positive_terminal_z_mm=25.0,
            positive_terminal_diameter_mm=16.0,
            positive_terminal_height_mm=10.0,
            negative_terminal_x_mm=140.0,
            negative_terminal_y_mm=100.0,
            negative_terminal_z_mm=25.0,
            negative_terminal_diameter_mm=16.0,
            negative_terminal_height_mm=10.0,
            vent_x_mm=100.0,
            vent_y_mm=100.0,
            vent_z_mm=25.0,
            vent_diameter_mm=5.0,
            stack_height_mm=95.0,
            stack_width_mm=196.0,
            stack_thickness_dry_mm=45.0,
            stack_thickness_soc0_mm=46.0,
            stack_thickness_soc100_mm=47.0,
            stack_count=2,
            gap_to_wall_dry_mm=2.0,
            gap_to_wall_soc100_mm=0.5,
        )

        # Both terminals and vent should be on top lid
        assert export.positive_terminal_y_mm == export.cell_height_mm
        assert export.negative_terminal_y_mm == export.cell_height_mm
        assert export.vent_y_mm == export.cell_height_mm

    def test_soc_swelling(self):
        """Test that SoC swelling produces increasing thickness."""
        export = PrismaticCADExport(
            cell_height_mm=100.0,
            cell_width_mm=200.0,
            cell_thickness_mm=50.0,
            external_corner_radius_mm=3.0,
            internal_corner_radius_mm=1.5,
            wall_top_mm=2.0,
            wall_bottom_mm=1.0,
            wall_front_mm=0.5,
            wall_back_mm=0.5,
            wall_left_mm=0.7,
            wall_right_mm=0.7,
            cavity_height_mm=97.0,
            cavity_width_mm=198.6,
            cavity_thickness_mm=49.0,
            lid_thickness_mm=2.0,
            lid_corner_radius_mm=2.0,
            positive_terminal_x_mm=60.0,
            positive_terminal_y_mm=100.0,
            positive_terminal_z_mm=25.0,
            positive_terminal_diameter_mm=16.0,
            positive_terminal_height_mm=10.0,
            negative_terminal_x_mm=140.0,
            negative_terminal_y_mm=100.0,
            negative_terminal_z_mm=25.0,
            negative_terminal_diameter_mm=16.0,
            negative_terminal_height_mm=10.0,
            vent_x_mm=100.0,
            vent_y_mm=100.0,
            vent_z_mm=25.0,
            vent_diameter_mm=5.0,
            stack_height_mm=95.0,
            stack_width_mm=196.0,
            stack_thickness_dry_mm=45.0,
            stack_thickness_soc0_mm=46.0,
            stack_thickness_soc100_mm=47.0,
            stack_count=2,
            gap_to_wall_dry_mm=2.0,
            gap_to_wall_soc100_mm=0.5,
        )

        # Thickness should increase with SoC (swelling)
        assert export.stack_thickness_dry_mm < export.stack_thickness_soc0_mm
        assert export.stack_thickness_soc0_mm < export.stack_thickness_soc100_mm


class TestV1PrismaticCADExport:
    """Integration test using V1 Prismatic reference cell."""

    def test_v1_prismatic_cad_features_defaults(self):
        """Test that CAD features have reasonable defaults for V1."""
        cad = PrismaticCADFeatures()

        # V1 Prismatic dimensions from reference
        cell_width = 264.6
        cell_thickness = 29.6

        # Get terminal positions for V1 cell
        term_pos = cad.terminals.get_positions(cell_width, cell_thickness)
        vent_pos = cad.vent.get_position(cell_width, cell_thickness)

        # Verify positions are reasonable for this cell size
        assert 70 < term_pos["positive_x_mm"] < 90  # ~30% of 264.6
        assert 180 < term_pos["negative_x_mm"] < 200  # ~70% of 264.6
        assert 14 < term_pos["positive_y_mm"] < 16  # ~50% of 29.6
        assert 130 < vent_pos["x_mm"] < 135  # ~50% of 264.6
        assert 14 < vent_pos["y_mm"] < 16  # ~50% of 29.6

    def test_v1_prismatic_terminal_separation(self):
        """Test that V1 terminals are well separated."""
        cad = PrismaticCADFeatures()
        cell_width = 264.6

        term_pos = cad.terminals.get_positions(cell_width, 29.6)

        # Terminals should be separated by ~40% of width (30% and 70% positions)
        separation = term_pos["negative_x_mm"] - term_pos["positive_x_mm"]
        assert separation == pytest.approx(0.4 * cell_width, rel=1e-6)  # 40% separation

