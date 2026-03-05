"""Unit tests for geometry mapping functions."""

import pytest

from forge.engine.conversion.exceptions import MissingFieldError
from forge.engine.conversion.template_to_input import _map_geometry, _map_sheet_geometry
from forge.engine.models.prismatic import PrismaticGeometry, PrismaticSheetGeometry


class TestMapGeometry:
    """Tests for _map_geometry function."""

    def test_map_geometry_basic(self):
        """Map basic envelope geometry."""
        envelope = {
            "cell_height_mm": 88.8,
            "cell_width_mm": 264.6,
            "cell_thickness_mm": 29.6,
            "wall_top_mm": 2.0,
            "wall_bottom_mm": 1.0,
            "wall_front_back_mm": 0.5,
            "wall_sides_mm": 0.7,
        }
        geometry = _map_geometry(envelope)

        assert isinstance(geometry, PrismaticGeometry)
        assert geometry.cell_height_mm == 88.8
        assert geometry.cell_width_mm == 264.6
        assert geometry.cell_thickness_mm == 29.6
        assert geometry.wall_top_mm == 2.0
        assert geometry.wall_bottom_mm == 1.0
        assert geometry.wall_front_back_mm == 0.5
        assert geometry.wall_sides_mm == 0.7

    def test_map_geometry_with_insulation_coating(self):
        """Map geometry with custom insulation coating."""
        envelope = {
            "cell_height_mm": 88.8,
            "cell_width_mm": 264.6,
            "cell_thickness_mm": 29.6,
            "wall_top_mm": 2.0,
            "wall_bottom_mm": 1.0,
            "wall_front_back_mm": 0.5,
            "wall_sides_mm": 0.7,
            "insulation_coating_um": 100.0,
        }
        geometry = _map_geometry(envelope)
        assert geometry.insulation_coating_um == 100.0

    def test_map_geometry_with_default_insulation_coating(self):
        """Map geometry with default insulation coating."""
        envelope = {
            "cell_height_mm": 88.8,
            "cell_width_mm": 264.6,
            "cell_thickness_mm": 29.6,
            "wall_top_mm": 2.0,
            "wall_bottom_mm": 1.0,
            "wall_front_back_mm": 0.5,
            "wall_sides_mm": 0.7,
        }
        geometry = _map_geometry(envelope)
        assert geometry.insulation_coating_um == 85.0

    def test_map_geometry_missing_required_field(self):
        """Raise error when required field missing."""
        envelope = {
            "cell_height_mm": 88.8,
            "cell_width_mm": 264.6,
            # Missing cell_thickness_mm
            "wall_top_mm": 2.0,
            "wall_bottom_mm": 1.0,
            "wall_front_back_mm": 0.5,
            "wall_sides_mm": 0.7,
        }
        with pytest.raises(MissingFieldError):
            _map_geometry(envelope)

    def test_map_geometry_template_format(self):
        """Map geometry from template format with metadata dicts."""
        envelope = {
            "cell_height_mm": {"_default": 88.8},
            "cell_width_mm": {"_default": 264.6},
            "cell_thickness_mm": {"_default": 29.6},
            "wall_top_mm": {"_default": 2.0},
            "wall_bottom_mm": {"_default": 1.0},
            "wall_front_back_mm": {"_default": 0.5},
            "wall_sides_mm": {"_default": 0.7},
        }
        geometry = _map_geometry(envelope)

        assert geometry.cell_height_mm == 88.8
        assert geometry.cell_width_mm == 264.6
        assert geometry.cell_thickness_mm == 29.6


class TestMapSheetGeometry:
    """Tests for _map_sheet_geometry function."""

    def test_map_sheet_geometry_basic(self):
        """Map basic sheet geometry."""
        stack_config = {
            "sheet_geometry": {
                "cathode_height_mm": 200.0,
                "cathode_width_mm": 100.0,
            }
        }
        geometry = _map_sheet_geometry(stack_config)

        assert isinstance(geometry, PrismaticSheetGeometry)
        assert geometry.cathode_height_mm == 200.0
        assert geometry.cathode_width_mm == 100.0

    def test_map_sheet_geometry_with_offsets(self):
        """Map sheet geometry with all offset specifications."""
        stack_config = {
            "sheet_geometry": {
                "cathode_height_mm": 200.0,
                "cathode_width_mm": 100.0,
                "anode_offset_top_mm": 3.0,
                "anode_offset_bottom_mm": 3.0,
                "anode_offset_left_mm": 2.5,
                "anode_offset_right_mm": 2.5,
                "separator_offset_top_mm": 2.0,
                "separator_offset_bottom_mm": 2.0,
                "separator_offset_left_mm": 1.5,
                "separator_offset_right_mm": 1.5,
            }
        }
        geometry = _map_sheet_geometry(stack_config)

        assert geometry.anode_offset_top_mm == 3.0
        assert geometry.anode_offset_bottom_mm == 3.0
        assert geometry.separator_offset_top_mm == 2.0
        assert geometry.separator_offset_left_mm == 1.5

    def test_map_sheet_geometry_with_defaults(self):
        """Map sheet geometry using default offsets."""
        stack_config = {
            "sheet_geometry": {
                "cathode_height_mm": 200.0,
                "cathode_width_mm": 100.0,
            }
        }
        geometry = _map_sheet_geometry(stack_config)

        # All offsets should use default of 2.0
        assert geometry.anode_offset_top_mm == 2.0
        assert geometry.anode_offset_bottom_mm == 2.0
        assert geometry.separator_offset_top_mm == 2.0
        assert geometry.separator_offset_right_mm == 2.0

    def test_map_sheet_geometry_missing_cathode_height(self):
        """Raise error when cathode_height_mm missing."""
        stack_config = {
            "sheet_geometry": {
                "cathode_width_mm": 100.0,
            }
        }
        with pytest.raises(MissingFieldError):
            _map_sheet_geometry(stack_config)

    def test_map_sheet_geometry_empty_config(self):
        """Handle empty stack_config."""
        stack_config = {}
        with pytest.raises(MissingFieldError):
            _map_sheet_geometry(stack_config)

    def test_map_sheet_geometry_template_format(self):
        """Map sheet geometry from template format."""
        stack_config = {
            "sheet_geometry": {
                "cathode_height_mm": {"_default": 200.0},
                "cathode_width_mm": {"_default": 100.0},
                "anode_offset_top_mm": {"_default": 3.0},
            }
        }
        geometry = _map_sheet_geometry(stack_config)

        assert geometry.cathode_height_mm == 200.0
        assert geometry.anode_offset_top_mm == 3.0
        assert geometry.anode_offset_bottom_mm == 2.0  # Default
